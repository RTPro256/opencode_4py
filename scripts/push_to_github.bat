@echo off
REM Simple script to push changes to GitHub
REM Usage: push_to_github.bat "commit message"

setlocal enabledelayedexpansion

REM Get commit message from argument or prompt
if "%~1"=="" (
    set /p COMMIT_MSG="Enter commit message: "
) else (
    set COMMIT_MSG=%~1
)

REM Check if git is initialized
if not exist ".git" (
    echo Initializing git repository...
    git init
    git remote add origin https://github.com/RTPro256/opencode_4py.git
)

REM Show status
echo.
echo === Current Status ===
git status --short
echo.

REM Add all changes
echo Adding changes...
git add .

REM Commit
echo Committing: !COMMIT_MSG!
git commit -m "!COMMIT_MSG!"

REM Push to GitHub
echo.
echo Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo === Done! ===
echo View your changes at: https://github.com/RTPro256/opencode_4py
pause
