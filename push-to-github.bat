@echo off
REM Script to push JspDemo1 to GitHub
REM Run this AFTER creating the repository on GitHub

echo.
echo ========================================
echo   Pushing JspDemo1 to GitHub
echo ========================================
echo.

REM Get GitHub username (default to piepengu)
set /p GITHUB_USER="Enter your GitHub username (default: piepengu): "
if "%GITHUB_USER%"=="" set GITHUB_USER=piepengu

echo.
echo Using GitHub account: %GITHUB_USER%
echo Repository: JspDemo1
echo.

REM Check if remote already exists
git remote -v | find "origin" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Remote 'origin' already exists. Removing it...
    git remote remove origin
)

REM Add the remote
echo Adding GitHub remote...
git remote add origin https://github.com/%GITHUB_USER%/JspDemo1.git

REM Rename branch to main
echo Renaming branch to 'main'...
git branch -M main

REM Push to GitHub
echo.
echo Pushing all commits to GitHub...
echo This may take a moment...
echo.
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   SUCCESS! Repository pushed to GitHub
    echo ========================================
    echo.
    echo View your repository at:
    echo https://github.com/%GITHUB_USER%/JspDemo1
    echo.
) else (
    echo.
    echo ========================================
    echo   Push failed - Authentication needed
    echo ========================================
    echo.
    echo You may need to:
    echo 1. Configure Git credentials
    echo 2. Use Personal Access Token instead of password
    echo 3. Set up SSH keys
    echo.
    echo See GITHUB-SETUP.md for detailed instructions
    echo.
)

pause

