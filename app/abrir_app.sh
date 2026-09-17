#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1

echo
echo " ================================================"
echo "  Previsão de ocupação · @fabiods.tech"
echo " ================================================"
echo

PY=python3
command -v $PY >/dev/null 2>&1 || PY=python
if ! command -v $PY >/dev/null 2>&1; then
  echo " [ERRO] Python não encontrado. Instale em python.org"
  read -r -p " Pressione Enter para fechar. "
  exit 1
fi

# verifica TODAS as dependências, não só o streamlit
if ! $PY -c "import streamlit, plotly, pandas" >/dev/null 2>&1; then
  echo " Instalando dependências, isso leva um minuto na primeira vez..."
  echo
  $PY -m pip install --upgrade -r requirements.txt
  echo
  if ! $PY -c "import streamlit, plotly, pandas" >/dev/null 2>&1; then
    echo " [ERRO] A instalação não completou. Rode manualmente:"
    echo "     $PY -m pip install streamlit plotly pandas"
    read -r -p " Pressione Enter para fechar. "
    exit 1
  fi
fi

echo " Abrindo no navegador. Para encerrar, use Ctrl+C."
echo
$PY -m streamlit run app.py
