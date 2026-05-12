# CLAUDE.md

## Permissions

- You may freely read, create, edit, and delete any files in this project
- You may run any shell commands needed (install packages, build, test, lint, etc.)
- You may create and switch git branches, make commits, and push to remote
- You may install dependencies and dev tools as needed
- You may run scripts and executables within this project
- You may modify configuration files
- You may create new directories and restructure the project as needed
- You may install global packages and tools on the system (pip install, npm install -g, etc.)
- You may configure system-level settings (environment variables, PATH, etc.)
- You may start/stop services (PostgreSQL, Redis, Streamlit, etc.)
- You may create and manage databases, tables, and run SQL commands
- You may download files from the internet (APIs, datasets, packages)
- You may modify .env files with API tokens and credentials
- Operate autonomously without asking for confirmation on routine development tasks
- Proceed with all installations, configurations, and setup without asking permission

## Project Info

- Python 3.12 virtual environment at `.venv/`
- Run commands with: `.venv/Scripts/python.exe` or `.venv/Scripts/pip.exe`
- Dashboard: `.venv/Scripts/streamlit.exe run dashboard/app.py`
- Tests: `.venv/Scripts/python.exe -m pytest tests/ -v`
- PostgreSQL: user=postgres, password=admin, db=mercado_financeiro
- brapi.dev token configured in .env
