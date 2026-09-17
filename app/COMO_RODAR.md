# Como abrir o app

## ⚠️ Baixou o `app.py` novo? Baixe o `modelo.json` junto

Os dois **andam em par**. Um `app.py` novo com um `modelo.json` antigo dá erro — o app
avisa qual versão ele espera e qual encontrou, mas o conserto é sempre o mesmo:
**baixar os dois de novo**.

Se você tem a pasta completa do projeto, dá para regerar o artefato:

```
python preparar_modelo.py
```

---

## Faltou o `plotly`? Um comando resolve

```
pip install plotly
```

Depois rode de novo. *(Se estiver usando o atalho, baixe a versão nova dele — a
anterior só verificava o `streamlit` e por isso pulava a instalação do resto.)*

---

## ⚠️ Duplo clique no `app.py` não funciona

Se você deu duplo clique e a janela piscou e fechou, foi isso. Um app Streamlit não
é um script comum: ele precisa de um **servidor**. Sem ele, o Python abre, não acha o
que rodar e fecha antes de você conseguir ler o erro.

*(A versão atual do `app.py` já explica isso na tela e espera você apertar Enter,
em vez de sumir.)*

---

## Jeito fácil — duplo clique no atalho

| Seu sistema | Arquivo |
|---|---|
| **Windows** | `abrir_app.bat` |
| **Mac / Linux** | `abrir_app.sh` |

Eles conferem se o Python existe, instalam as dependências na primeira vez e abrem o
app no navegador. Só precisa ter **Python 3.9 ou superior** instalado.

No Mac e no Linux, pode ser preciso liberar o arquivo uma vez:

```bash
chmod +x abrir_app.sh
```

---

## Jeito manual — pelo terminal

Abra o terminal **na pasta onde está o `app.py`** e rode:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre em **http://localhost:8501**. Para encerrar: `Ctrl+C`.

> **Como abrir o terminal na pasta certa**
> **Windows:** clique na barra de endereço do Explorer, digite `cmd` e Enter.
> **Mac:** botão direito na pasta → Serviços → Novo Terminal na Pasta.

---

## Os arquivos

```
app/
├── app.py            ← o app
├── escala.py         ← escala real e otimizador de turnos (OBRIGATÓRIO)
├── modelo.json              ← OBRIGATÓRIO, no mesmo diretório do app.py
├── escala.py                ← OBRIGATÓRIO
├── requirements.txt
├── abrir_app.bat     ← atalho Windows
├── abrir_app.sh      ← atalho Mac / Linux
└── .streamlit/
    └── config.toml   ← opcional (pasta oculta; se sumir, o app funciona igual)
```

⚠️ `app.py` e `modelo.json` precisam ficar **lado a lado**. Sem o JSON o app não sobe.

---

## Se der problema

| Sintoma | Causa | Solução |
|---|---|---|
| A janela pisca e fecha | duplo clique no `app.py` | use `abrir_app.bat` / `.sh`, ou o terminal |
| `streamlit: command not found` | não está no PATH | `python -m streamlit run app.py` |
| `python: command not found` (Mac/Linux) | o comando é outro | use `python3` |
| `FileNotFoundError: modelo.json` | arquivo em outra pasta | ponha o JSON ao lado do `app.py` |
| `KeyError: 'capacidade_moto'` (ou outro bloco) | `modelo.json` antigo com `app.py` novo | baixe o `modelo.json` de novo |
| Tela vermelha "O modelo.json está desatualizado" | idem | idem — a mensagem diz o que falta |
| `KeyError: 'Média global'` (ou outra chave com acento) | `app.py` antigo lendo o JSON sem UTF-8 no Windows | baixe o `app.py` novo — corrigido |
| `Port 8501 is already in use` | outro app rodando | `streamlit run app.py --server.port 8502` |
| Fundo claro, texto sumido | `app.py` desatualizado | use a última versão — o tema é forçado no arquivo |
| `No module named 'plotly'` | dependência faltando | `pip install plotly` |
| `No module named 'pandas'` | idem | `pip install pandas` |

> Se quiser instalar tudo de uma vez, sem depender do `requirements.txt`:
> ```
> pip install streamlit plotly pandas
> ```

---

## Publicar na internet (opcional)

O caminho mais curto é o **Streamlit Community Cloud**, gratuito:

1. Suba a pasta `app/` num repositório do GitHub
2. Entre em [share.streamlit.io](https://share.streamlit.io) com a conta do GitHub
3. Aponte para o repositório e para o arquivo `app.py`

Ele lê o `requirements.txt` sozinho. Como o app carrega só 6 KB, sobe em segundos.

O app **não nomeia o estabelecimento** em lugar nenhum — descreve só a estrutura
("garagem automática · 21 andares · 378 vagas").

---

## Atualizar depois de uma nova versão do dataset

O app não lê o CSV — lê o `modelo.json`. Para regerar:

```bash
python preparar_modelo.py
```

Isso exige o `logs_estacionamento_v13.csv`, o `parametros.yaml` e os scripts do
projeto no mesmo lugar. É o único passo que depende do dataset completo.
