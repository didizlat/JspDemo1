@echo off
echo Building application (first time only)...
echo.

REM Check if JAR exists
if not exist target\jspdemo1-1.0.0.jar (
    echo Building JAR file...
    call mvnw.cmd clean package -DskipTests
    echo.
)

echo Starting server...
echo.
echo Server will be available at: http://localhost:8080
echo Press Ctrl+C to stop
echo.

java -jar target\jspdemo1-1.0.0.jar

