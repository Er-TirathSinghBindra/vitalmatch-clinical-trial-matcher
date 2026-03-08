# Invoke Data Ingestion Lambda

Write-Host "Invoking Data Ingestion Lambda..." -ForegroundColor Green
Write-Host "This may take up to 5 minutes (Lambda timeout is 300 seconds)..." -ForegroundColor Yellow

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

aws lambda invoke `
    --function-name dev-vitalmatch-data-ingestion `
    --log-type Tail `
    ingestion-response.json

Write-Host "`nResponse:" -ForegroundColor Cyan
Get-Content ingestion-response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

Write-Host "`nChecking CloudWatch Logs for details..." -ForegroundColor Yellow
aws logs tail /aws/lambda/dev-vitalmatch-data-ingestion --since 5m --format short
