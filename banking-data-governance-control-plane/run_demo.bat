@echo off
setlocal
set PYTHONPATH=src
python -m governance_control.generator --output data/input
if errorlevel 1 exit /b %errorlevel%
python -m governance_control.engine --input data/input --output data/output --policy config/policies.json
endlocal

