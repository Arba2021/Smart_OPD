# Smart OPD - Competition Demo Data Generator
# Generates 50+ patients across 3 categories

$API_URL = "http://localhost:8000"
$DOCTOR_ID = "gen-001"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart OPD - Demo Data Generator" -ForegroundColor Cyan
Write-Host "  Generating 50+ test patients..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Category 1: DENGUE OUTBREAK (18 patients)
Write-Host "[1/3] Generating DENGUE cluster (18 patients)..." -ForegroundColor Yellow
$dengueSymptoms = @(
    "High fever with severe body pain",
    "Fever and severe joint pain",
    "High fever with headache and body ache",
    "Severe body pain with high fever",
    "Fever with rash and body pain",
    "High fever with muscle pain",
    "Fever with severe headache and body pain",
    "Body pain with high fever and weakness",
    "High fever with joint pain and rash",
    "Severe fever with body ache",
    "Fever with bone pain and headache",
    "High fever with severe muscle pain",
    "Fever with body pain and weakness",
    "High fever with joint and muscle pain",
    "Severe body pain with fever",
    "Fever with severe headache",
    "High fever with rash and joint pain",
    "Body pain with fever and weakness"
)

$dengueNames = @(
    "Rajesh Kumar", "Priya Sharma", "Arun Kumar", "Lakshmi Devi",
    "Suresh Patel", "Meera Reddy", "Karthik Iyer", "Anita Singh",
    "Ramesh Gupta", "Kavita Joshi", "Sanjay Rao", "Deepa Nair",
    "Venkat Reddy", "Pooja Mehta", "Arun Kumar", "Sunita Devi",
    "Mohan Das", "Rekha Singh"
)

for ($i = 0; $i -lt 18; $i++) {
    $phone = "98765432" + (100 + $i).ToString()
    $body = @{
        name = $dengueNames[$i]
        phone = $phone
        doctor_id = $DOCTOR_ID
        symptom = $dengueSymptoms[$i]
        language = @("en", "hi", "ta")[$i % 3]
    } | ConvertTo-Json
    
    try {
        $result = Invoke-RestMethod -Uri "$API_URL/book" -Method Post -ContentType "application/json" -Body $body
        Write-Host "  ✓ $($dengueNames[$i]) - Token: $($result.doctor_token)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Start-Sleep -Seconds 2

# Category 2: VIRAL FEVER CLUSTER (18 patients)
Write-Host ""
Write-Host "[2/3] Generating VIRAL FEVER cluster (18 patients)..." -ForegroundColor Yellow
$viralSymptoms = @(
    "Fever with sore throat",
    "Cough and body aches",
    "Fever and throat pain",
    "Sore throat with fever",
    "Fever with cough and cold",
    "Throat infection with fever",
    "Body ache with mild fever",
    "Fever with running nose",
    "Cough with fever and weakness",
    "Sore throat and body pain",
    "Fever with throat irritation",
    "Mild fever with cough",
    "Fever with cold and cough",
    "Throat pain with fever",
    "Body pain with sore throat",
    "Fever with headache and cough",
    "Cough with throat pain",
    "Fever with body weakness"
)

$viralNames = @(
    "Amit Shah", "Neha Kapoor", "Ravi Shankar", "Pooja Agarwal",
    "Vikram Singh", "Anjali Verma", "Rohit Malhotra", "Sneha Das",
    "Akash Jain", "Divya Pillai", "Nikhil Rao", "Preeti Kaur",
    "Abhishek Mishra", "Shruti Bansal", "Gaurav Saxena", "Isha Chopra",
    "Kunal Mehta", "Tanya Sinha"
)

for ($i = 0; $i -lt 18; $i++) {
    $phone = "98765433" + (100 + $i).ToString()
    $body = @{
        name = $viralNames[$i]
        phone = $phone
        doctor_id = $DOCTOR_ID
        symptom = $viralSymptoms[$i]
        language = @("en", "hi", "bn")[$i % 3]
    } | ConvertTo-Json
    
    try {
        $result = Invoke-RestMethod -Uri "$API_URL/book" -Method Post -ContentType "application/json" -Body $body
        Write-Host "  ✓ $($viralNames[$i]) - Token: $($result.doctor_token)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Start-Sleep -Seconds 2

# Category 3: NORMAL/ROUTINE CASES (15 patients)
Write-Host ""
Write-Host "[3/3] Generating NORMAL cases (15 patients)..." -ForegroundColor Yellow
$normalCases = @(
    @{ name = "Sunita Devi"; symptom = "Regular checkup"; phone = "9876543400" },
    @{ name = "Ramesh Kumar"; symptom = "Knee pain"; phone = "9876543401" },
    @{ name = "Priya Singh"; symptom = "Eye infection"; phone = "9876543402" },
    @{ name = "Arun Patel"; symptom = "Stomach pain"; phone = "9876543403" },
    @{ name = "Meera Reddy"; symptom = "Back pain"; phone = "9876543404" },
    @{ name = "Suresh Gupta"; symptom = "Dental checkup"; phone = "9876543405" },
    @{ name = "Kavita Sharma"; symptom = "Skin rash"; phone = "9876543406" },
    @{ name = "Rajesh Verma"; symptom = "Ear pain"; phone = "9876543407" },
    @{ name = "Anita Joshi"; symptom = "Headache"; phone = "9876543408" },
    @{ name = "Sanjay Rao"; symptom = "Routine blood test"; phone = "9876543409" },
    @{ name = "Deepa Nair"; symptom = "Vaccination"; phone = "9876543410" },
    @{ name = "Venkat Iyer"; symptom = "Health checkup"; phone = "9876543411" },
    @{ name = "Pooja Mehta"; symptom = "Allergy"; phone = "9876543412" },
    @{ name = "Mohan Das"; symptom = "Chest pain"; phone = "9876543413" },
    @{ name = "Rekha Singh"; symptom = "Thyroid checkup"; phone = "9876543414" }
)

foreach ($case in $normalCases) {
    $body = @{
        name = $case.name
        phone = $case.phone
        doctor_id = $DOCTOR_ID
        symptom = $case.symptom
        language = "en"
    } | ConvertTo-Json
    
    try {
        $result = Invoke-RestMethod -Uri "$API_URL/book" -Method Post -ContentType "application/json" -Body $body
        Write-Host "  ✓ $($case.name) - Token: $($result.doctor_token)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Demo Data Generation Complete!" -ForegroundColor Green
Write-Host "  Total Patients: 51" -ForegroundColor Green
Write-Host "  - Dengue Cluster: 18 patients" -ForegroundColor Yellow
Write-Host "  - Viral Fever: 18 patients" -ForegroundColor Yellow
Write-Host "  - Normal Cases: 15 patients" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Wait 2 minutes for surveillance job" -ForegroundColor White
Write-Host "2. OR run: .\trigger-surveillance.ps1" -ForegroundColor White
Write-Host "3. Check Radar page at: http://localhost:3000/admin/radar" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan