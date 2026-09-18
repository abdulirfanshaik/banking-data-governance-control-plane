@echo off
setlocal
set PYTHONPATH=src
python -m unittest discover -s tests -v
endlocal

