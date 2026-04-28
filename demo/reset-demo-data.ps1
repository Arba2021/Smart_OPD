# Clear all test data
Write-Host "WARNING: This will delete ALL test data!" -ForegroundColor Yellow
Write-Host "Are you sure? (Y/N)" -NoNewline
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "Clearing database..." -ForegroundColor Cyan
    
    docker-compose exec db psql -U smartopd_user -d smartopd_db -c "
        DELETE FROM doctor_queue;
        DELETE FROM registration_queue;
        DELETE FROM patient_master;
        DELETE FROM health_alerts;
    "
    
    Write-Host "✓ Database cleared successfully!" -ForegroundColor Green
    Write-Host "Run .\generate-demo-data.ps1 to create fresh test data" -ForegroundColor Cyan
} else {
    Write-Host "Operation cancelled" -ForegroundColor Yellow
}