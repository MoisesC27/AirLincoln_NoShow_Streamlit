@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Air Lincoln - Inteligencia de No-show ===
if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual, solo la primera vez...
  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ y marca "Add python.exe to PATH".
    pause
    exit /b 1
  )
)
echo Instalando dependencias, la primera vez tarda unos minutos...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo.
  echo Fallo la instalacion. Copia el mensaje de arriba y envialo para revisarlo.
  pause
  exit /b 1
)
echo Abriendo el dashboard en el navegador. Para cerrarlo, cierra esta ventana.
".venv\Scripts\python.exe" -m streamlit run app.py
pause
