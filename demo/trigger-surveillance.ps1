# Force surveillance check immediately
Write-Host "Triggering AI surveillance analysis..." -ForegroundColor Cyan

# Call the surveillance endpoint
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/admin/run-surveillance" -Method Post -Headers @{
        "x-api-key" = "super_secret_internal_key_change_in_production"
    } -ContentType "application/json"
    
    Write-Host "✓ Surveillance triggered successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Results:" -ForegroundColor Cyan
    if ($response.alerts) {
        foreach ($alert in $response.alerts) {
            Write-Host "  🔴 $($alert.suspected_disease) - $($alert.confidence)% confidence - $($alert.match_count) matches" -ForegroundColor Red
        }
    } else {
        Write-Host "  No active clusters detected" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Note: Surveillance job may already be running" -ForegroundColor Yellow
}