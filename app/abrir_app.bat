@echo off
chcp 65001 >nul
cd /d "%~dp0"
title App de previsao de ocupacao - @fabiods.tech

echo.
echo  ================================================
echo   Previsao de ocupacao - @fabiods.tech
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo  [ERRO] Python nao encontrado.
  echo  Instale em python.org e marque "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

rem verifica TODAS as dependencias, nao so o streamlit
python -c "import streamlit, plotly, pandas" >nul 2>&1
if errorlevel 1 (
  echo  Instalando dependencias, isso leva um minuto na primeira vez...
  echo.
  python -m pip install --upgrade -r requirements.txt
  echo.
  python -c "import streamlit, plotly, pandas" >nul 2>&1
  if errorlevel 1 (
    echo  [ERRO] A instalacao nao completou. Rode manualmente:
    echo      python -m pip install streamlit plotly pandas
    echo.
    pause
    exit /b 1
  )
)

echo  Abrindo no navegador. Para encerrar, feche esta janela.
echo.
python -m streamlit run app.py

pause
