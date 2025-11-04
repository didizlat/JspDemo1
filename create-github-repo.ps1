# Script to create GitHub repository for JspDemo1
# This script will guide you through creating a GitHub repository

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Repository Setup for JspDemo1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "OPTION 1: Install GitHub CLI (Recommended)" -ForegroundColor Yellow
Write-Host "-------------------------------------------"
Write-Host "1. Download GitHub CLI from: https://cli.github.com/"
Write-Host "2. Install it and restart PowerShell"
Write-Host "3. Run these commands:"
Write-Host "   gh auth login" -ForegroundColor Green
Write-Host "   gh repo create JspDemo1 --public --source=. --push" -ForegroundColor Green
Write-Host ""

Write-Host "OPTION 2: Manual Setup (If CLI doesn't work)" -ForegroundColor Yellow
Write-Host "-------------------------------------------"
Write-Host "1. Go to: https://github.com/new" -ForegroundColor Cyan
Write-Host "2. Repository name: JspDemo1" -ForegroundColor White
Write-Host "3. Description: JSP Demo Application with AI-driven Testing Framework" -ForegroundColor White
Write-Host "4. Choose: Public" -ForegroundColor White
Write-Host "5. DO NOT initialize with README (we already have one)" -ForegroundColor Red
Write-Host "6. Click 'Create repository'" -ForegroundColor White
Write-Host ""
Write-Host "7. After creating, GitHub will show commands. Use these instead:" -ForegroundColor Yellow
Write-Host ""

# Get the GitHub username from memory (piepengu account preferred)
$githubUser = "piepengu"

Write-Host "   git remote add origin https://github.com/$githubUser/JspDemo1.git" -ForegroundColor Green
Write-Host "   git branch -M main" -ForegroundColor Green
Write-Host "   git push -u origin main" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Current Git Status:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
git log --oneline -5
Write-Host ""

Write-Host "Total commits ready to push: " -NoNewline
$commitCount = (git rev-list --count HEAD)
Write-Host $commitCount -ForegroundColor Green

Write-Host ""
Write-Host "Would you like to:" -ForegroundColor Yellow
Write-Host "  [1] Try to install GitHub CLI now" -ForegroundColor White
Write-Host "  [2] Get manual setup instructions" -ForegroundColor White
Write-Host "  [3] Exit and set up later" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host "`nAttempting to install GitHub CLI..." -ForegroundColor Cyan
        try {
            winget install --id GitHub.cli --source winget
            Write-Host "`nInstallation complete! Please:" -ForegroundColor Green
            Write-Host "1. Close and reopen PowerShell" -ForegroundColor Yellow
            Write-Host "2. Run: gh auth login" -ForegroundColor Yellow
            Write-Host "3. Run: gh repo create JspDemo1 --public --source=. --push" -ForegroundColor Yellow
        } catch {
            Write-Host "`nInstallation failed. Please use manual setup (Option 2)" -ForegroundColor Red
        }
    }
    "2" {
        Write-Host "`nManual Setup Steps:" -ForegroundColor Green
        Write-Host "===================" -ForegroundColor Green
        Write-Host "1. Open browser: https://github.com/new" -ForegroundColor White
        Write-Host "2. Create repository named 'JspDemo1'" -ForegroundColor White
        Write-Host "3. After creation, run these commands here:" -ForegroundColor White
        Write-Host ""
        Write-Host "   git remote add origin https://github.com/$githubUser/JspDemo1.git" -ForegroundColor Cyan
        Write-Host "   git branch -M main" -ForegroundColor Cyan
        Write-Host "   git push -u origin main" -ForegroundColor Cyan
    }
    "3" {
        Write-Host "`nNo problem! Run this script again when you're ready." -ForegroundColor Yellow
    }
    default {
        Write-Host "`nInvalid choice. Run the script again." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "For more help, visit: https://docs.github.com/en/get-started/quickstart/create-a-repo" -ForegroundColor Cyan
Write-Host ""

