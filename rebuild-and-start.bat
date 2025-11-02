@echo off
echo Rebuilding application...
echo.

call mvnw.cmd clean package -DskipTests

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo Build successful!
    echo ============================================================
    echo.
    echo Starting server...
    echo Server will be available at: http://localhost:8080
    echo Press Ctrl+C to stop
    echo.
    
    java -jar target\jspdemo1-1.0.0.jar
) else (
    echo.
    echo ============================================================
    echo Build failed! Please check errors above.
    echo ============================================================
    pause
)

