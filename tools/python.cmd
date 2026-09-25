@echo off
REM Homesteader Python shim.
REM
REM Windows resolves "python" to the Microsoft Store stub, which is not a
REM real interpreter - it opens the Store and fails. Typing "python" in this
REM repo just work, so this shim forwards to the interpreter the
REM project already uses (see .mcp.json -> C:/Python313/python.exe).
REM
REM Put this file's folder on PATH, or add tools\ to PATH, to use it.

setlocal
set "REAL_PYTHON=C:\Python313\python.exe"

if not exist "%REAL_PYTHON%" (
    echo python.cmd: cannot find %REAL_PYTHON% >&2
    echo python.cmd: edit tools\python.cmd and point REAL_PYTHON at your interpreter. >&2
    exit /b 9009
)

"%REAL_PYTHON%" %*
exit /b %ERRORLEVEL%
