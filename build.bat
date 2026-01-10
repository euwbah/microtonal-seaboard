REM use version 3.12 for now, seems like 3.13 is not supported by rtmidi yet.
set "UV_AVAILABLE="
where uv >nul 2>&1 && set "UV_AVAILABLE=1"

REM Delete existing venv if it exists
if exist .venv (
    rmdir /s /q .venv
)

if exist build (
    rmdir /s /q build
)

if exist dist (
    rmdir /s /q dist
)

if defined UV_AVAILABLE (
    REM Ensure Python 3.12 is available and create venv with uv
    uv python install 3.12
    uv venv --python 3.12 .venv
    set "PIP=uv pip"
    set "PYINSTALLER=uv run pyinstaller"
) else (
    py -3.12 -m venv .venv
    set "PIP=python -m pip"
    set "PYINSTALLER=python -m pyinstaller"
)

call .\.venv\Scripts\activate.bat
%PIP% install --upgrade pip setuptools
%PIP% install .
%PYINSTALLER% microtonal-seaboard.spec
if %errorlevel% neq 0 exit /b %errorlevel%
cd dist
tar -a -c -f microtonal-seaboard-windows.zip ../mappings ../mapping_generator microtonal-seaboard.exe
cd ..
deactivate