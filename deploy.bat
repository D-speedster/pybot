@echo off
REM Telegram Bot Deployment Script for Windows
REM Usage: deploy.bat [start|stop|restart|logs|status]

setlocal enabledelayedexpansion

set PROJECT_NAME=telegram-userbot-downloader

REM Function to print colored output (Windows doesn't support colors easily, so we use simple text)
set "INFO_PREFIX=[INFO]"
set "SUCCESS_PREFIX=[SUCCESS]"
set "WARNING_PREFIX=[WARNING]"
set "ERROR_PREFIX=[ERROR]"

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_PREFIX% Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_PREFIX% Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check environment file
if not exist ".env" (
    echo %WARNING_PREFIX% .env file not found.
    if exist ".env.example" (
        echo %WARNING_PREFIX% Creating .env from .env.example...
        copy ".env.example" ".env" >nul
        echo %WARNING_PREFIX% Please edit .env file with your bot credentials before starting!
        echo %WARNING_PREFIX% Required: BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS
        if "%1"=="start" (
            echo %ERROR_PREFIX% Please configure .env file first!
            pause
            exit /b 1
        )
    ) else (
        echo %ERROR_PREFIX% .env.example file not found!
        pause
        exit /b 1
    )
)

REM Parse command line arguments
if "%1"=="" goto help
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="update" goto update
if "%1"=="cleanup" goto cleanup
if "%1"=="backup" goto backup
if "%1"=="help" goto help

echo %ERROR_PREFIX% Unknown command: %1
goto help

:start
echo %INFO_PREFIX% Starting Telegram Bot...

REM Create necessary directories
if not exist "sessions" mkdir sessions
if not exist "logs" mkdir logs
if not exist "temp_downloads" mkdir temp_downloads

REM Build and start containers
docker-compose up -d --build
if errorlevel 1 (
    echo %ERROR_PREFIX% Failed to start the bot!
    pause
    exit /b 1
)

echo %SUCCESS_PREFIX% Bot started successfully!
echo %INFO_PREFIX% Use 'docker-compose logs -f' to view logs
echo %INFO_PREFIX% Use 'deploy.bat logs' for formatted logs
goto end

:stop
echo %INFO_PREFIX% Stopping Telegram Bot...
docker-compose down
echo %SUCCESS_PREFIX% Bot stopped successfully!
goto end

:restart
echo %INFO_PREFIX% Restarting Telegram Bot...
docker-compose down
docker-compose up -d --build
if errorlevel 1 (
    echo %ERROR_PREFIX% Failed to restart the bot!
    pause
    exit /b 1
)
echo %SUCCESS_PREFIX% Bot restarted successfully!
goto end

:logs
echo %INFO_PREFIX% Showing bot logs (Press Ctrl+C to exit)...
docker-compose logs -f --tail=100
goto end

:status
echo %INFO_PREFIX% Bot Status:
docker-compose ps
echo.
echo %INFO_PREFIX% Container Health:
docker inspect --format="{{.State.Health.Status}}" %PROJECT_NAME% 2>nul || echo Health check not available
echo.
echo %INFO_PREFIX% Resource Usage:
docker stats --no-stream %PROJECT_NAME% 2>nul || echo Container not running
goto end

:update
echo %INFO_PREFIX% Updating Telegram Bot...

REM Pull latest changes (if using git)
if exist ".git" (
    git pull
)

REM Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
if errorlevel 1 (
    echo %ERROR_PREFIX% Failed to update the bot!
    pause
    exit /b 1
)
echo %SUCCESS_PREFIX% Bot updated successfully!
goto end

:cleanup
echo %INFO_PREFIX% Cleaning up Docker resources...

REM Stop and remove containers
docker-compose down --remove-orphans

REM Remove unused images
docker image prune -f

echo %SUCCESS_PREFIX% Cleanup completed!
goto end

:backup
echo %INFO_PREFIX% Creating backup...

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "BACKUP_DIR=backup_%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

mkdir "%BACKUP_DIR%" 2>nul

REM Backup important files
if exist "sessions" xcopy /E /I "sessions" "%BACKUP_DIR%\sessions" >nul 2>&1
if exist "logs" xcopy /E /I "logs" "%BACKUP_DIR%\logs" >nul 2>&1
if exist "userbot_manager.db" copy "userbot_manager.db" "%BACKUP_DIR%\" >nul 2>&1
if exist ".env" copy ".env" "%BACKUP_DIR%\" >nul 2>&1

echo %SUCCESS_PREFIX% Backup created: %BACKUP_DIR%
goto end

:help
echo Telegram Bot Deployment Script for Windows
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   start     Start the bot
echo   stop      Stop the bot
echo   restart   Restart the bot
echo   logs      Show bot logs
echo   status    Show bot status
echo   update    Update and restart the bot
echo   cleanup   Clean up Docker resources
echo   backup    Backup bot data
echo   help      Show this help message
echo.
echo Examples:
echo   %0 start    # Start the bot
echo   %0 logs     # View logs
echo   %0 status   # Check status
echo.
echo Note: Make sure Docker Desktop is running before using this script.
goto end

:end
if "%1"=="" pause
exit /b 0