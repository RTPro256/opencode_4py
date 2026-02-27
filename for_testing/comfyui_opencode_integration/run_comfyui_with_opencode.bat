@echo off
REM Launch ComfyUI with OpenCode_4py integration
REM OpenCode TUI can be started from the button in ComfyUI interface

echo Starting ComfyUI with OpenCode_4py integration...
echo.
echo NOTE: OpenCode TUI can be started by clicking the "OpenCode" button
echo in the ComfyUI interface (next to the Manager button).
echo.

REM Set environment variables
set OPENCODE_CONFIG=%~dp0opencode.toml
set PYTHONPATH=%~dp0python_embeded\Lib\site-packages

REM Enable debug logging for troubleshooting
REM Logs will be saved to the target project's docs/opencode/logs/ folder automatically
set OPENCODE_LOG_LEVEL=DEBUG

REM Start ComfyUI (with warnings suppressed for requests dependency)
REM OpenCode TUI can be launched from the button in the ComfyUI interface
.\python_embeded\python.exe -W ignore -s ComfyUI\main.py --windows-standalone-build

pause
