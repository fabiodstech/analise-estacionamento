"""Painel final do projeto — garagem automática em dados sintéticos.

⚠ ESTE ARQUIVO NÃO É EXECUTADO COM DUPLO CLIQUE.
   Um app Streamlit precisa de um servidor. No terminal, na pasta deste arquivo:

       streamlit run app.py

   Ou use os atalhos: abrir_app.bat (Windows) / abrir_app.sh (Mac e Linux).

Consome `modelo.json` (12 KB), não o dataset de 15 MB.
"""
import json

import numpy as np
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

import regras
from escala import (MANOBRISTAS, APOIO, QUADRO, ALMOCO, cobertura,
                    cobertura_com_almoco, horas_efetivas, tipo_de_escala,
                    horas_de, formata)

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    from plotly.subplots import make_subplots
    TEM_PLOTLY = True
except ModuleNotFoundError:
    TEM_PLOTLY = False


def _sem_servidor():
    try:
        from streamlit.runtime import exists
        return not exists()
    except Exception:
        return False


if _sem_servidor():
    print("\n" + "=" * 66)
    print("  Este arquivo não roda com duplo clique.")
    print("=" * 66)
    print("\n  Um app Streamlit precisa de um servidor. Abra o terminal na")
    print("  pasta deste arquivo e rode:\n")
    print("      streamlit run app.py\n")
    print("  Se der 'command not found', use:\n")
    print("      python -m streamlit run app.py\n")
    print("  Ou use o atalho: abrir_app.bat (Windows) / abrir_app.sh (Mac, Linux)")
    print("=" * 66)
    try:
        input("\n  Pressione Enter para fechar. ")
    except EOFError:
        pass
    raise SystemExit(0)


BASE = Path(__file__).parent
AZUL, VERDE, VERM, AMBAR, ROXO = "#2b7fff", "#3ddc84", "#ff6b63", "#e5a83a", "#a371f7"
AZUL_CLARO = "#5aa0ff"
# cinza-azulado das séries sem destaque. 3,16:1 sobre o fundo — acima dos 3:1
# exigidos para elemento gráfico que carrega informação (o comprimento da barra
# é informação). O #33405a de antes dava 1,89:1.
APAGADO = "#50608a"
CINZA, FUNDO, CARD = "#9aa6b6", "#070b16", "#0b1220"
DOW = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
DOW3 = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# "auto" e não "expanded": em tela estreita o Streamlit colapsa a barra
# sozinho. Com "expanded", no celular ela abria POR CIMA do conteúdo e a
# primeira coisa que a pessoa via era o selo, não o título.
st.set_page_config(page_title="Dataset sintético fiel · @fabiods.tech", page_icon="🅿️",
                   layout="wide", initial_sidebar_state="auto")

# ⚠ O tema escuro NÃO pode depender só do .streamlit/config.toml: a pasta é
#   oculta e some quando alguém baixa o projeto aos pedaços. E o CSS abaixo
#   não alcança os widgets (date_input, st.code, st.dataframe, checkbox), que
#   leem a cor do tema do Streamlit, não da folha de estilo. Então o próprio
#   app declara o tema e recarrega uma vez para aplicá-lo.
TEMA = {"theme.base": "dark",
        "theme.backgroundColor": FUNDO,
        "theme.secondaryBackgroundColor": CARD,
        "theme.primaryColor": AZUL,
        "theme.textColor": "#e8eef7",
        # Inter é a fonte dos carrosséis. O Streamlit sabe carregar uma fonte
        # externa por conta própria; assim ela vale também para os widgets.
        "theme.font": "Inter:https://fonts.googleapis.com/css2?"
                      "family=Inter:wght@400;500;600;700;800;900&display=swap,"
                      " sans-serif"}


def _garante_tema():
    try:
        from streamlit import config as _config
        if all(_config.get_option(k) == v for k, v in TEMA.items()):
            return
        for k, v in TEMA.items():
            _config.set_option(k, v)
    except Exception:
        return          # API interna: se mudar de versão, o CSS segura o resto
    if not st.session_state.get("_tema_aplicado"):
        st.session_state["_tema_aplicado"] = True
        st.rerun()      # o tema viaja na abertura da sessão; 1 rerun aplica


_garante_tema()


def data_br(iso):
    """2026-06-01 → 01/06/2026. O ISO no meio da frase parecia outra coisa."""
    a, m, d = str(iso).split("-")
    return f"{d}/{m}/{a}"


def num(v, casas=1, sinal=False):
    """Número em português: vírgula decimal e ponto de milhar."""
    s = f"{v:+,.{casas}f}" if sinal else f"{v:,.{casas}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


st.markdown(f"""<style>
 @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

 /* ---- tipografia: Inter é a fonte dos carrosséis; sem ela o app cai no
        Source Sans padrão do Streamlit, e é daí que vem boa parte da diferença
        de acabamento entre o app e os posts. Quem carrega a fonte é o tema
        (TEMA["theme.font"]); o @import e a regra abaixo são a rede de
        segurança para o caso de o tema não ser aplicado. ---- */
 .stApp, [data-testid="stSidebar"], .stApp p, .stApp li, .stApp label,
 .stApp span:not([data-testid="stIconMaterial"]), .stApp a, .stApp button,
 .stApp input, .stApp select, .stApp textarea, .stApp th, .stApp td,
 .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
   font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif !important}}
 /* ⚠ os ícones do Streamlit são uma fonte de ligaduras: se a regra acima
    alcançar esses spans, o ícone vira o texto "arrow_right" na tela. */
 [data-testid="stIconMaterial"], .material-icons, .material-symbols-rounded {{
   font-family:'Material Symbols Rounded' !important}}

 .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
   background:{FUNDO} !important; color:#e8eef7 !important}}
 [data-testid="stSidebar"] {{background:{CARD} !important;
   border-right:1px solid #16202e}}
 [data-testid="stSidebar"] *, .stApp p, .stApp label, .stApp span,
 .stApp h1, .stApp h2, .stApp h3, .stApp li {{color:#e8eef7}}
 .stApp small, [data-testid="stCaptionContainer"] {{color:{CINZA} !important}}

 /* ---- escala de títulos: o app misturava h3, h4 e h5 sem degrau visível ---- */
 [data-testid="stMain"] h1 {{font-size:2.85rem !important; font-weight:800 !important;
      letter-spacing:-.03em !important; line-height:1.06 !important}}
 [data-testid="stMain"] h2 {{font-size:1.7rem !important; font-weight:700 !important}}
 [data-testid="stMain"] h3 {{font-size:1.5rem !important; font-weight:700 !important;
      margin:2.6rem 0 .1rem !important}}
 [data-testid="stMain"] h4 {{font-size:1.2rem !important; font-weight:700 !important;
      margin:2.4rem 0 .1rem !important}}
 [data-testid="stMain"] h5 {{font-size:1.04rem !important; font-weight:700 !important;
      color:#fff !important; margin:2.1rem 0 .1rem !important}}
 [data-testid="stSidebar"] h3 {{font-size:1.02rem !important; font-weight:700 !important;
      color:#fff !important; margin:0 0 .2rem !important}}
 h1,h2,h3,h4,h5 {{letter-spacing:-.02em}}

 /* ---- medida da linha: em 1440px o texto corrido passava de 130 caracteres.
        68ch é a faixa confortável. Dentro de coluna, a coluna já limita. ---- */
 [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
 [data-testid="stMain"] [data-testid="stMarkdownContainer"] li {{
   max-width:68ch; line-height:1.68; font-size:.98rem; color:#c3ccd9}}
 [data-testid="stMain"] [data-testid="stMarkdownContainer"] blockquote {{
   max-width:68ch; border-left:2px solid {AZUL}}}
 [data-testid="stMain"] [data-testid="stCaptionContainer"] p {{
   max-width:68ch; line-height:1.6}}
 [data-testid="stColumn"] [data-testid="stMarkdownContainer"] p,
 [data-testid="stColumn"] [data-testid="stMarkdownContainer"] li,
 [data-testid="stColumn"] [data-testid="stCaptionContainer"] p,
 [data-testid="stSidebar"] p, .aviso p, .alerta p {{max-width:none}}
 /* métricas e tabelas têm <p> dentro: a regra de medida de linha acima não
    pode encolher o número grande da métrica. */
 [data-testid="stMetricValue"] p, [data-testid="stMetricLabel"] p,
 [data-testid="stMetricDelta"] p, [data-testid="stMain"] table p {{
   font-size:inherit !important; max-width:none; color:inherit; line-height:inherit}}
 [data-testid="stMarkdownContainer"] strong {{color:#fff}}

 /* ---- código: sem o tema aplicado o bloco saía branco ---- */
 .stApp code {{color:{AZUL_CLARO} !important;
   background:rgba(43,127,255,.10) !important; font-size:.86em}}
 [data-testid="stCode"], .stCode pre, .stApp pre {{
   background:{CARD} !important; border:1px solid #1e2a3d; border-radius:8px}}
 [data-testid="stCode"] code, [data-testid="stCode"] span {{
   color:#c3ccd9 !important; background:none !important; font-size:.84rem}}

 /* ---- abas ---- */
 .stTabs [data-baseweb="tab-highlight"] {{background:{AZUL} !important}}
 .stTabs [data-baseweb="tab-border"] {{background:#1e2a3d !important}}
 .stTabs button[role="tab"] p, .stTabs [data-testid="stTab"] p {{
   font-size:.95rem !important; color:{CINZA}}}
 .stTabs button[aria-selected="true"] p,
 .stTabs [data-testid="stTab"][aria-selected="true"] p {{
   color:#fff; font-weight:600}}
 /* divisória entre os três blocos de abas */
 .stTabs [role="tablist"] [data-testid="stTab"]:nth-of-type(3),
 .stTabs [role="tablist"] [data-testid="stTab"]:nth-of-type(7) {{
   margin-left:20px; padding-left:24px; border-left:1px solid #1e2a3d}}

 /* ---- métricas ---- */
 [data-testid="stMetricLabel"] p {{color:{CINZA} !important; font-size:.84rem}}
 [data-testid="stMetricValue"] {{color:#fff !important; font-size:1.8rem;
   font-weight:700; letter-spacing:-.02em}}
 [data-testid="stMetricDelta"] {{font-size:.8rem}}

 hr {{border-color:#1e2a3d !important; margin:2.4rem 0 !important}}

 .rodape {{color:#6f7d90;font-size:.82rem;text-align:center;padding:26px 0 6px}}
 /* bloco de marca da barra lateral — o mesmo par branco/azul dos carrosséis */
 .marca-pill {{display:inline-block;font-size:.63rem;letter-spacing:.10em;
   color:{AZUL_CLARO};border:1px solid rgba(43,127,255,.35);border-radius:999px;
   padding:4px 11px;background:rgba(43,127,255,.09)}}
 .marca-tit {{font-size:1.45rem;font-weight:800;letter-spacing:-.03em;
   line-height:1.12;color:#fff;margin:14px 0 2px}}
 .marca-tit span {{color:{AZUL}}}
 /* tira de procedência, logo abaixo do subtítulo */
 .proveniencia {{display:flex;flex-wrap:wrap;gap:8px 10px;margin:2px 0 6px}}
 .proveniencia span {{font-size:.72rem;color:{CINZA};background:rgba(43,127,255,.06);
   border:1px solid #1e2a3d;border-radius:999px;padding:3px 11px;white-space:nowrap}}
 .proveniencia b {{color:#c3ccd9;font-weight:600}}
 /* ---- as quatro caixas, cada uma com um trabalho ----
    .achado   conclusão da seção — o cartão neon dos carrosséis, um por seção
    .certo    o estado correto de um controle interativo
    .ressalva o limite do dado — discreta, mas sempre idêntica
    .alerta   o estado de erro
    .fluxo    o pipeline do projeto                                        ---- */
 .achado, .certo, .ressalva, .alerta, .fluxo {{
   font-size:.92rem; line-height:1.62; max-width:72ch;
   padding:16px 20px; border-radius:10px; margin:10px 0 22px}}
 .achado {{color:#dce4ef; background:linear-gradient(180deg,
            rgba(43,127,255,.12), rgba(43,127,255,.05));
           border:1px solid rgba(43,127,255,.42);
           box-shadow:0 0 26px rgba(43,127,255,.13)}}
 .achado b {{color:#fff}}
 .certo {{color:#c3ccd9; background:rgba(61,220,132,.06);
          border-left:3px solid {VERDE}; border-radius:0 8px 8px 0}}
 .certo b {{color:#dff5e8}}
 .ressalva {{color:{CINZA}; background:none; border:0;
             border-left:2px solid #2a3a52; border-radius:0;
             padding:4px 0 4px 16px; font-size:.88rem; margin:6px 0 20px}}
 .ressalva b {{color:#c3ccd9; font-weight:600}}
 .alerta {{color:#e3c9c7; background:rgba(255,107,99,.09);
           border-left:3px solid {VERM}; border-radius:0 8px 8px 0}}
 .alerta b {{color:#ffd9d6}}
 .fluxo {{color:#c3ccd9; background:{CARD}; border:1px solid #1e2a3d;
          font-size:.9rem}}
 .fluxo b {{color:{AZUL_CLARO}; font-weight:600}}
 /* st.info/st.warning nativos: discretos, para não disputar com o .achado */
 [data-testid="stAlert"] {{background:rgba(43,127,255,.06) !important;
   border:1px solid rgba(43,127,255,.22); border-radius:10px; max-width:72ch}}
 [data-testid="stAlert"] p {{color:#c3ccd9 !important; font-size:.92rem}}
 /* respiro em volta do gráfico: antes ele encostava no texto seguinte */
 [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {{
   margin:2px 0 18px}}
 [data-testid="stMain"] [data-testid="stExpander"] details {{
   border:1px solid #1e2a3d !important; border-radius:10px; background:{CARD}}}
 /* card dos controles interativos — borda discreta, sem competir com .achado */
 [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {{
   border-color:#1e2a3d !important; border-radius:10px; background:{CARD}}}
</style>""", unsafe_allow_html=True)


ARQ_MODELO = BASE / "modelo.json"


def _assinatura():
    """mtime + tamanho: é o que faz o cache perceber um modelo.json novo."""
    s = ARQ_MODELO.stat()
    return (s.st_mtime_ns, s.st_size)


@st.cache_data
def carregar(assinatura):
    # `assinatura` não é usada no corpo de propósito: ela existe para ser a
    # chave do cache. Sem isso, trocar o modelo.json não muda nada na tela até
    # reiniciar o servidor — o app mostraria número velho sem avisar.
    #
    # ⚠ encoding="utf-8" é OBRIGATÓRIO. Sem ele, o Windows lê o arquivo como
    #   cp1252 e as chaves acentuadas ("Média global") viram outra coisa —
    #   o app quebra com KeyError num acento. No Linux o padrão já é UTF-8,
    #   então o bug só aparece na máquina de quem usa.
    return json.loads(ARQ_MODELO.read_text(encoding="utf-8"))


VERSAO_ESPERADA = 5

try:
    M = carregar(_assinatura())
except FileNotFoundError:
    st.error("### Falta o `modelo.json`\n\n"
             "Ele precisa estar na mesma pasta do `app.py`. Os dois vêm juntos.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"### O `modelo.json` está corrompido\n\n"
             f"O arquivo existe, mas não é um JSON válido (`{e}`). Baixe o arquivo "
             f"de novo — provavelmente veio truncado.")
    st.stop()

# ⚠ O erro mais provável de quem baixa o projeto aos pedaços: app.py novo com
#   modelo.json antigo. Sem esta checagem o app estoura um KeyError seco.
_faltando = [c for c in ("capacidade", "capacidade_moto", "manobras", "moto_atual",
                         "receita", "recarga_ev", "experimento_denominador",
                         "experimento_bloqueado", "projeto") if c not in M]
if _faltando or M.get("meta", {}).get("versao_artefato", 1) < VERSAO_ESPERADA:
    st.error(
        f"### O `modelo.json` está desatualizado\n\n"
        f"Este `app.py` precisa da versão **{VERSAO_ESPERADA}** do artefato, e o "
        f"arquivo encontrado é da versão "
        f"**{M.get('meta', {}).get('versao_artefato', 1)}**.\n\n"
        + (f"Blocos que faltam: `{'`, `'.join(_faltando)}`\n\n" if _faltando else "")
        + "**Como resolver:** baixe o `modelo.json` novo e substitua o que está na "
          "pasta, ao lado do `app.py`. Os dois vêm juntos e precisam ser da mesma "
          "versão.\n\n"
          "Se você tem o projeto completo, dá para regerar com:\n\n"
          "```\npython preparar_modelo.py\n```")
    st.stop()

CAP, CONTRATADAS = M["capacidade"]["carro"], M["capacidade"]["contratadas"]
CAP_MOTO = M["capacidade_moto"]["vagas"]
FERIADOS = set(M["feriados"])
EV = M["recarga_ev"]

if not TEM_PLOTLY:
    st.warning("**Falta a dependência `plotly`.** O app funciona com gráficos "
               "simples. Para os completos: `pip install plotly`")


# ============================ ESTILO DOS GRÁFICOS ============================
# Um template só, em vez do mesmo update_layout repetido nove vezes. O fundo do
# gráfico é o MESMO da página: o retângulo mais escuro de antes desenhava uma
# caixa em volta de cada gráfico, sem separar nada.
PLOTLY_CONF = {"displayModeBar": False, "scrollZoom": False}

if TEM_PLOTLY:
    _eixo = dict(gridcolor="#16202e", zeroline=False, linecolor="#16202e",
                 ticks="outside", tickcolor="#16202e", ticklen=4,
                 title=dict(font=dict(color=CINZA, size=12)),
                 tickfont=dict(color=CINZA, size=11))
    pio.templates["garagem"] = go.layout.Template(layout=dict(
        paper_bgcolor=FUNDO, plot_bgcolor=FUNDO, separators=",.",
        font=dict(color="#c3ccd9", size=12,
                  family="Inter, 'Segoe UI', system-ui, sans-serif"),
        colorway=[AZUL, ROXO, AZUL_CLARO, AMBAR, CINZA],
        xaxis=_eixo, yaxis=_eixo,
        legend=dict(orientation="h", y=1.16, x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(color=CINZA, size=11)),
        margin=dict(l=8, r=8, t=44, b=8),
        hoverlabel=dict(bgcolor=CARD, bordercolor=AZUL,
                        font=dict(color="#e8eef7", size=12)),
    ))
    pio.templates.default = "garagem"


# As contas vivem em `regras.py`, sem Streamlit, para poderem ser testadas
# (`python testes_app.py`). Aqui ficam só os atalhos que injetam o modelo.
def curva_ocupacao(dia, tipo="carro"):
    return regras.curva_ocupacao(dia, M, FERIADOS, tipo)


def curva_manobras(dia):
    return regras.curva_manobras(dia, M, FERIADOS)


def tarifa(minutos, veiculo):
    return regras.tarifa(minutos, veiculo, M["precos"])


def erlang_b(taxa_dia, n_tomadas, janela_h=12):
    return regras.erlang_b(taxa_dia, n_tomadas, EV["duracao_h"], janela_h)


def linhas(traces, titulo_y, altura=380, extras=None):
    if not TEM_PLOTLY:
        st.line_chart(pd.DataFrame({t["nome"]: t["y"] for t in traces},
                                   index=range(24)), height=altura - 60)
        return
    fig = go.Figure()
    for t in traces:
        fig.add_trace(go.Scatter(
            x=list(range(24)), y=t["y"], mode="lines", name=t["nome"],
            line=dict(color=t["cor"], width=t.get("w", 3), dash=t.get("dash")),
            fill=t.get("fill"), fillcolor=t.get("fillcolor"),
            hovertemplate="%{x}h · %{y:.0f}<extra>" + t["nome"] + "</extra>"))
    for e in (extras or []):
        fig.add_hline(**e)
    fig.update_layout(height=altura, hovermode="x unified",
                      xaxis=dict(title="hora do dia", dtick=2, ticksuffix="h"),
                      yaxis=dict(title=titulo_y))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)


# ================================ SIDEBAR ================================
# A data saiu daqui: ela só afeta três das sete abas, e na barra lateral não
# havia como saber disso — mudar a data em "O método" não fazia nada. Agora o
# seletor vive dentro das abas que dependem dele (ver `seletor_data`).
HOJE = date(2026, 8, 13)
if "_data" not in st.session_state:
    st.session_state["_data"] = HOJE
dia = st.session_state["_data"]


def _data_mudou(k):
    """Callback do seletor: quem mexeu vira a fonte da verdade.

    Roda ANTES do script, então quando os três seletores forem criados nesta
    mesma execução, `_data` já está atualizado.
    """
    st.session_state["_data"] = st.session_state[k]


def seletor_data(onde):
    """O mesmo seletor, replicado nas três abas que usam a data.

    O valor de verdade é `_data`. Como as três cópias têm chave própria, o
    `value=` seria ignorado a partir da segunda execução — por isso cada uma
    alinha a própria chave a `_data` ANTES de ser criada (depois de criada, a
    chave do widget não pode mais ser escrita).
    """
    k = f"data_{onde}"
    st.session_state[k] = st.session_state["_data"]
    c = st.columns([1, 2.6])
    d = c[0].date_input("Cenário do dia", min_value=HOJE,
                        max_value=HOJE + timedelta(days=365),
                        key=k, on_change=_data_mudou, args=(k,),
                        help="Escolher 20/08 é escolher 'uma quinta comum'. O modelo "
                             "só enxerga dia da semana e feriado — não existe "
                             "previsão para uma data específica.")
    c[0].caption(DOW[d.weekday()] + (" · feriado" if str(d) in FERIADOS else "")
                 + " — o modelo lê só isto: dia da semana e feriado")
    return d


with st.sidebar:
    st.markdown('<div class="marca">'
                '<div class="marca-pill">PROJETO COMPLETO</div>'
                '<div class="marca-tit">Dataset<br><span>sintético fiel</span></div>'
                '</div>', unsafe_allow_html=True)
    st.divider()
    st.metric("Erro do modelo", f"{num(M['meta']['mae_diario'], 2)} carros")
    st.caption(f"{num(M['meta']['mae_diario']/CAP*100, 2)} p.p. das {CAP} vagas · medido "
               "em 46 dias que o modelo nunca viu")

st.title("Como se constrói um dataset sintético fiel")
st.caption("E como descobrir que fidelidade não é suficiência · "
           "caso: garagem automática de 21 andares no centro de São Paulo")

# Procedência à vista: de qual artefato vieram os números desta tela, quanto
# tempo eles cobrem, e que são sintéticos. Tudo sai do próprio modelo.json.
st.markdown(
    f'<div class="proveniencia">'
    f'<span>dados <b>sintéticos</b></span>'
    f'<span>modelo v{M["meta"]["versao_artefato"]}</span>'
    f'<span>base <b>{M["meta"]["gerado_de"]}</b></span>'
    f'<span>{M["dias_periodo"]} dias cobertos</span>'
    f'<span>regime a partir de {data_br(M["meta"]["marco"])}</span>'
    f'</div>', unsafe_allow_html=True)

# Os rótulos não têm mais emoji: eram sete cores fora da paleta, e a aba ativa
# já é marcada pelo sublinhado azul. O agrupamento em três blocos (como se
# constrói · o painel · o que ele não pode dizer) é feito no CSS, por uma
# divisória antes da 3ª e da 7ª aba — sem mudar nome nem ordem.
a0, ax, a1, a5, a2, a3, a4 = st.tabs(
    ["O método", "Faça o erro", "Operação do dia", "Escala",
     "Receita", "Capacidade", "Limites"])

PR = M["projeto"]

# ============================== ABA MÉTODO ==============================
with a0:
    st.markdown("""
Os dados reais não podem sair da empresa. E dado sintético mal feito **não ensina
nada** — ele sempre parece certo, roda sem erro e preenche todas as colunas, mesmo
mentindo o tempo todo.

Então o projeto virou outra coisa: mapear as regras de operação com quem trabalha na
garagem, transformar cada uma em código **e em teste**, e usar o resultado para
responder perguntas de negócio de verdade.
    """)
    c = st.columns(4)
    c[0].metric("Seções de regra mapeadas", PR["secoes_de_regra"])
    c[1].metric("Asserções automatizadas", f"{PR['asercoes']}/{PR['asercoes']}",
                f"eram {PR['asercoes_antes']}", delta_arrow="off")
    c[2].metric("Versões do gerador", PR["versoes_do_gerador"])
    c[3].metric("Validação externa", f"{num(PR['validacao_externa'], 2)}×",
                "recarga elétrica", delta_color="off", delta_arrow="off")

    st.divider()
    st.markdown("##### O gerador não tem nenhum número literal")
    st.markdown(f"""
São **{PR['valores_total']} valores numéricos** vivendo num arquivo de parâmetros, lido
pelo gerador **e** pelo validador. Cada bloco declara **de onde o número veio** — é o
que separa um dado apurado de um chute meu:
    """)
    c = st.columns(4)
    c[0].metric("informados pela operação", PR["val_fabio"],
                f"{PR['val_fabio']/PR['valores_total']:.0%} do total",
                delta_color="off", delta_arrow="off")
    c[1].metric("medidos em fonte externa", PR["val_medido"],
                "app do carregador", delta_color="off", delta_arrow="off")
    c[2].metric("referência de mercado", PR["val_externo"],
                "tarifa de energia", delta_color="off", delta_arrow="off")
    c[3].metric("ainda sem respaldo", PR["val_arbitrado"],
                f"{PR['val_arbitrado']/PR['valores_total']:.0%} — declarados como tal",
                delta_color="inverse", delta_arrow="off")
    st.caption(f"Os {PR['val_sem_origem']} restantes são estruturais — datas de "
               "calendário, chaves de configuração, um valor derivado de outro — e "
               "não carregam origem própria.")

    st.markdown("##### Alguns dos parâmetros, e de onde vieram")
    st.markdown("""
| Parâmetro | Valor | De onde veio |
|---|---|---|
| Tarifa de 1 hora, carro | R$ 15,00 | informado pela operação |
| Hora adicional, tabela antiga | R$ 6,00 | informado pela operação |
| Energia por sessão de recarga | 10,71 kWh | **medido**: 12 meses do app do carregador |
| Tarifa da recarga, desde jun/26 | R$ 2,50 / kWh | informado — reajuste trimestral desde a instalação |
| Custo do kWh para a casa | R$ 0,99 a 1,03 | ⚠ **referência de mercado**, não é dado da operação |
| Duração das viagens do morador | 3 a 7 dias | ⚠ **arbitrado** — não segue padrão e a operação não consegue observar |
    """)
    st.caption("Cada linha do arquivo carrega essa marcação. É ela que impede um "
               "palpite meu de virar, três meses depois, um número que parece apurado.")

    st.markdown("""
E se o gerador pedir um parâmetro que não está declarado, **ele para**. Esta mensagem
aconteceu de verdade, na primeira execução, porque escrevi o caminho errado no código:
    """)
    st.code("ParametroAusente: 'segmentos.morador.persona_ev_dependente_recargas_dia'\n"
            "não está em parametros.yaml. Declare o parâmetro antes de usá-lo.",
            language="text")
    st.caption("O parâmetro existia — em `recarga_ev`, não em `segmentos.morador`. "
               "Sem essa checagem o gerador teria rodado em silêncio com outro valor, "
               "e nenhum teste pegaria.")

    st.markdown(f"""
Isso existe porque a auditoria encontrou **{PR['numeros_so_no_codigo']} números que
viviam só no código** e contradiziam ou faltavam no documento de regras — a tarifa de
recarga, os valores de mensalidade, a taxa de inadimplência, o bloqueio automático.

**Nenhum teste pegava**, porque o validador tinha as próprias constantes, copiadas do
gerador. Agora os dois leem o mesmo arquivo.
    """)
    st.markdown('<div class="fluxo">'
                '<b>regras de negócio</b> → <b>parametros.yaml</b> → '
                '<b>gerador</b> ⇄ <b>validador</b> → <b>análise</b> → <b>este painel</b>'
                '<br><br>Um número não pode divergir da regra escrita em silêncio.'
                '</div>', unsafe_allow_html=True)

    with st.expander(f"E o que ainda não tem respaldo — {PR['pendencias']} pendências declaradas"):
        st.markdown("""
O arquivo termina com a lista do que continua **arbitrado**, para que ninguém
(inclusive eu) trate como medido:

- **o custo do kWh** — sem acesso à conta de energia, e com geração solar no meio o
  custo efetivo varia ao longo do dia
- **o dimensionamento do sistema solar** — potência, geração e modalidade de
  compensação desconhecidas
- **a duração das viagens do morador** — não segue padrão, e a operação não consegue
  observar: a ausência de um cliente não gera evento nenhum
- **o tamanho da base de clientes** — é escolha de modelagem, não medição

Cada um limita alguma conclusão, e cada limitação está escrita ao lado do número que
ela afeta.
        """)

    st.divider()
    st.markdown("##### E metade dos achados não eram achados")
    c = st.columns([1, 2])
    c[0].metric("Achados auditados", PR["achados_auditados"])
    c[0].metric("Reprovados", PR["achados_reprovados"],
                f"-{PR['achados_reprovados']/PR['achados_auditados']:.0%}",
                delta_color="off", delta_arrow="off")
    c[1].markdown("""
Classifiquei todos os achados da análise **pela origem**. Oito dos quinze eram o
gerador reproduzindo os próprios parâmetros — incluindo coisas que eu tinha escrito
com entusiasmo.

> Dado sintético só produz achado sobre o mundo quando confrontado com **fonte
> externa**, com **regra documentada**, quando é **derivado das regras** e não do
> dataset, ou quando é sobre o **dado enquanto dado**.
> Todo o resto é o gerador falando sozinho.
    """)
    st.info("**A aba ao lado deixa você cometer três desses erros.** "
            "É mais rápido de entender errando do que lendo.")

# ============================== ABA FAÇA O ERRO ==============================
with ax:
    st.markdown("### Três erros que este projeto cometeu")
    st.caption("Todos foram publicados como conclusão antes de serem pegos. "
               "Nenhum foi pego por teste.")

    # ---------- 1. o denominador ----------
    st.markdown("#### 1 · A métrica que muda 33 pontos conforme quem você conta")
    st.markdown("""
A diretoria orienta que avulsos pagando com cartão usem o **totem**. Medir a adesão
parece trivial: dividir quem foi ao totem por quem podia ter ido.

**Quem podia ter ido?** Marque abaixo quem você contaria como "avulso pagando cartão".
    """)
    D = M["experimento_denominador"]
    rot = {"hotel": "Hóspede de hotel", "moto": "Moto", "selo": "Convênio de selo",
           "recarga": "Recarga elétrica", "carga": "Carga e descarga"}
    obrig = {"hotel": "Passe Livre é caixa obrigatório — ativação manual",
             "moto": "o totem cobraria valor de carro",
             "selo": "o desconto é aplicado manualmente pelo operador",
             "recarga": "o serviço é lançado à mão no caixa",
             "carga": "tarifa própria, selecionada pelo operador"}
    # Os controles ficam dentro de um card: separa "o que você mexe" de "o que
    # muda por causa disso", que antes eram distinguidos só pelo espaçamento.
    with st.container(border=True):
        cols = st.columns(3)
        incl = {}
        for i, (k, nome) in enumerate(rot.items()):
            incl[k] = cols[i % 3].checkbox(nome, value=True, key=f"den_{k}")
    # ⚠ O mensalista inadimplente ENTRA no denominador. A cancela não abre, o
    #   sistema avisa que a mensalidade venceu e ele tira ticket como qualquer
    #   avulso ("mensalista X — entrada como avulso"); na saída paga no totem
    #   normalmente. Já esteve na lista de exclusões acima, por erro meu de
    #   regra — o gerador sempre soube disso (5 no totem, 2 no caixa).
    #   Desde o artefato v6 o `preparar_modelo.py` já soma dentro de `nucleo`,
    #   então aqui não se soma de novo. A chave antiga fica aceita para não
    #   quebrar com um modelo.json anterior.
    t, c_ = D["nucleo"]
    if "inadimplente" in D:                    # artefato anterior ao v6
        t += D["inadimplente"][0]
        c_ += D["inadimplente"][1]
    dentro = []
    for k, on in incl.items():
        if on:
            t += D[k][0]; c_ += D[k][1]; dentro.append(k)
    ader = t / (t + c_) * 100

    cc = st.columns([1, 2])
    cc[0].metric("Aderência ao totem", f"{num(ader)}%", f"n = {t+c_}",
                 delta_color="off", delta_arrow="off")
    if dentro:
        cc[1].markdown('<div class="alerta">Você está contando como <b>desvio do '
                       'atendente</b> pagamentos que a regra <b>obriga</b> a ir ao '
                       'caixa:<br>' + "<br>".join(
                           f"· <b>{rot[k]}</b> — {obrig[k]}" for k in dentro) +
                       '</div>', unsafe_allow_html=True)
    else:
        cc[1].markdown('<div class="certo"><b>Este é o denominador correto:</b> só '
                       'quem realmente podia usar o totem. Repare que o valor bate com '
                       'o parâmetro do gerador — é assim que se sabe que o '
                       'denominador fechou.</div>', unsafe_allow_html=True)

    if TEM_PLOTLY:
        cen = [("Categoria \"Avulso\"", list(rot)), ("+ só carro", ["selo", "recarga", "carga"]),
               ("+ sem selo e recarga", ["carga"]), ("Correto", [])]
        xs, ys = [], []
        for nome, ks in cen:
            tt, cq = D["nucleo"]                   # ver a nota acima sobre o v6
            if "inadimplente" in D:
                tt += D["inadimplente"][0]
                cq += D["inadimplente"][1]
            for k in ks:
                tt += D[k][0]; cq += D[k][1]
            xs.append(nome); ys.append(tt / (tt + cq) * 100)
        fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=[VERM, APAGADO, APAGADO, VERDE],
                               text=[f"{num(v)}%" for v in ys], textposition="outside"))
        fig.add_hline(y=ader, line=dict(color=AZUL, dash="dash", width=2),
                      annotation_text="sua escolha", annotation_position="right",
                      annotation_font=dict(color=AZUL, size=11))
        fig.update_layout(height=300, showlegend=False, bargap=.45,
                          margin=dict(l=8, r=86, t=34, b=8),
                          yaxis=dict(title="% pago no totem", range=[0, 112]),
                          xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)

    st.markdown("""
**A causa raiz não estava no dado.** Estava no meu próprio documento de regras: a
fórmula de uma seção classificava como desvio o que outra seção tornava obrigatório.

E eu publiquei um valor intermediário — parei uma camada cedo, porque **carga e
descarga não tem rótulo no sistema** e ficava escondido dentro de avulso.
    """)

    st.divider()

    # ---------- 2. a entrada bloqueada ----------
    st.markdown("#### 2 · A linha que diz \"entrada\" e não é entrada")
    B = M["experimento_bloqueado"]
    st.markdown("""
Quando um mensalista está com o boleto em aberto, ele é **barrado na cancela**. O
sistema registra essa tentativa como `Sentido = Entrada`.

O veículo **não entrou** — foi impedido. Some as entradas e saídas para reconstruir a
ocupação e veja o que acontece:
    """)
    with st.container(border=True):
        contar = st.toggle("Contar tentativas barradas como entrada", value=False)
    cc = st.columns(3)
    for i, (tv, cap) in enumerate([("moto", B["moto"]["capacidade"]),
                                   ("carro", B["carro"]["capacidade"])]):
        d = B[tv]["com" if contar else "sem"]
        excede = d[0] > cap
        cc[i].metric(f"Pico de {tv}", f"{d[0]:.0f} / {cap}",
                     f"{d[0]/cap*100:.0f}% da capacidade",
                     delta_color="inverse" if excede else "off",
                     delta_arrow="off")
    cc[2].metric("Ocupação média de moto",
                 f"{num(B['moto']['com' if contar else 'sem'][1])}")

    if contar:
        st.markdown(f'<div class="alerta"><b>{B["moto"]["com"][0]} motos num espaço '
                    f'que comporta {B["moto"]["capacidade"]}.</b> Nenhuma linha do '
                    f'dataset está errada — cada registro é válido. O erro só aparece '
                    f'na <b>soma</b>, e foi o número impossível que denunciou.'
                    f'<br><br>Não foi um teste que pegou: foi a física do prédio.'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="certo">Filtrando as tentativas barradas, tudo cabe. '
                    'Esta é a regra que virou coluna derivada no dicionário de dados: '
                    '<code>entrada_efetiva = Sentido == \'Entrada\' and Status != '
                    '\'Bloqueado\'</code></div>', unsafe_allow_html=True)
    st.caption(f"Medido no {B['fonte']}. A versão atual do gerador já não produz "
               "bloqueios fora do período em que o sistema de bloqueio existia.")

    st.divider()

    # ---------- 3. o modelo ----------
    st.markdown("#### 3 · Metade da vantagem do modelo era uma linha de código")
    E = M["experimento_modelo"]
    # cinto de segurança: se por qualquer motivo o arquivo chegar mal decodificado,
    # casa a chave ignorando acentos em vez de estourar KeyError.
    import unicodedata as _u

    def _chave(d, nome):
        if nome in d:
            return d[nome]
        norm = lambda x: _u.normalize("NFKD", x).encode("ascii", "ignore").lower()
        for k, v in d.items():
            if norm(k) == norm(nome):
                return v
        raise KeyError(nome)
    st.markdown("""
Árvores contra baselines na previsão de ocupação, validação cronológica. As árvores
vencem — mas o período de teste fica inteiro **depois de uma mudança conhecida na
operação**, e elas aprenderam isso.

Dê ao baseline a mesma informação: a média por dia da semana, calculada **duas vezes,
uma por regime**. Continua sendo baseline — duas tabelas, sem treino.
    """)
    with st.container(border=True):
        degrau = st.toggle("Dar o degrau de junho ao baseline", value=False)
    base_nome = "Baseline sazonal + degrau" if degrau else "Baseline sazonal"
    mae_base, mae_gb = _chave(E, base_nome), _chave(E, "Gradient Boosting")
    ganho = (mae_base - mae_gb) / mae_base * 100
    pval = (E["p_gb_vs_baseline_degrau"] if degrau
            else E["p_gb_vs_baseline_simples"])

    cc = st.columns(3)
    cc[0].metric("Erro do baseline", f"{num(mae_base, 2)} carros")
    cc[1].metric("Erro do Gradient Boosting", f"{num(mae_gb, 2)} carros")
    cc[2].metric("Vantagem das árvores", f"{num(ganho)}%",
                 "significativa" if pval < .05 else "NÃO significativa",
                 delta_color="normal" if pval < .05 else "inverse",
                 delta_arrow="off")

    if TEM_PLOTLY:
        ordem = ["Média global", "Baseline sazonal", "Persistência 7 dias",
                 "Baseline sazonal + degrau", "Random Forest", "Gradient Boosting"]
        cores = [AZUL if n == base_nome else (ROXO if "Boosting" in n or "Forest" in n
                 else APAGADO) for n in ordem]
        fig = go.Figure(go.Bar(y=ordem[::-1], x=[_chave(E, n) for n in ordem][::-1],
                               orientation="h", marker_color=cores[::-1],
                               text=[f"{num(_chave(E, n), 2)}" for n in ordem][::-1],
                               textposition="outside"))
        fig.update_layout(height=300, showlegend=False, bargap=.35,
                          margin=dict(l=8, r=58, t=16, b=8),
                          xaxis=dict(title="MAE (carros)"),
                          yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)

    if degrau:
        st.markdown(f'<div class="achado"><b>Uma linha de código percorreu 54% da '
                    f'distância.</b> O que sobra — {num(ganho)}% — <b>não é '
                    f'estatisticamente significativo</b> (Wilcoxon, p = {num(pval, 3)}) '
                    f'num teste de 46 dias.<br><br>O modelo gasta 92% da capacidade '
                    f'explicativa em três coisas: domingo, dia da semana e feriado.'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alerta">Sem o degrau, as árvores ganham {num(ganho)}% '
                    f'com significância (p = {num(pval, 3)}). Parece caso encerrado — '
                    f'ligue o botão acima.</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("""
##### O que os três têm em comum

Nenhum foi pego por teste. **Todos foram pegos por alguém que conhece a operação lendo
o resultado e dizendo "não é assim que funciona".**

Não é acaso: um teste automatizado compara o dado com o que eu declarei esperar — e
nos três casos o problema era a **expectativa**, não a execução. A suíte de 25
asserções passava em todas as versões.
    """)

# ================================ ABA 1 ================================
with a1:
    dia = seletor_data("operacao")
    occ, man = curva_ocupacao(dia), curva_manobras(dia)
    pico_o, h_o = max(occ), occ.index(max(occ))
    pico_m, h_m = max(man), man.index(max(man))

    c = st.columns(4)
    c[0].metric("Ocupação média", f"{sum(occ)/24:.0f} carros",
                f"{sum(occ)/24/CAP*100:.0f}% da capacidade",
                delta_color="off", delta_arrow="off")
    c[1].metric("Pico de ocupação", f"{pico_o:.0f} carros", f"às {h_o}h",
                delta_color="off", delta_arrow="off")
    c[2].metric("Pico de movimentos", f"{pico_m:.0f}/hora", f"às {h_m}h",
                delta_color="off", delta_arrow="off")
    c[3].metric("Vagas livres no pico", f"{CAP-pico_o:.0f}")

    st.markdown("##### Ocupação × movimentos ao longo do dia")
    st.caption("A ocupação diz quantos carros estão no prédio. Os movimentos dizem "
               "quantas entradas e saídas acontecem — e os dois picos não coincidem.")
    # ⚠ Dois painéis, não duas linhas no mesmo eixo. Ocupação é ESTOQUE (carros
    #   parados) e movimento é FLUXO (entradas e saídas por hora): dividir a
    #   mesma escala sugeria que os números são comparáveis, e não são. O que o
    #   gráfico precisa mostrar é que os PICOS não coincidem — e isso depende do
    #   eixo x comum, não do y.
    if TEM_PLOTLY:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.09,
                            row_heights=[.62, .38])
        fig.add_trace(go.Scatter(x=list(range(24)), y=occ, mode="lines",
                                 name="carros no prédio", fill="tozeroy",
                                 fillcolor="rgba(43,127,255,.16)",
                                 line=dict(color=AZUL, width=3),
                                 hovertemplate="%{x}h · %{y:.0f} carros"
                                               "<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=list(range(24)), y=man, mode="lines",
                                 name="movimentos de carro por hora",
                                 line=dict(color=ROXO, width=2.6, dash="dot"),
                                 hovertemplate="%{x}h · %{y:.0f} movimentos"
                                               "<extra></extra>"), row=2, col=1)
        fig.add_hline(y=CONTRATADAS, row=1, col=1,
                      line=dict(color=AMBAR, dash="dash", width=1.4),
                      annotation_text=f"vagas contratadas ({CONTRATADAS})",
                      annotation_position="top left",
                      annotation_font=dict(color=AMBAR, size=11))
        fig.update_layout(height=440, hovermode="x unified",
                          margin=dict(l=8, r=8, t=44, b=8))
        fig.update_yaxes(title_text="carros no prédio", row=1, col=1)
        fig.update_yaxes(title_text="movimentos/hora", row=2, col=1)
        fig.update_xaxes(title_text="hora do dia", dtick=2, ticksuffix="h",
                         row=2, col=1)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)
    else:
        st.line_chart(pd.DataFrame({"carros no prédio": occ}, index=range(24)),
                      height=220)
        st.line_chart(pd.DataFrame({"movimentos de carro por hora": man},
                                   index=range(24)), height=160)

    if pico_m > 0:
        faixa = [h for h in range(24) if man[h] >= pico_m * .8]
        st.markdown(f'<div class="achado"><b>O pico de movimentos vem antes do pico de '
                    f'ocupação</b> — {h_m}h contra {h_o}h. Ocupação é <b>estoque</b>; '
                    f'movimento é <b>fluxo</b>, e cada movimento de carro consome um '
                    f'manobrista e uma viagem de elevador (regras 15 e 23). Moto não '
                    f'entra: o cliente estaciona sozinho.</div>'
                    f'<div class="ressalva">'
                    f'<b>⚠ A forma desta curva é do dado sintético</b>, cujas janelas de '
                    f'chegada e saída são constantes do gerador. O que vale aqui é a '
                    f'<b>relação entre as duas curvas</b>, não os valores por hora.</div>',
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("##### A semana inteira")
    st.caption("O sábado move quase o mesmo que um dia útil, numa janela de comércio "
               "2 horas mais curta — logo, mais movimento por hora aberta. A direção é "
               "garantida pelas regras; os valores vêm do dado sintético.")
    sem = []
    for w in range(7):
        d = dia + timedelta(days=(w - dia.weekday()) % 7)
        mm, oo = curva_manobras(d), curva_ocupacao(d)
        sem.append({"dia": DOW3[w], "movimentos no dia": sum(mm),
                    "pico por hora": max(mm),
                    "ocupação média": sum(oo) / 24})
    sem = pd.DataFrame(sem).set_index("dia")
    if TEM_PLOTLY:
        cores = [AZUL] * 5 + [ROXO, APAGADO]
        fig = go.Figure(go.Bar(x=sem.index, y=sem["movimentos no dia"],
                               marker_color=cores,
                               text=[f"{v:.0f}" for v in sem["movimentos no dia"]],
                               textposition="outside",
                               hovertemplate="%{x}: %{y:.0f} movimentos<extra></extra>"))
        fig.update_layout(height=300, showlegend=False, bargap=.42,
                          margin=dict(l=8, r=8, t=28, b=8),
                          yaxis=dict(title="movimentos no dia"),
                          xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)
    else:
        st.bar_chart(sem[["movimentos no dia"]], height=280)
    st.dataframe(sem.style.format(precision=1, decimal=",", thousands="."),
                 use_container_width=True)

# ================================ ABA ESCALA ================================
with a5:
    dia = seletor_data("escala")
    tipo = tipo_de_escala(dia.weekday(), str(dia) in FERIADOS)
    turnos = MANOBRISTAS[tipo]
    cob = cobertura(turnos)
    dem = curva_manobras(dia)

    st.markdown("##### A escala real da casa")
    c = st.columns(4)
    c[0].metric("Quadro", f"{sum(QUADRO.values())} pessoas",
                f"{QUADRO['manobristas']} manobristas",
                delta_color="off", delta_arrow="off")
    c[1].metric("Turnos hoje", f"{len(turnos)}")
    c[2].metric("Horas efetivas", f"{num(horas_efetivas(turnos))} h",
                f"{num(horas_de(turnos))} h de presença",
                delta_color="off", delta_arrow="off",
                help="Presença menos os intervalos: 30 min nos turnos de 6h30, "
                     "1 h nos de 9 h, e o turno da noite não tem intervalo")
    c[3].metric("Pico de cobertura", f"{int(cob.max())} pessoas",
                f"às {int(np.argmax(cob))}h" if TEM_PLOTLY else None,
                delta_color="off", delta_arrow="off")

    if tipo == "domingo":
        st.markdown('<div class="ressalva"><b>Domingo não tem escala fixa.</b> São dois '
                    'turnos de 8 horas (6h–14h e 14h–22h) pagos por fora, e os '
                    'manobristas decidem entre si quem vem. É o único dia em que o '
                    'custo de operação é variável.</div>', unsafe_allow_html=True)

    def _linhas(lista):
        return [{"quem": n, "entra": formata(a), "sai": formata(b),
                 "presença": round(b - a, 1),
                 "almoço": ALMOCO.get(n, 0.0),
                 "trabalho": round(b - a - ALMOCO.get(n, 0.0), 1)} for n, a, b in lista]
    tab = pd.DataFrame(_linhas(turnos) + _linhas(APOIO.get(tipo, [])))
    st.dataframe(tab.set_index("quem").style.format(precision=1, decimal=",",
                                                    thousands="."),
                 use_container_width=True)
    st.caption("O manobrista da noite é o único sem intervalo — o movimento entre "
               "22h e 6h é quase nulo. As jornadas fecham em 36 h/semana para os "
               "turnos de 6 h e 44 h para os de 8 h.")

    st.markdown("##### Quem está no prédio a cada hora")
    st.caption("Só a escala, sem interpretação: quantas pessoas estão presentes, e "
               "quantas estão efetivamente disponíveis depois do intervalo.")
    oti = cobertura_com_almoco(turnos, dem, "otimo")
    pio = cobertura_com_almoco(turnos, dem, "pior")
    if TEM_PLOTLY:
        fig = go.Figure()
        # ⚠ a barra da hora h precisa cobrir h→h+1, igual ao degrau da linha:
        #   centrada em h, ela ficava meia hora deslocada em relação às linhas.
        fig.add_trace(go.Bar(x=list(range(24)), y=cob, name="presentes na escala",
                             width=1, offset=0,
                             marker_color="rgba(43,127,255,.28)",
                             marker_line=dict(width=0)))
        fig.add_trace(go.Scatter(x=list(range(24)), y=oti, mode="lines",
                                 name="disponíveis · intervalo cedo ou tarde",
                                 line=dict(color=VERDE, width=2.6, shape="hv")))
        fig.add_trace(go.Scatter(x=list(range(24)), y=pio, mode="lines",
                                 name="disponíveis · intervalo no meio",
                                 line=dict(color=VERM, width=2.6, shape="hv",
                                           dash="dot")))
        fig.update_layout(height=360, bargap=0,
                          margin=dict(l=8, r=8, t=50, b=8),
                          xaxis=dict(title="hora do dia", dtick=2, ticksuffix="h",
                                     showgrid=False),
                          yaxis=dict(title="pessoas", dtick=1))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)

        dif = oti - pio
        h_crit = int(np.argmax(dif))
        st.markdown(f'<div class="achado"><b>A duração do intervalo é conhecida; o '
                    f'horário não.</b> E isso muda a cobertura: às <b>{h_crit}h</b>, '
                    f'dependendo de quando cada um sai para almoçar, a equipe '
                    f'disponível fica entre <b>{num(pio[h_crit])} e {num(oti[h_crit])} '
                    f'pessoas</b>.<br><br>A distância entre a linha verde e a vermelha '
                    f'é o que <b>uma regra de horário de intervalo resolveria</b> — e é '
                    f'a única recomendação desta aba que não exige medir nada novo.'
                    f'</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("##### ⚠️ O que esta aba deliberadamente não faz")
    st.markdown("""
**Não diz se a escala é adequada.** Para isso seria preciso saber quantos carros um
manobrista consegue movimentar por hora — e esse número **não existe**: nunca foi
cronometrado, e quem trabalha lá não consegue estimar, porque não segue padrão fixo.

Uma versão anterior deste app tinha um otimizador de turnos e uma métrica de
"manobristas necessários". **Foi removida.** Ela multiplicava dois números que ninguém
pode verificar — a curva horária, que é design do gerador, e o ritmo por pessoa, que é
desconhecido — e devolvia uma recomendação de equipe com aparência de precisão.

Era o único lugar do projeto que fazia exatamente aquilo que o resto dele critica.

**O que ficaria de pé com um dado a mais:** cronometrar algumas dezenas de manobras.
É barato, leva uma semana, e transformaria esta aba de descrição em dimensionamento.
Enquanto isso não existir, ela descreve — e para por aí.
    """)

    st.divider()
    st.markdown("##### Os papéis não são estanques")
    st.markdown("""
As operações simples de caixa — cobrança, desconto de selo, ativação de Passe Livre —
são feitas **também pelos manobristas quando necessário**. Todos sabem fazer. O papel
do caixa é **controle financeiro**: organização, fechamento diário e conferência.

Isso dá **causa estrutural** a um problema registrado nas regras de negócio: a
correção retroativa de forma de pagamento no fim do dia. Não é descuido — é o
resultado esperado de uma cobrança executada **por 7 pessoas de vez em quando** e
conferida **por 2 no fechamento**.

E é a mesma raiz do desvio da orientação do totem: o manobrista que atende uma
cobrança em hora de fila resolve no caixa em vez de orientar o cliente à máquina.
    """)


# ================================ ABA 2 ================================
with a2:
    rec, dias = M["receita"], M["dias_periodo"]
    ordem = sorted(rec.items(), key=lambda x: -x[1]["total"])
    total = sum(v["total"] for v in rec.values())
    hotel, avulso = rec.get("Hóspede Hotel", {}), rec.get("Avulso Regular", {})

    st.markdown("##### De onde vem a receita")
    c = st.columns(4)
    c[0].metric("Receita no período", f"R$ {total/1000:.0f} mil", f"{dias} dias",
                delta_color="off", delta_arrow="off")
    c[1].metric("Por dia", f"R$ {num(total/dias, 0)}")
    c[2].metric("Ticket do hotel", f"R$ {num(hotel.get('ticket', 0), 2)}")
    c[3].metric("Ticket do avulso", f"R$ {num(avulso.get('ticket', 0), 2)}",
                f"{avulso.get('ticket',1)/max(hotel.get('ticket',1),1)-1:.0%}",
                delta_color="off", delta_arrow="off")

    if TEM_PLOTLY:
        fig = go.Figure(go.Bar(
            y=[k for k, _ in ordem][::-1], x=[v["total"] for _, v in ordem][::-1],
            orientation="h", marker_color=AZUL, cliponaxis=False,
            text=[f"R$ {v['total']/1000:.0f}k" for _, v in ordem][::-1],
            textposition="outside"))
        fig.update_layout(height=340, showlegend=False, bargap=.35,
                          margin=dict(l=8, r=96, t=16, b=8),
                          xaxis=dict(title="R$ no período",
                                     range=[0, max(v["total"] for _, v in ordem) * 1.18]),
                          yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)
    else:
        st.bar_chart(pd.DataFrame({"R$": {k: v["total"] for k, v in ordem}}))

    st.markdown(f'<div class="achado"><b>O hotel entrega quase a mesma receita que o '
                f'avulso inteiro com {avulso.get("n",1)/max(hotel.get("n",1),1):.0f}× '
                f'menos transações.</b> E por regra ele paga sempre no caixa — o '
                f'segmento mais rentável por transação é o que menos se automatiza.'
                f'</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("##### Quanto custa uma estadia")
    c = st.columns([1, 2])
    veic = c[0].radio("Veículo", ["Carro", "Moto"], horizontal=True)
    horas = c[1].slider("Permanência (horas)", 0.25, 13.0, 3.0, 0.25)
    valor, explic = tarifa(horas * 60, veic)
    t = M["precos"]["carro" if veic == "Carro" else "moto"]

    c = st.columns(3)
    c[0].metric("Valor cobrado", f"R$ {num(valor, 2)}")
    c[1].metric("Por hora", f"R$ {num(valor/horas, 2)}")
    c[2].metric("Situação", "no teto" if 60 < horas * 60 <= 720
                and valor >= t["diaria_12h"] else "tarifa progressiva")
    st.caption(explic)

    grade = [i / 4 for i in range(1, 53)]
    vals = [tarifa(h * 60, veic)[0] for h in grade]
    if TEM_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=grade, y=vals, mode="lines",
                                 line=dict(color=AZUL, width=3.5)))
        fig.add_trace(go.Scatter(x=[horas], y=[valor], mode="markers",
                                 marker=dict(color=VERDE, size=14)))
        fig.update_layout(height=300, showlegend=False,
                          margin=dict(l=8, r=8, t=16, b=8),
                          xaxis=dict(title="permanência (horas)", ticksuffix="h"),
                          yaxis=dict(title="valor (R$)"))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)
    else:
        st.line_chart(pd.DataFrame({"valor (R$)": vals}, index=grade), height=280)

    if veic == "Carro":
        st.markdown(f'<div class="achado"><b>O patamar não é bug.</b> A tabela não tem '
                    f'faixa de 4, 5 ou 6 horas: são R$ {t["hora_adicional"]:.0f} por '
                    f'hora adicional, limitados a R$ {t["diaria_12h"]:.0f} para '
                    f'qualquer permanência de até 12 horas. O teto é atingido na 3ª '
                    f'hora — <b>da 3ª à 12ª o cliente ocupa a vaga sem custo '
                    f'adicional.</b></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("##### Convênio de selos — e se o preço mudasse?")
    c = st.columns([1, 1, 2])
    n = c[0].select_slider("Selos apresentados", [1, 2, 3], value=1)
    preco = c[1].number_input("Preço do selo (R$)", 5.0, 20.0,
                              float(M["selo"]["preco_venda"]), 0.5)
    margem = n * preco - min(n * t["uma_hora"], valor)
    c[2].metric("Margem nesta estadia", f"R$ {num(margem, 2, sinal=True)}",
                delta_color="normal" if margem >= 0 else "inverse")

    faixas = [.5, 1, 2, 3, 4, 6, 10]
    tc = M["precos"]["carro"]
    dados = {f"{k} selo(s)": [k * preco - min(k * tc["uma_hora"], tarifa(h * 60, "Carro")[0])
                              for h in faixas] for k in (1, 2, 3)}
    piv = pd.DataFrame(dados, index=[f"{h:g}h" for h in faixas])
    if TEM_PLOTLY:
        fig = go.Figure()
        for col, cor in zip(piv.columns, ["#1f5ed0", AZUL_CLARO, ROXO]):
            fig.add_trace(go.Bar(x=piv.index, y=piv[col], name=col, marker_color=cor))
        fig.add_hline(y=0, line=dict(color="#5b6a80", width=1.2))
        fig.update_layout(height=320, barmode="group", bargap=.34,
                          margin=dict(l=8, r=8, t=44, b=8),
                          yaxis=dict(title="margem (R$)"),
                          xaxis=dict(title="permanência", showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)
    else:
        st.bar_chart(piv, height=300)

    if preco < tc["uma_hora"]:
        st.markdown(f'<div class="alerta">A R$ {num(preco, 2)}, o selo é vendido <b>abaixo '
                    f'dos R$ {tc["uma_hora"]:.0f} que ele desconta</b>. Um selo isolado '
                    f'dá prejuízo em qualquer conta acima de R$ {preco:.0f} — e o mínimo '
                    f'da tabela é R$ {tc["meia_hora"]:.0f}. A margem só fica positiva '
                    f'quando o desconto <b>transborda</b> a conta, o que acontece com 2 '
                    f'ou 3 selos em estadias curtas.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="certo">A R$ {num(preco, 2)} o selo cobre o que desconta. '
                    f'<b>Nenhuma faixa fica negativa</b> — o programa deixa de ser '
                    f'subsidiado pelo estacionamento.</div>', unsafe_allow_html=True)

# ================================ ABA 3 ================================
with a3:
    dia = seletor_data("capacidade")
    occ, occ_m = curva_ocupacao(dia), curva_ocupacao(dia, "moto")
    st.markdown("##### Vaga vendida não é vaga ocupada")
    c = st.columns(4)
    c[0].metric("Carro · capacidade", f"{CAP}")
    c[1].metric("Carro · contratadas", f"{CONTRATADAS}",
                f"{CONTRATADAS/CAP*100:.0f}% vendido",
                delta_color="off", delta_arrow="off")
    c[2].metric("Carro · ocupação média", f"{sum(occ)/24:.0f}",
                f"{sum(occ)/24/CONTRATADAS*100:.0f}% do contratado",
                delta_color="off", delta_arrow="off")
    c[3].metric("Moto · ocupação média", f"{sum(occ_m)/24:.0f}",
                f"{sum(occ_m)/24/CAP_MOTO*100:.0f}% das {CAP_MOTO} vagas",
                delta_color="off", delta_arrow="off")

    linhas([dict(nome="carro", y=occ, cor=AZUL, fill="tozeroy",
                 fillcolor="rgba(43,127,255,.16)"),
            dict(nome="moto", y=occ_m, cor=ROXO, w=2.6)],
           "veículos no prédio", altura=340)

    st.markdown(f'<div class="achado"><b>{CAP-CONTRATADAS} das {CAP} vagas de carro não '
                f'têm contrato nenhum.</b> A ociosidade física aparece no gráfico; a '
                f'comercial é uma ordem de grandeza maior — e nenhuma das duas é medida '
                f'pelo sistema, que não sabe quantas vagas estão ocupadas.</div>',
                unsafe_allow_html=True)

    st.divider()
    st.markdown("##### Tomadas de recarga — quantas o crescimento exige")
    st.caption(f"Modelo de filas sobre a duração real medida no app do carregador "
               f"({num(EV['duracao_h'], 2)} h por sessão).")

    c = st.columns([2, 1])
    taxa = c[0].slider("Recargas por dia", 1.0, 20.0,
                       float(EV["recargas_dia_atual"]), .5)
    n_tom = c[1].number_input("Tomadas instaladas", 1, 8,
                              EV["tomadas"] + EV["em_obra"])
    bloq = erlang_b(taxa, int(n_tom))

    c = st.columns(4)
    c[0].metric("Chance de não achar tomada", f"{num(bloq)}%")
    c[1].metric("Manobras extras/dia", f"{taxa:.0f}",
                help="Cada recarga gera uma manobra a mais: tirar da tomada e guardar "
                     "em outra vaga")
    c[2].metric("Energia vendida", f"{taxa*EV['kwh_sessao']:.0f} kWh/dia")
    c[3].metric("Receita de recarga", f"R$ {taxa*EV['kwh_sessao']*EV['tarifa']:.0f}/dia")

    if TEM_PLOTLY:
        xs = [i / 2 for i in range(2, 41)]
        fig = go.Figure()
        for nn, cor, dash in [(2, "#5b6a80", "dot"), (3, AZUL, None),
                              (4, AZUL_CLARO, "dash"), (6, ROXO, "dot")]:
            fig.add_trace(go.Scatter(x=xs, y=[erlang_b(x, nn) for x in xs],
                                     mode="lines", name=f"{nn} tomadas",
                                     line=dict(color=cor, width=2.6, dash=dash)))
        fig.add_hline(y=5, line=dict(color=AMBAR, dash="dash", width=1.4),
                      annotation_text="limite de 5%", annotation_position="top left",
                      annotation_font=dict(color=AMBAR, size=11))
        fig.add_vline(x=taxa, line=dict(color="#5b6a80", width=1.2))
        fig.update_layout(height=340,
                          margin=dict(l=8, r=8, t=44, b=8),
                          xaxis=dict(title="recargas por dia"),
                          yaxis=dict(title="chance de bloqueio (%)"))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONF)

    if bloq > 5:
        st.markdown(f'<div class="alerta">Com {int(n_tom)} tomadas e {num(taxa)} recargas '
                    f'por dia, <b>{bloq:.0f}% dos motoristas chegam e não acham vaga de '
                    f'recarga</b>. A demanda cresceu 8× em 11 meses — e o achado não '
                    f'óbvio é que <b>potência rende mais que número de vagas</b>: '
                    f'trocar por tomadas trifásicas triplica a capacidade sem abrir vaga '
                    f'nova.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="certo">Com {int(n_tom)} tomadas, {num(taxa)} recargas '
                    f'por dia ficam confortáveis ({num(bloq)}% de bloqueio). Mas a '
                    f'demanda cresceu 8× em 11 meses — vale acompanhar onde a curva '
                    f'cruza os 5%.</div>', unsafe_allow_html=True)

    with st.expander("A validação contra o mundo real"):
        st.markdown("A recarga elétrica é a **única parte do dado que dá para conferir "
                    "contra a realidade** — o carregador tem app próprio, fora do "
                    "sistema do estacionamento. Foram lidos 12 meses de lá; abaixo, os "
                    "sete que se sobrepõem ao período do dataset:")
        st.dataframe(pd.DataFrame({"recargas/dia (real)": EV["serie_real"]}).T
                     .style.format(precision=2, decimal=",", thousands="."),
                     use_container_width=True)
        st.caption("Contra o simulado: volume 1,01× e energia 0,99×. "
                   "O resto do dataset não tem contra o que ser conferido.")

# ================================ ABA 4 ================================
with a4:
    st.markdown("##### O que estes números não são")
    st.markdown(f"""
**A ocupação não é medida.** O sistema **não sabe quantas vagas estão ocupadas** — a
alocação é manual, com cartão físico entregue ao cliente. A ocupação é *reconstruída*
somando entradas e saídas, e só é válida depois de excluir as tentativas barradas na
cancela, que o log registra como "entrada" sem que o veículo tenha entrado.

**A previsão não foi validada contra a operação real.** O modelo foi treinado e testado
sobre um **dataset sintético**, gerado a partir de 39 seções de regras de operação
mapeadas com quem trabalha lá. O que este painel demonstra é o **método**.

**A única parte conferida contra o mundo** é a recarga elétrica, comparada com 12 meses
do app do carregador: volume 1,01× e energia 0,99×.

**O erro tem contexto.** {num(M['meta']['mae_diario'], 2)} carros parecem pouco porque a
amplitude semanal é de ~22 e a garagem opera a 18% da capacidade. Num cenário de
ocupação alta, o problema seria outro.

**Vale para o regime atual.** A partir de {data_br(M['meta']['marco'])} a operação mudou em três
frentes ao mesmo tempo — tabela unificada, entrada do ERP e saída do maior cliente.
Prever com dados anteriores seria treinar num mundo que deixou de existir.

**⚠ O número de manobristas é simulação, não previsão.** Vale detalhar, porque é o
único lugar do painel onde um número aparece sem ter sido medido:

| Peça | De onde vem | Confiável? |
|---|---|---|
| "cada movimento de carro é uma manobra com elevador" | regras 15 e 23, do informante | ✅ |
| "moto não conta" (o cliente estaciona sozinho) | regra 23 | ✅ |
| "o pico de manobra vem antes do de ocupação" | estoque × fluxo, verdadeiro por construção | ✅ |
| "sábado tem mais manobras por hora" | mesmo volume em janela menor — direção garantida | ✅ |
| **a forma horária da curva** | **do dado sintético**, cujas janelas de chegada são constantes do gerador | ❌ |
| **"31 manobras por hora no pico"** | **idem** | ❌ |
| **"8 manobras por hora por manobrista"** | **chute meu — nunca foi cronometrado** | ❌ |
| **"4 manobristas no pico"** | os dois acima, divididos | ❌ |

Por isso os dois últimos números **saíram do painel**. Uma versão anterior tinha um
controle de ritmo por manobrista e uma métrica de equipe necessária: ela multiplicava
dois números que ninguém pode verificar e devolvia uma recomendação de equipe com
aparência de precisão. A aba *Escala* passou a descrever a escala real e parar aí.
**Cronometrar algumas dezenas de manobras** resolveria — é o dado que falta para essa
parte sair da simulação e virar dimensionamento de verdade.
    """)

    st.divider()
    st.markdown("##### Por que um baseline, e não um modelo complexo")
    st.dataframe(pd.DataFrame({
        "Modelo": ["Gradient Boosting", "Baseline sazonal + degrau", "Persistência 7 dias",
                   "Baseline sazonal", "Média global"],
        "MAE (carros)": [2.23, 2.71, 3.25, 3.27, 7.27],
        "Precisa de treino": ["sim", "não", "não", "não", "não"],
    }).set_index("Modelo").style.format(precision=2, decimal=",", thousands="."),
        use_container_width=True)
    st.markdown("""
A diferença entre o Gradient Boosting e o baseline usado aqui **não é estatisticamente
significativa** (Wilcoxon, p = 0,150) num teste de 46 dias. E mais da metade da vantagem
dele vinha de ter aprendido o degrau de junho — que aqui é declarado em uma linha.

⚠️ **A escolha tem prazo de validade:** o baseline com degrau depende de alguém saber
que existe um degrau e onde ele está. Numa quebra **não documentada**, as árvores
achariam sozinhas e o baseline não.
    """)

    st.divider()
    c = st.columns(4)
    c[0].metric("Regras mapeadas", "39 seções")
    c[1].metric("Asserções no gerador", "25/25")
    c[2].metric("Validação externa", "1,01×")
    # medido no arquivo, para não envelhecer: estava escrito 12 KB e o
    # modelo.json já tinha crescido.
    c[3].metric("Tamanho do modelo",
                f"{(BASE / 'modelo.json').stat().st_size / 1024:.0f} KB",
                help="O app não carrega o dataset de 15 MB — só as tabelas do modelo")

st.markdown('<div class="rodape">@fabiods.tech · projeto completo · '
            'da regra de negócio ao painel</div>', unsafe_allow_html=True)
