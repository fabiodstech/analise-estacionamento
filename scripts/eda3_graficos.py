"""Os 8 gráficos da Etapa 3, sobre o v13."""
import math
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from params import carregar
from eda3_negocio import carregar_dados, estadias, ocupacao, tarifa, MARCO, P

OUT = Path("/mnt/user-data/outputs/graficos_etapa3")
OUT.mkdir(parents=True, exist_ok=True)

BG, FG, GRID = "#0b1220", "#e8eef7", "#1e2a3d"
AZUL, CINZA, VERDE, VERM, AMBAR = "#2b7fff", "#3d4a5e", "#3ddc84", "#ff6b63", "#e5a83a"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "axes.labelcolor": "#9aa6b6", "xtick.color": "#c3ccd9",
    "ytick.color": "#7e8b9c", "axes.edgecolor": GRID, "grid.color": GRID,
    "axes.grid": True, "grid.alpha": .35, "figure.dpi": 190, "font.size": 11,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False,
    "text.usetex": False, "mathtext.default": "regular", "axes.formatter.use_mathtext": False,
})


def salvar(fig, nome):
    fig.tight_layout()
    fig.savefig(OUT / f"{nome}.png", bbox_inches="tight")
    plt.close(fig)
    print("->", nome)


df = carregar_dados()
est = estadias(df)
DIAS = df.data.nunique()

# ---------- 1. onde está o dinheiro ----------
pagas = est[est.valor > 0]
t = (pagas.groupby("subcat").valor.agg(n="size", ticket="mean", total="sum")
     .sort_values("ticket"))
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
ax[0].barh(t.index, t.ticket, color=[CINZA, CINZA, CINZA, AZUL][:len(t)])
for i, v in enumerate(t.ticket):
    ax[0].text(v * 1.02, i, f"R$ {v:.2f}", va="center", color=FG, fontsize=10)
ax[0].set_xlim(0, t.ticket.max() * 1.28)
ax[0].set_title("Ticket médio por transação")
ax[1].barh(t.index, t.n, color=[CINZA, CINZA, CINZA, AZUL][:len(t)])
for i, v in enumerate(t.n):
    ax[1].text(v * 1.02, i, f"{int(v):,}".replace(",", "."), va="center", color=FG, fontsize=10)
ax[1].set_xlim(0, t.n.max() * 1.28)
ax[1].set_title("Nº de transações")
ax[1].set_yticklabels([])
fig.suptitle("Onde está o dinheiro: ticket alto, volume baixo", y=1.02,
             fontsize=15, fontweight="bold", color=FG)
salvar(fig, "01_onde_esta_o_dinheiro")

# ---------- 2. margem do selo ----------
carro = P["precos.nova.carro"]
fig, ax = plt.subplots(figsize=(9.2, 4.4))
hs = [0.5, 1, 2, 3, 4, 6, 10]
x = np.arange(len(hs))
w = .26
for i, (n, cor) in enumerate(zip([1, 2, 3], [VERM, AMBAR, VERDE])):
    m = []
    for h in hs:
        cheio = tarifa(h, "Carro", pd.Timestamp("2026-07-01"), regime="nova")
        m.append(9 * n - min(15 * n, cheio))
    b = ax.bar(x + (i - 1) * w, m, w, color=cor, label=f"{n} selo{'s' if n > 1 else ''}")
    for xx, v in zip(x + (i - 1) * w, m):
        ax.text(xx, v + (.5 if v >= 0 else -1.6), f"{v:+.0f}", ha="center",
                color=FG, fontsize=8.5)
ax.axhline(0, color=FG, lw=1)
ax.set_xticks(x, [f"{h:g}h" for h in hs])
ax.set_ylabel("margem por estadia (R$)")
ax.set_title("O selo é vendido por 9 reais e desconta 15 — e a margem inverte com a quantidade")
ax.legend(ncol=3, fontsize=9)
salvar(fig, "02_margem_do_selo")

# ---------- 3. vaga vendida x ocupada ----------
occ = ocupacao(df, "Carro")
cap = P["capacidade.carro.vagas"]
contratadas = df[(df.Categoria_Principal == "Mensalista")
                 & (df.Tipo_Veiculo == "Carro")].Veiculo_ID.nunique()
fig, ax = plt.subplots(figsize=(10, 4.4))
h = occ.groupby(occ.index.hour).mean()
ax.fill_between(h.index, h.values, color=AZUL, alpha=.22)
ax.plot(h.index, h.values, color=AZUL, lw=2.4, label="ocupação física")
ax.axhline(contratadas, color=AMBAR, ls="--", lw=1.8, label=f"vagas contratadas ({contratadas})")
ax.set_ylim(0, contratadas * 1.35)
ax.text(23.4, contratadas * 1.22,
        f"capacidade total: {cap} vagas\n(fora da escala — a garagem opera a {occ.mean()/cap*100:.0f}% dela)",
        ha="right", va="center", color=VERM, fontsize=9.5)
ax.annotate("", xy=(23.4, contratadas*1.32), xytext=(23.4, contratadas*1.27),
            arrowprops=dict(arrowstyle="-|>", color=VERM, lw=1.4))
ax.set_xticks(range(0, 24, 2))
ax.set_xlabel("hora do dia")
ax.set_ylabel("carros no prédio")
ax.set_title(f"A garagem opera a {occ.mean()/contratadas*100:.0f}% do que já está vendido")
ax.legend(fontsize=9.5)
salvar(fig, "03_vaga_vendida_vs_ocupada")

# ---------- 4. o sábado ----------
JAN = {"dia_util": (8, 17.5), "sabado": (8, 15.5)}
car = df[(df.Sentido.isin(["Entrada", "Saída"])) & (df.Status != "Bloqueado")
         & (df.Tipo_Veiculo == "Carro")]
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
rot, tot, ph = [], [], []
for k, lab in [("dia_util", "Dia útil"), ("sabado", "Sábado")]:
    s = car[car.td == k]
    nd = s.data.nunique()
    ini, fim = JAN[k]
    rot.append(f"{lab}\n({fim-ini:g}h de comércio)")
    tot.append(len(s) / nd)
    ph.append(len(s[(s.hora >= ini) & (s.hora < fim)]) / nd / (fim - ini))
ax[0].bar(rot, tot, color=[CINZA, AZUL], width=.55)
for i, v in enumerate(tot):
    ax[0].text(i, v + 5, f"{v:.0f}", ha="center", color=FG, fontweight="bold")
ax[0].set_title("Manobras por dia  ·  +2%")
ax[1].bar(rot, ph, color=[CINZA, AZUL], width=.55)
for i, v in enumerate(ph):
    ax[1].text(i, v + .5, f"{v:.1f}", ha="center", color=FG, fontweight="bold")
ax[1].set_title(f"Manobras por hora de comércio  ·  +{(ph[1]/ph[0]-1)*100:.0f}%")
fig.suptitle("O sábado move quase o mesmo — numa janela 2 horas mais curta",
             y=1.02, fontsize=15, fontweight="bold", color=FG)
salvar(fig, "04_o_sabado")

# ---------- 4b. o prêmio de preço do sábado ----------
av = est[(est.subcat == "Avulso Regular") & (est.valor > 0)].copy()
av["regime"] = np.where(av.data < MARCO, "Tabela antiga", "Tabela unificada")
p4 = av[av.td.isin(["dia_util", "sabado"])].pivot_table(
    index="regime", columns="td", values="valor", aggfunc="mean")
fig, ax = plt.subplots(figsize=(8.6, 4.2))
x = np.arange(2)
w = .32
ax.bar(x - w / 2, p4["dia_util"], w, color=CINZA, label="dia útil")
ax.bar(x + w / 2, p4["sabado"], w, color=AZUL, label="sábado")
for i in range(2):
    ax.text(i - w / 2, p4["dia_util"].iloc[i] + .3, f"{p4['dia_util'].iloc[i]:.2f}",
            ha="center", color=FG, fontsize=10)
    ax.text(i + w / 2, p4["sabado"].iloc[i] + .3, f"{p4['sabado'].iloc[i]:.2f}",
            ha="center", color=FG, fontsize=10)
    d = p4["sabado"].iloc[i] / p4["dia_util"].iloc[i] - 1
    ax.text(i, max(p4.iloc[i]) + 2.2, f"{d:+.0%}", ha="center",
            color=VERDE if d > .1 else VERM, fontweight="bold", fontsize=12)
ax.set_xticks(x, p4.index)
ax.set_ylabel("ticket médio do avulso (R$)")
ax.set_ylim(0, max(p4.max()) * 1.28)
ax.set_title("O sábado era o dia cheio E caro. Virou só o dia cheio.")
ax.legend(fontsize=9.5)
salvar(fig, "05_premio_do_sabado")

# ---------- 5. EV contra o real ----------
REAL = {"2026-02": 1.11, "2026-03": 1.23, "2026-04": 2.00, "2026-05": 1.84,
        "2026-06": 2.60, "2026-07": 2.65, "2026-08": 4.80}
ev = df[df.KWh_Consumido > 0]
mm = ev.groupby(ev.dt.dt.to_period("M")).size()
nd = df.groupby(df.dt.dt.to_period("M")).data.nunique()
lab = list(REAL)
sint = [mm.get(pd.Period(k), 0) / nd[pd.Period(k)] for k in lab]
fig, ax = plt.subplots(figsize=(9.6, 4.2))
ax.plot(lab, list(REAL.values()), color=VERDE, lw=2.8, marker="o", ms=7,
        label="real (app de recarga)")
ax.plot(lab, sint, color=AZUL, lw=2.8, ls="--", marker="s", ms=6, label="simulado (v13)")
ax.set_ylabel("recargas por dia")
esperado = sum(REAL[k] * nd[pd.Period(k)] for k in REAL)
ax.set_title(f"Volume {len(ev)/esperado:.2f}× o real  ·  "
             f"energia {ev.KWh_Consumido.mean()/10.71:.2f}×")
ax.legend(fontsize=9.5)
salvar(fig, "06_ev_real_vs_v13")

# ---------- 6. tomadas ----------
def erlang_b(a, n):
    b = 1.0
    for i in range(1, n + 1):
        b = a * b / (i + a * b)
    return b

dur = P["recarga_ev.duracao_h_media"]
ago = len(ev[ev.dt.dt.month == 8]) / df[df.dt.dt.month == 8].data.nunique()
taxas = np.linspace(1, 16, 60)
fig, ax = plt.subplots(figsize=(9.6, 4.4))
for n, cor, ls in [(2, VERM, "-"), (3, AZUL, "-"), (4, VERDE, "--"), (6, CINZA, ":")]:
    ax.plot(taxas, [erlang_b(x * dur / 12, n) * 100 for x in taxas],
            color=cor, lw=2.4, ls=ls, label=f"{n} tomadas")
ax.axhline(5, color=AMBAR, ls="--", lw=1.4)
ax.text(15.6, 6.2, "limite de 5%", color=AMBAR, fontsize=9, ha="right")
ax.axvline(ago, color="#8492a4", lw=1.2)
ax.text(ago + .25, 46, f"ago/2026\n{ago:.1f}/dia", color="#c3ccd9", fontsize=9)
ax.set_xlabel("recargas por dia")
ax.set_ylabel("chance de não achar tomada livre (%)")
ax.set_title("A 3ª tomada satura em ~5 recargas/dia — que é o volume de agosto")
ax.legend(fontsize=9.5)
salvar(fig, "07_dimensionamento_tomadas")

# ---------- 7. o teto da 3ª hora ----------
a = est[est.subcat == "Avulso Regular"]
fig, ax = plt.subplots(figsize=(10, 4.6))
hh = np.arange(.25, 9, .25)
ax.plot(hh, [tarifa(h, "Carro", pd.Timestamp("2026-07-01"), regime="nova") for h in hh],
        color=AZUL, lw=3, label="o que o cliente paga")
ax2 = ax.twinx()
ax2.hist(a.horas, bins=36, color="#7e8b9c", alpha=.30)
ax2.set_ylabel("estadias de avulso", color="#7e8b9c")
ax2.grid(False)
ax.axvline(3, color=VERM, ls="--", lw=1.8)
ax.text(3.15, 12, "a partir daqui,\ncada hora é grátis", color=VERM, fontsize=10.5,
        fontweight="bold")
ax.set_xlabel("permanência (horas)")
ax.set_ylabel("valor cobrado (R$)", color=AZUL)
ax.set_ylim(0, 36)
ax.set_zorder(ax2.get_zorder() + 1)
ax.patch.set_visible(False)
ax.set_title(f"{(a.horas>3).mean()*100:.0f}% das estadias passam das 3 horas — "
             "e param de gerar receita")
salvar(fig, "08_teto_da_terceira_hora")

# ---------- 8. inadimplência ----------
ina = est[est.subcat == "Mensalista Inadimplente"]
bo = df[df.Sentido == "Renovação Mensal"]
fig, ax = plt.subplots(figsize=(8.8, 4.2))
vals = [bo.Valor_Cobrado_Total.mean(), ina.valor.sum() / max(ina.subcat.size, 1)]
ax.bar(["Mensalidade\nque deixou de entrar", "Ticket que o bloqueado\npaga na saída"],
       [vals[0], vals[1]], color=[CINZA, VERDE], width=.5)
for i, v in enumerate(vals):
    ax.text(i, v + 8, f"R$ {v:.2f}", ha="center", color=FG, fontweight="bold", fontsize=12)
ax.set_ylim(0, vals[0] * 1.22)
ax.text(0.5, vals[0]*1.08, f"o bloqueado devolve {vals[1]/vals[0]*100:.0f}% do que deixou de pagar —\ne isso entra como receita nova", ha="center", color="#9aa6b6", fontsize=10)
ax.set_ylabel("R$")
ax.set_title("A inadimplência entra no caixa como receita, não como perda")
salvar(fig, "09_inadimplencia_como_receita")

print("\nOK")
