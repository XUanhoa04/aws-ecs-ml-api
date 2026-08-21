[CmdletBinding()]
param(
    [string]$Region = "us-east-1",
    [string]$ProjectName = "ecs-ml-lab",
    [string]$Environment = "dev",
    [string]$ImageTag = "destroy-only",
    [string]$GitHubRepository = "",
    [switch]$KeepBootstrap
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$InfraDir = Join-Path $RepoRoot "infra"
$BootstrapDir = Join-Path $InfraDir "bootstrap"

foreach ($Command in @("aws", "terraform")) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        throw "Required command '$Command' was not found on PATH."
    }
}

$StateBucket = terraform "-chdir=$BootstrapDir" output -raw state_bucket_name
if ($LASTEXITCODE -ne 0 -or -not $StateBucket) {
    throw "Bootstrap output is missing; refusing to guess the state location."
}

terraform "-chdir=$InfraDir" init -reconfigure `
    "-backend-config=bucket=$StateBucket" `
    "-backend-config=key=$ProjectName/$Environment.tfstate" `
    "-backend-config=region=$Region" `
    "-backend-config=use_lockfile=true"
if ($LASTEXITCODE -ne 0) { throw "terraform init failed." }

terraform "-chdir=$InfraDir" destroy -auto-approve -input=false `
    "-var=aws_region=$Region" `
    "-var=project_name=$ProjectName" `
    "-var=environment=$Environment" `
    "-var=image_tag=$ImageTag"
if ($LASTEXITCODE -ne 0) { throw "Application infrastructure destroy failed." }

# Terraform deregisters ECS task definitions; the ECS API keeps those revisions
# as INACTIVE until an explicit purge request is submitted.
$TaskFamily = "$ProjectName-$Environment"
$InactiveTaskDefinitions = aws ecs list-task-definitions --region $Region `
    --family-prefix $TaskFamily --status INACTIVE --query "taskDefinitionArns" |
    ConvertFrom-Json
foreach ($TaskDefinitionArn in $InactiveTaskDefinitions) {
    aws ecs delete-task-definitions --region $Region `
        --task-definitions $TaskDefinitionArn | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not purge inactive task definition $TaskDefinitionArn."
    }
}

if (-not $KeepBootstrap) {
    if (-not (Get-Command "gh" -ErrorAction SilentlyContinue)) {
        throw "Required command 'gh' was not found on PATH."
    }
    if (-not $GitHubRepository) {
        $GitHubRepository = gh repo view --json nameWithOwner --jq .nameWithOwner
    }

    $BootstrapState = terraform "-chdir=$BootstrapDir" state list
    $ManagesOidcProvider = $BootstrapState -contains "aws_iam_openid_connect_provider.github[0]"
    $BootstrapArguments = @(
        "-chdir=$BootstrapDir", "destroy", "-auto-approve", "-input=false",
        "-var=aws_region=$Region",
        "-var=project_name=$ProjectName",
        "-var=github_repository=$GitHubRepository",
        "-var=create_github_oidc_provider=$(if ($ManagesOidcProvider) { 'true' } else { 'false' })"
    )
    if (-not $ManagesOidcProvider) {
        $Providers = aws iam list-open-id-connect-providers | ConvertFrom-Json
        $ExistingProviderArn = $Providers.OpenIDConnectProviderList.Arn |
            Where-Object { $_ -like "*/token.actions.githubusercontent.com" } |
            Select-Object -First 1
        if (-not $ExistingProviderArn) {
            throw "The existing GitHub OIDC provider could not be found."
        }
        $BootstrapArguments += "-var=existing_github_oidc_provider_arn=$ExistingProviderArn"
    }

    terraform @BootstrapArguments
    if ($LASTEXITCODE -ne 0) { throw "Bootstrap destroy failed." }

    foreach ($VariableName in @(
        "AWS_REGION", "AWS_ROLE_ARN", "TF_STATE_BUCKET", "PROJECT_NAME", "ENVIRONMENT"
    )) {
        gh variable delete $VariableName 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove GitHub variable $VariableName."
        }
    }
}

Write-Host "Lab resources were destroyed."
