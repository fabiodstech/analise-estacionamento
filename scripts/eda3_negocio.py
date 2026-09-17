"""Etapa 3 — EDA de negócio sobre o v13.

Oito perguntas, escolhidas antes de abrir o notebook (ver etapa3_perguntas.md).
Cada uma passou pelo filtro da auditoria de origem: a resposta não pode ser um
parâmetro que o próprio gerador escreveu.
"""
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from params import carregar

P = carregar()
FERIADOS = P.feriados()
MARCO = P.data("marco_modernizacao.data")
CSV = "logs_estacionamento_v13.csv"


def tipo_de_dia(d):
    if d in FERIADOS:
        return "feriado"
    return {5: "sabado", 6: "domingo"}.get(pd.Timestamp(d).weekday(), "dia_util")


def carregar_dados():
    # keep_default_na=False: sem isso o pandas vira "N/A" em NaN e todas as
    # credenciais de avulso colapsam numa chave de pareamento só.
    df = pd.read_csv(CSV, keep_default_na=False)
    df["dt"] = pd.to_datetime(df.Data + " " + df.Hora, format="%d/%m/%Y %H:%M:%S")
    df["data"] = df.dt.dt.date
    df["hora"] = df.dt.dt.hour
    df["td"] = df.data.map(tipo_de_dia)
    for c in ["KWh_Consumido", "Valor_Recarga_EV", "Valor_Cobrado_Total", "Selos_Apresentados"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # janela plena: os últimos dias só têm saídas de estadias longas
    g = df.groupby("data").size()
    return df[~df.data.isin(g[g < 50].index)].copy()


def estadias(df):
    """Pareamento entrada->saída. Exclui tentativas bloqueadas: o veículo não entrou."""
    mov = df[(df.Sentido.isin(["Entrada", "Saída"])) & (df.Status != "Bloqueado")].copy()
    mov["chave"] = np.where(mov.Veiculo_ID.ne("N/A"),
                            "V:" + mov.Veiculo_ID, "T:" + mov.Credencial)
    pares = []
    for chave, g in mov.groupby("chave", sort=False):
        g = g.sort_values("dt")
        pilha = []
        for r in g.itertuples():
            if r.Sentido == "Entrada":
                pilha.append(r)
            elif pilha:
                e = pilha.pop(0)
                pares.append(dict(subcat=e.Subcategoria, veic=e.Tipo_Veiculo,
                                  entrada=e.dt, saida=r.dt, valor=r.Valor_Cobrado_Total,
                                  selos=r.Selos_Apresentados, local=r.Local_Pagamento,
                                  data=e.data, td=e.td))
    est = pd.DataFrame(pares)
    est["horas"] = (est.saida - est.entrada).dt.total_seconds() / 3600
    return est


def ocupacao(df, tipo_veiculo, freq="h"):
    mov = df[(df.Sentido.isin(["Entrada", "Saída"])) & (df.Status != "Bloqueado")
             & (df.Tipo_Veiculo == tipo_veiculo)].sort_values("dt")
    serie = pd.Series(np.cumsum(np.where(mov.Sentido == "Entrada", 1, -1)),
                      index=mov.dt.values).groupby(level=0).last()
    grade = pd.date_range(df.dt.min().floor("h"), df.dt.max().ceil("h"), freq=freq)
    return serie.reindex(serie.index.union(grade)).ffill().reindex(grade).fillna(0)


def tarifa(horas, tipo_veiculo, dt_saida, regime=None):
    reg = regime or ("nova" if dt_saida.date() >= MARCO else "antiga")
    v = "carro" if tipo_veiculo == "Carro" else "moto"
    if reg == "nova":
        t = P[f"precos.nova.{v}"]
    else:
        fds = dt_saida.weekday() >= 5 or dt_saida.date() in FERIADOS
        t = P[f"precos.antiga.{v}_{'fds' if fds else 'seg_sex'}"]
    m = horas * 60
    if m <= 30:
        return float(t["meia_hora"])
    if m <= 60:
        return float(t["uma_hora"])
    if m <= 720:
        return float(min(t["uma_hora"] + math.ceil((m - 60) / 60) * t["hora_adicional"],
                         t["diaria_12h"]))
    return float(math.ceil(m / 1440) * t["diaria_24h"])


# ============================================================================
if __name__ == "__main__":
    df = carregar_dados()
    est = estadias(df)
    DIAS = df.data.nunique()
    print(f"v13 · {len(df):,} registros · {DIAS} dias plenos · {len(est):,} estadias\n")

    # ---- 1. Onde está o dinheiro ----
    print("=" * 76)
    print("1. ONDE ESTÁ O DINHEIRO — ticket médio por segmento")
    pagas = est[est.valor > 0]
    t = pagas.groupby("subcat").valor.agg(transacoes="size", ticket="mean", total="sum")
    t = t.sort_values("ticket", ascending=False).round(2)
    t["por_dia"] = (t.transacoes / DIAS).round(1)
    print(t.to_string())
    bo = df[df.Sentido == "Renovação Mensal"]
    print(f"\nmensalidade (boleto): {len(bo)} · ticket R$ {bo.Valor_Cobrado_Total.mean():.2f}")
    h = t.loc["Hóspede Hotel"] if "Hóspede Hotel" in t.index else None
    a = t.loc["Avulso Regular"]
    if h is not None:
        print(f"\n>> hotel entrega {h.total/a.total:.2f}x a receita do avulso "
              f"com {a.transacoes/h.transacoes:.1f}x MENOS transações")

    # ---- 2. O selo ----
    print("\n" + "=" * 76)
    print("2. O CONVÊNIO DE SELOS — margem por quantidade apresentada")
    sel = est[est.selos > 0].copy()
    sel["regime"] = np.where(sel.data < MARCO, "antiga", "nova")
    sel["cheio"] = [tarifa(r.horas, r.veic, r.saida) for r in sel.itertuples()]
    sel["abono"] = (sel.cheio - sel.valor).round(2)
    sel["venda"] = sel.selos * np.where(sel.regime == "antiga",
                                        P["selo.preco_venda_antes"], P["selo.preco_venda_apos"])
    g = sel.groupby(["regime", "selos"]).agg(n=("valor", "size"), abono=("abono", "mean"),
                                             venda=("venda", "mean")).round(2)
    g["margem"] = (g.venda - g.abono).round(2)
    print(g.to_string())
    tot = sel.venda.sum() - sel.abono.sum()
    print(f"\n>> {int(sel.selos.sum())} selos · vendidos R$ {sel.venda.sum():,.0f} · "
          f"abono real R$ {sel.abono.sum():,.0f} · margem R$ {tot:,.0f}")

    # ---- 3. Vaga vendida x vaga ocupada ----
    print("\n" + "=" * 76)
    print("3. VAGA VENDIDA NÃO É VAGA OCUPADA")
    occ = ocupacao(df, "Carro")
    cap = P["capacidade.carro.vagas"]
    men = df[(df.Categoria_Principal == "Mensalista") & (df.Tipo_Veiculo == "Carro")]
    contratadas = men.Veiculo_ID.nunique()
    print(f"capacidade total      : {cap}")
    print(f"vagas contratadas     : {contratadas}  ({contratadas/cap*100:.0f}% do total)")
    print(f"ocupação física média : {occ.mean():.0f}  ({occ.mean()/cap*100:.0f}% do total, "
          f"{occ.mean()/contratadas*100:.0f}% do contratado)")
    print(f"pico                  : {occ.max():.0f}  · piso noturno (3h): "
          f"{occ[occ.index.hour == 3].mean():.0f}")

    # ---- 4. O sábado ----
    print("\n" + "=" * 76)
    print("4. O SÁBADO É MAIS PESADO DO QUE O VOLUME SUGERE")
    JANELA = {"dia_util": (8, 17.5), "sabado": (8, 15.5), "feriado": (8, 15)}
    carro = df[(df.Sentido.isin(["Entrada", "Saída"])) & (df.Status != "Bloqueado")
               & (df.Tipo_Veiculo == "Carro")]
    print(f"{'':10} {'manobras/dia':>13} {'janela':>8} {'na janela':>10} {'por hora':>9}")
    for tdia in ["dia_util", "sabado"]:
        s = carro[carro.td == tdia]
        nd = s.data.nunique()
        ini, fim = JANELA[tdia]
        dentro = len(s[(s.hora >= ini) & (s.hora < fim)]) / nd
        print(f"{tdia:10} {len(s)/nd:13.0f} {fim-ini:7.1f}h {dentro:10.0f} {dentro/(fim-ini):9.1f}")
    av = est[(est.subcat == "Avulso Regular") & (est.valor > 0)].copy()
    av["regime"] = np.where(av.data < MARCO, "antiga", "nova")
    print("\nticket médio do avulso:")
    print(av.pivot_table(index="regime", columns="td", values="valor", aggfunc="mean")
            .round(2).to_string())

    # ---- 5. EV contra o real ----
    print("\n" + "=" * 76)
    print("5. A RECARGA ELÉTRICA CONTRA O APP REAL")
    REAL = {"2026-02": 1.11, "2026-03": 1.23, "2026-04": 2.00, "2026-05": 1.84,
            "2026-06": 2.60, "2026-07": 2.65, "2026-08": 4.80}
    ev = df[df.KWh_Consumido > 0]
    mm = ev.groupby(ev.dt.dt.to_period("M")).size()
    nd = df.groupby(df.dt.dt.to_period("M")).data.nunique()
    for k, v in REAL.items():
        per = pd.Period(k)
        s = mm.get(per, 0) / nd[per]
        print(f"  {k}  sintético {s:5.2f}  real {v:5.2f}  {s/v:.2f}x")
    # ⚠ o resumo correto pondera pelos DIAS COBERTOS de cada mês. Dividir o total
    #   por 180 e comparar com a média simples das taxas mensais dá outro número:
    #   a janela cobre fevereiro pela metade e agosto por um terço.
    esperado = sum(REAL[k] * nd[pd.Period(k)] for k in REAL)
    print(f"\n>> {len(ev)} sessões contra {esperado:.0f} esperadas pela série real "
          f"= {len(ev)/esperado:.2f}x")
    print(f">> kWh/sessão: {ev.KWh_Consumido.mean():.2f} contra "
          f"{P['recarga_ev.kwh_por_sessao_medio']} medidos")

    # ---- 6. Tomadas ----
    print("\n" + "=" * 76)
    print("6. QUANTAS TOMADAS O CRESCIMENTO EXIGE (Erlang B)")
    def erlang_b(a, n):
        b = 1.0
        for i in range(1, n + 1):
            b = a * b / (i + a * b)
        return b
    dur = P["recarga_ev.duracao_h_media"]
    print(f"{'recargas/dia':>13} " + " ".join(f"{n} tomadas".rjust(11) for n in (2, 3, 4, 6)))
    ago = len(ev[ev.dt.dt.month == 8]) / df[df.dt.dt.month == 8].data.nunique()
    for taxa, rot in [(2.65, "jul/2026"), (ago, "ago/2026"), (8.3, "+3 meses"), (14.3, "+6 meses")]:
        a = taxa * dur / 12          # concentrado em ~12h do dia
        linha = " ".join(f"{erlang_b(a, n)*100:10.1f}%" for n in (2, 3, 4, 6))
        print(f"{taxa:9.1f} {rot:>9} {linha}")

    # ---- 7. O teto da 3ª hora ----
    print("\n" + "=" * 76)
    print("7. DEPOIS DA 3ª HORA, A VAGA É DE GRAÇA")
    t12 = P["precos.nova.carro.diaria_12h"]
    a = est[est.subcat == "Avulso Regular"]
    faixas = [(0, .5, "até 30min"), (.5, 1, "30min–1h"), (1, 3, "1h–3h · tarifa ainda sobe"),
              (3, 12, "3h–12h · TETO, paga o mesmo"), (12, 24, "12h–24h")]
    for lo, hi, lab in faixas:
        n = int(((a.horas > lo) & (a.horas <= hi)).sum())
        print(f"  {lab:30} {n:5d}  {n/len(a)*100:5.1f}%")
    teto = a[a.horas > 3]
    horas_gratis = (teto.horas - 3).sum()
    perda = (np.ceil(teto.horas - 3) * P["precos.nova.carro.hora_adicional"]).sum()
    print(f"\n>> {len(teto)} estadias no teto ({len(teto)/len(a)*100:.1f}%)")
    print(f">> {horas_gratis:.0f}h de vaga além da 3ª hora, a custo marginal zero")
    print(f">> cobrando a hora adicional até a 12ª: +R$ {perda:,.0f} "
          f"({perda/a.valor.sum()*100:.0f}% da receita de avulso)")

    # ---- 8. Inadimplência ----
    print("\n" + "=" * 76)
    print("8. A INADIMPLÊNCIA APARECE COMO RECEITA")
    ina = est[est.subcat == "Mensalista Inadimplente"]
    bl = df[df.Status == "Bloqueado"]
    print(f"bloqueios: {len(bl)} · clientes distintos: {bl.Cliente_ID.nunique()}")
    print(f"tickets pagos por bloqueado: {len(ina)} · receita R$ {ina.valor.sum():,.2f}")
    print(f"mensalidade média devida   : R$ {bo.Valor_Cobrado_Total.mean():.2f}")
    print(f"\n>> o cliente que não pagou gera linha POSITIVA no caixa.")
    print(">> antes de 06/2026 virava juros no boleto; depois, ticket de avulso.")
    print(">> um painel de faturamento diário não enxerga o problema.")
