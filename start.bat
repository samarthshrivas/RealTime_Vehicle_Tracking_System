@echo off
setlocal enableextensions

REM Root of the project
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo [INFO] Activating Python virtual environment...
if exist "%ROOT%venv\Scripts\activate.bat" (
  call "%ROOT%venv\Scripts\activate.bat"
) else (
  echo [ERROR] Virtual environment not found at venv\Scripts\activate.bat
  echo         Create it with: python -m venv venv
  goto :END
)

echo [INFO] Starting backend (uvicorn) on http://localhost:8000 ...
start "YOLO API" cmd /c uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM Small wait to let backend boot
timeout /t 2 >nul

echo [INFO] Starting frontend static server on http://localhost:5555 ...
pushd "%ROOT%frontend"
start "Frontend Server" cmd /c python -m http.server 5555
popd

REM Open default browser to frontend
start "" http://localhost:5555/

echo [INFO] Servers launched. This window can be closed.
goto :END

:END
endlocal
