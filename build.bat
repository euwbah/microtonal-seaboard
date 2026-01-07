REM use version 3.12 for now, seems like 3.13 is not supported by rtmidi yet.
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    set PYTHON=python3.12
) else (
    set PYTHON=py -3.12
)   

%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install --user virtualenv
%PYTHON% -m venv .venv
call .\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install --upgrade setuptools
pip install -r requirements.txt
pyinstaller microtonal-seaboard.spec &&^
    cd dist/ &&^
    tar -a -c -f microtonal-seaboard-windows.zip ../mappings microtonal-seaboard.exe
deactivate