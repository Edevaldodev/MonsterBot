@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Criando ambiente virtual...
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env (
  copy .env.example .env
  echo.
  echo ATENCAO: abra o arquivo .env e coloque sua chave Groq.
  notepad .env
)
python main.py
pause
