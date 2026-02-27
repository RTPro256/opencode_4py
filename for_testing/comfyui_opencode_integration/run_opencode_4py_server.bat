@echo off
REM OpenCode_4py Server Mode
REM Runs OpenCode_4py as a background server

echo Starting OpenCode_4py Server on port 4096...
echo.

cd /d "%~dp0"
.\python_embeded\python.exe -m opencode serve --port 4096

pause
