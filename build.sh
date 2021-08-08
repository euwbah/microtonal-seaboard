python3 -m pip install --user --upgrade pip
python3 -m pip install --user virtualenv
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
pyinstaller -F --hidden-import=websockets.legacy -n microtonal-seaboard main.py &&\
    cd dist/ &&\
    zip -r9 microtonal-seaboard.zip ../mappings microtonal-seaboard
deactivate