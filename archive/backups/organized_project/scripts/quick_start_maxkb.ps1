# Flash Loan Project - MaxKB Quick Start Script
# Windows PowerShell script to start MaxKB knowledge base

Write-Host "🧠 MaxKB Knowledge Base - Quick Start" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Check if Docker is running
try {
    $dockerVersion = docker --version 2>$null
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Start MaxKB with the provided command
Write-Host "🚀 Starting MaxKB container..." -ForegroundColor Green

try {
    # Run the MaxKB container
    docker run -d --name=maxkb --restart=always -p 8080:8080 -v ~/.maxkb:/var/lib/postgresql/data -v ~/.python-packages:/opt/maxkb/app/sandbox/python-packages 1panel/maxkb
    
    Write-Host "✅ MaxKB container started successfully!" -ForegroundColor Green
    
    Write-Host "⏳ Waiting for MaxKB to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Write-Host ""
    Write-Host "🎉 MaxKB is ready!" -ForegroundColor Green
    Write-Host "==================" -ForegroundColor Green
    Write-Host "🌐 URL: http://localhost:8080" -ForegroundColor Cyan
    Write-Host "👤 Username: admin" -ForegroundColor Cyan
    Write-Host "🔑 Password: MaxKB@123.." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 Note: It may take a few more minutes to fully initialize" -ForegroundColor Yellow
    
    # Optional: Open browser
    $openBrowser = Read-Host "Open MaxKB in browser now? (Y/n)"
    if ($openBrowser.ToLower() -ne "n") {
        Start-Process "http://localhost:8080"
    }
}
catch {
    Write-Host "❌ Failed to start MaxKB container" -ForegroundColor Red
    Write-Host "🔧 Try running: docker pull 1panel/maxkb" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Green
Write-Host "   Stop MaxKB:    docker stop maxkb" -ForegroundColor White
Write-Host "   Start MaxKB:   docker start maxkb" -ForegroundColor White
Write-Host "   Remove MaxKB:  docker rm -f maxkb" -ForegroundColor White
Write-Host "   View logs:     docker logs maxkb" -ForegroundColor White
