[CmdletBinding()]
param(
    [string]$Region = "us-east-1",
    [string]$ProjectName = "ecs-ml-lab",
    [string]$Environment = "dev",
    [string]$ImageTag = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$InfraDir = Join-Path $RepoRoot "infra"
$BootstrapDir = Join-Path $InfraDir "bootstrap"

foreach ($Command in @("aws", "docker", "terraform", "git")) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        throw "Required command '$Command' was not found on PATH."
    }
}

if (-not $ImageTag) {
    $ImageTag = git -C $RepoRoot rev-parse --short=12 HEAD
}
if ($ImageTag.Length -lt 7) { throw "ImageTag must contain at least 7 characters." }

$StateBucket = terraform "-chdir=$BootstrapDir" output -raw state_bucket_name
if ($LASTEXITCODE -ne 0 -or -not $StateBucket) {
    throw "Bootstrap output is missing. Run scripts/bootstrap.ps1 first."
}

terraform "-chdir=$InfraDir" init -reconfigure `
    "-backend-config=bucket=$StateBucket" `
    "-backend-config=key=$ProjectName/$Environment.tfstate" `
    "-backend-config=region=$Region" `
    "-backend-config=use_lockfile=true"
if ($LASTEXITCODE -ne 0) { throw "terraform init failed." }

$TerraformVariables = @(
    "-var=aws_region=$Region",
    "-var=project_name=$ProjectName",
    "-var=environment=$Environment",
    "-var=image_tag=$ImageTag"
)

terraform "-chdir=$InfraDir" apply -auto-approve -input=false `
    "-target=aws_ecr_repository.api" @TerraformVariables
if ($LASTEXITCODE -ne 0) { throw "Could not create the ECR repository." }

$RepositoryUrl = terraform "-chdir=$InfraDir" output -raw ecr_repository_url
$RepositoryName = "$ProjectName-$Environment"
$Registry = $RepositoryUrl.Split("/")[0]

aws ecr describe-images --region $Region --repository-name $RepositoryName `
    --image-ids "imageTag=$ImageTag" | Out-Null
$ImageExists = $LASTEXITCODE -eq 0

if (-not $ImageExists) {
    aws ecr get-login-password --region $Region |
        docker login --username AWS --password-stdin $Registry
    if ($LASTEXITCODE -ne 0) { throw "Docker login to ECR failed." }

    docker build --build-arg "APP_VERSION=$ImageTag" `
        --tag "${RepositoryUrl}:${ImageTag}" $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed." }

    docker push "${RepositoryUrl}:${ImageTag}"
    if ($LASTEXITCODE -ne 0) { throw "Docker push failed." }
} else {
    Write-Host "Image ${RepositoryUrl}:${ImageTag} already exists; skipping build."
}

terraform "-chdir=$InfraDir" apply -auto-approve -input=false @TerraformVariables
if ($LASTEXITCODE -ne 0) { throw "Application infrastructure deployment failed." }

$ApiUrl = terraform "-chdir=$InfraDir" output -raw api_url
$Ready = $false
for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    try {
        $Health = Invoke-RestMethod -Uri "$ApiUrl/health/ready" -TimeoutSec 5
        if ($Health.status -eq "ready") {
            $Ready = $true
            break
        }
    } catch {
        Write-Host "Smoke test attempt $Attempt/30 is waiting for the ALB..."
    }
    Start-Sleep -Seconds 10
}
if (-not $Ready) { throw "The API did not become healthy: $ApiUrl" }

$Prediction = Invoke-RestMethod -Method Post -Uri "$ApiUrl/predict" `
    -ContentType "application/json" `
    -Body '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

Write-Host "Deployment verified: $ApiUrl"
Write-Host "Prediction: $($Prediction.class_name), confidence=$($Prediction.confidence)"
