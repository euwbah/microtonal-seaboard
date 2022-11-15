python3 -m pip install --user --upgrade pip
python3 -m pip install --user virtualenv
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
pyinstaller -F ./microtonal-seaboard.spec &&\
    cd dist/ &&\
    zip -r9 microtonal-seaboard.zip ../mappings microtonal-seaboard
deactivate