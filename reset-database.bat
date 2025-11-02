@echo off
echo ============================================================
echo Database Reset Script
echo ============================================================
echo.
echo This will delete all data and reset the database to clean state.
echo.
pause

echo.
echo [1/2] Stopping Spring Boot server...
taskkill /F /IM java.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/2] Deleting database files...
if exist data\jspdemo.mv.db (
    del /F /Q data\jspdemo.mv.db
    echo   - Deleted: data\jspdemo.mv.db
)
if exist data\jspdemo.trace.db (
    del /F /Q data\jspdemo.trace.db
    echo   - Deleted: data\jspdemo.trace.db
)
if exist data\*.lock.db (
    del /F /Q data\*.lock.db
    echo   - Deleted: lock files
)

echo.
echo ============================================================
echo Database reset complete!
echo ============================================================
echo.
echo The database will be recreated on next server start.
echo Tables will be empty with fresh schema.
echo.
echo To start the server:
echo   mvnw.cmd spring-boot:run
echo.
pause

