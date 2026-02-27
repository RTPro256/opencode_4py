@echo off
REM OpenCode_4py Launch Script for ComfyUI_windows_portable
REM This script launches the OpenCode_4py TUI interface

echo Starting OpenCode_4py...
echo.

REM Set environment variables
set OPENCODE_CONFIG=%~dp0opencode.toml
set PYTHONPATH=%~dp0python_embeded\Lib\site-packages

REM Run pre-flight check first
cd /d "%~dp0"
echo Running pre-flight checks...
.\python_embeded\python.exe check_prerequisites.py
if errorlevel 1 (
    echo.
    echo Pre-flight checks failed. Please fix the issues above before continuing.
    pause
    exit /b 1
)

echo.
echo Pre-flight checks passed. Launching OpenCode_4py...
echo.

REM Launch OpenCode_4py TUI (run command is the default)
.\python_embeded\python.exe -m opencode run

echo.
echo OpenCode_4py has exited.
pause
