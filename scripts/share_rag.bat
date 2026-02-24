@echo off
REM Simple script to share your troubleshooting RAG with the community
REM This creates a pull request to add your error documents to the community RAG

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Share Your Troubleshooting RAG
echo ========================================
echo.

REM Check if RAG exists
if not exist "RAG\agent_troubleshooting" (
    echo Error: No troubleshooting RAG found.
    echo Create one first with: opencode rag create troubleshooting --source ./docs
    pause
    exit /b 1
)

REM Check for git
git --version >nul 2>&1
if errorlevel 1 (
    echo Error: Git is not installed.
    echo Download from: https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Check if user has GitHub token
if "%GITHUB_TOKEN%"=="" (
    echo Note: GITHUB_TOKEN not set.
    echo.
    echo For automatic PR creation, set your GitHub token:
    echo   set GITHUB_TOKEN=ghp_your_token_here
    echo.
    echo You can create a token at: https://github.com/settings/tokens
    echo Required scopes: 'repo' or 'public_repo'
    echo.
)

echo This script will:
echo   1. Fork RTPro256/opencode_4py (if not already forked)
echo   2. Copy your RAG to the community folder
echo   3. Create a pull request
echo.

set /p CONFIRM="Continue? (y/n): "
if /i not "!CONFIRM!"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo === Step 1: Preparing files ===

REM Create community RAG folder structure
if not exist "community_rag_temp" mkdir community_rag_temp
if not exist "community_rag_temp\RAG" mkdir community_rag_temp\RAG
if not exist "community_rag_temp\RAG\agent_troubleshooting" mkdir community_rag_temp\RAG\agent_troubleshooting

REM Copy RAG files
echo Copying RAG files...
xcopy /E /I /Y "RAG\agent_troubleshooting\*" "community_rag_temp\RAG\agent_troubleshooting\"

echo.
echo === Step 2: Manual GitHub Process ===
echo.
echo Since the repo is at: https://github.com/RTPro256/opencode_4py
echo.
echo To share your RAG, follow these steps:
echo.
echo   1. Go to: https://github.com/RTPro256/opencode_4py
echo   2. Click "Fork" in the top right
echo   3. Clone your fork locally:
echo      git clone https://github.com/YOUR_USERNAME/opencode_4py.git
echo   4. Copy your RAG folder:
echo      xcopy /E /I /Y "RAG\agent_troubleshooting" "opencode_4py\RAG\agent_troubleshooting"
echo   5. Commit and push:
echo      cd opencode_4py
echo      git add .
echo      git commit -m "Add troubleshooting RAG updates"
echo      git push
echo   6. Create Pull Request:
echo      Go to your fork on GitHub and click "Create Pull Request"
echo.
echo Alternatively, just email your RAG folder to the maintainer!
echo.

REM Cleanup
rmdir /S /Q community_rag_temp 2>nul

echo ========================================
echo   Thank you for sharing!
echo ========================================
pause
