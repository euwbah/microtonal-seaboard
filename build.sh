#!/bin/bash
# use version 3.12 for now, seems like 3.13 is not supported by rtmidi yet.

# Check if uv is available
if command -v uv &> /dev/null; then
    UV_AVAILABLE=1
else
    UV_AVAILABLE=0
fi

# Delete existing venv if it exists
if [ -d .venv ]; then
    rm -rf .venv
fi

if [ -d build ]; then
    rm -rf build
fi

if [ -d dist ]; then
    rm -rf dist
fi

if [ $UV_AVAILABLE -eq 1 ]; then
    # Ensure Python 3.12 is available and create venv with uv
    uv python install 3.12
    uv venv --python 3.12 .venv
    PIP="uv pip"
    PYINSTALLER="uv run pyinstaller"
else
    python3.12 -m venv .venv
    PIP="python -m pip"
    PYINSTALLER="python -m pyinstaller"
fi

source .venv/bin/activate
$PIP install --upgrade pip setuptools
$PIP install .
$PYINSTALLER microtonal-seaboard.spec
if [ $? -ne 0 ]; then
    exit $?
fi
cd dist
zip -r9 microtonal-seaboard-macos.zip ../mappings ../mapping_generator microtonal-seaboard
cd ..
deactivate