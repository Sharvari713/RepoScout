Write-Host "Setting up RepoScout..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed. Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Check if pip is installed
try {
    $pipVersion = pip --version
    Write-Host "pip is installed: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "pip is not installed. Please install pip from https://pip.pypa.io/en/stable/installation/" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "Node.js is installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js is not installed. Please install Node.js from https://nodejs.org/en/download/" -ForegroundColor Red
    exit 1
}

# Check if npm is installed
try {
    $npmVersion = npm --version
    Write-Host "npm is installed: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "npm is not installed. Please install npm from https://docs.npmjs.com/downloading-and-installing-node-js-and-npm" -ForegroundColor Red
    exit 1
}

# Setup backend
Write-Host "`nSetting up backend..." -ForegroundColor Green
cd backend
pip install -r requirements.txt

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    "GITHUB_TOKEN=`"ENTER YOUR GITHUB Personal Access Token`"" | Out-File -FilePath .env
    Write-Host "Please update the GITHUB_TOKEN in backend/.env with your GitHub Personal Access Token" -ForegroundColor Yellow
}

# Setup frontend
Write-Host "`nSetting up frontend..." -ForegroundColor Green
cd ../frontend
npm install

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Starting the application..." -ForegroundColor Cyan

# Start backend server in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\..\backend'; python app.py"

# Start frontend server in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm start"

Write-Host "`nBoth servers are starting in new windows." -ForegroundColor Green
Write-Host "Please make sure to update your GitHub token in backend/.env if you haven't already." -ForegroundColor Yellow 