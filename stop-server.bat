@echo off
echo Stopping Spring Boot server...
echo.

taskkill /F /IM java.exe /T >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo ✓ Server stopped successfully
) else (
    echo No Java process found (server may already be stopped)
)

echo.
timeout /t 2 /nobreak >nul

