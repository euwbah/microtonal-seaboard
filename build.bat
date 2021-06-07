py -m pip install --upgrade pip
py -m pip install --user virtualenv
py -m venv venv
.\venv\Scripts\activate
pip install --upgrade setuptools
pip install -r requirements.txt
pyinstaller -F -n microtonal-seaboard main.py &&^
    cd dist/ &&^
    tar -a -c -f microtonal-seaboard-windows.zip ../mappings microtonal-seaboard.exe
deactivate