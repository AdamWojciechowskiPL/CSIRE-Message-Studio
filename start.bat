@echo off
echo Starting CSIRE Message Studio using the virtual environment's Python...

REM Bezpośrednio wywołaj plik python.exe z katalogu venv/Scripts
venv\Scripts\python.exe -m app.main

echo Application finished.
pause