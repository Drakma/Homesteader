@echo off
REM tools\unity_mcp.cmd - Windows shim for the Unity MCP wrapper.
REM Resolves the absolute Python interpreter (mirrors tools\python.cmd)
REM and forwards all args to tools\unity_mcp.py.
SETLOCAL
set "PYTHON_EXE=C:\Python313\python.exe"
set "WRAPPER=%~dp0unity_mcp.py"
"%PYTHON_EXE%" "%WRAPPER%" %*
ENDLOCAL
