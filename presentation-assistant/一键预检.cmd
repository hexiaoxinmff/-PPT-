@echo off
setlocal EnableExtensions
chcp 65001 >nul
set PYTHONUTF8=1

if "%~1"=="" (
  echo.
  echo Drag a .pptx file onto this script to run the read-only preflight.
  echo A *_preflight-report.json file will be written next to the PPTX.
  echo.
  pause
  exit /b 2
)

if /I not "%~x1"==".pptx" (
  echo.
  echo Please provide a .pptx file: %~nx1
  echo.
  pause
  exit /b 2
)

set "SCRIPT=%~dp0scripts\preflight_pptx.py"
set "REPORT=%~dpn1_preflight-report.json"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%SCRIPT%" "%~f1" --report "%REPORT%"
) else (
  python "%SCRIPT%" "%~f1" --report "%REPORT%"
)

set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo Preflight complete. Report: %REPORT%
) else (
  echo Preflight failed or a local dependency is missing. Review the messages above.
)
echo.
pause
exit /b %RESULT%

