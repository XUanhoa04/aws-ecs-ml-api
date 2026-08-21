[CmdletBinding()]
param(
    [string]$Region = "us-east-1",
    [string]$ProjectName = "ecs-ml-lab",
    [string]$GitHubRepository = "",
    [switch]$UseExistingOidcProvider
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BootstrapDir = Join-Path $RepoRoot "infra/bootstrap"

foreach ($Command in @("aws", "terraform", "gh")) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        throw "Required command '$Command' was not found on PATH."
    }
}

if (-not $GitHubRepository) {
    $GitHubRepository = gh repo view --json nameWithOwner --jq .nameWithOwner
    if ($LASTEXITCODE -ne 0 -or -not $GitHubRepository) {
        throw "Could not detect the GitHub repository. Pass -GitHubRepository owner/name."
    }
}

aws sts get-caller-identity --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "AWS credentials are not valid. Run 'aws configure' and retry."
}

$ExistingProviderArn = ""
if ($UseExistingOidcProvider) {
    $Providers = aws iam list-open-id-connect-providers | ConvertFrom-Json
    $ExistingProviderArn = $Providers.OpenIDConnectProviderList.Arn |
        Where-Object { $_ -like "*/token.actions.githubusercontent.com" } |
        Select-Object -First 1
    if (-not $ExistingProviderArn) {
        throw "GitHub's OIDC provider does not exist in this AWS account."
    }
}

terraform "-chdir=$BootstrapDir" init
if ($LASTEXITCODE -ne 0) { throw "terraform init failed for bootstrap." }

$ApplyArguments = @(
    "-chdir=$BootstrapDir", "apply", "-auto-approve", "-input=false",
    "-var=aws_region=$Region",
    "-var=project_name=$ProjectName",
    "-var=github_repository=$GitHubRepository",
    "-var=create_github_oidc_provider=$(if ($UseExistingOidcProvider) { 'false' } else { 'true' })"
)
if ($UseExistingOidcProvider) {
    $ApplyArguments += "-var=existing_github_oidc_provider_arn=$ExistingProviderArn"
}

terraform @ApplyArguments
if ($LASTEXITCODE -ne 0) { throw "terraform apply failed for bootstrap." }

$StateBucket = terraform "-chdir=$BootstrapDir" output -raw state_bucket_name
$RoleArn = terraform "-chdir=$BootstrapDir" output -raw github_role_arn

gh variable set AWS_REGION --body $Region
gh variable set AWS_ROLE_ARN --body $RoleArn
gh variable set TF_STATE_BUCKET --body $StateBucket
gh variable set PROJECT_NAME --body $ProjectName
gh variable set ENVIRONMENT --body "dev"
if ($LASTEXITCODE -ne 0) { throw "Could not configure GitHub repository variables." }

Write-Host "Bootstrap complete."
Write-Host "State bucket: $StateBucket"
Write-Host "GitHub role: $RoleArn"
Write-Host "Repository: $GitHubRepository"
