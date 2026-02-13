# SAML Passkey IdP - Quick Setup Script for Windows (PowerShell)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "SAML Passkey IdP - Quick Setup Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if MongoDB is running
try {
    $mongoService = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
    if ($mongoService) {
        if ($mongoService.Status -eq 'Running') {
            Write-Host "✓ MongoDB service is running" -ForegroundColor Green
        } else {
            Write-Host "⚠️  MongoDB service is installed but not running. Starting MongoDB..." -ForegroundColor Yellow
            Start-Service MongoDB
            Write-Host "✓ MongoDB service started" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️  MongoDB service not found. Please ensure MongoDB is installed." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check MongoDB status. Please ensure MongoDB is installed and running." -ForegroundColor Yellow
}

# Check if OpenSSL is installed
try {
    $opensslVersion = openssl version 2>&1
    Write-Host "✓ OpenSSL found: $opensslVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ OpenSSL is not installed. Please install OpenSSL to generate certificates." -ForegroundColor Red
    Write-Host "   Download from: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
python -m venv venv
Write-Host "✓ Virtual environment created" -ForegroundColor Green
Write-Host ""

# Activate virtual environment and install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Generate SAML certificates
Write-Host "🔐 Generating SAML certificates..." -ForegroundColor Cyan
& .\generate_certs.ps1
Write-Host "✓ Certificates generated" -ForegroundColor Green
Write-Host ""

# Create .env file if it doesn't exist
if (-Not (Test-Path .env)) {
    Write-Host "⚙️  Creating .env file..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    
    # Generate a random secret key
    $bytes = New-Object Byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $secretKey = [System.Convert]::ToBase64String($bytes)
    
    (Get-Content .env) -replace 'your-secret-key-change-in-production', $secretKey | Set-Content .env
    Write-Host "✓ .env file created with random secret key" -ForegroundColor Green
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review and adjust settings in .env file"
Write-Host "2. Run: .\venv\Scripts\Activate.ps1"
Write-Host "3. Run: python app.py"
Write-Host "4. Open: http://localhost:5000"
Write-Host ""
Write-Host "For more information, see README.md"
