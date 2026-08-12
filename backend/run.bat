@echo off
cd /d "%~dp0"

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\pip.exe install -q -r requirements-dev.txt
call .venv\Scripts\uvicorn.exe app.main:app --reload
