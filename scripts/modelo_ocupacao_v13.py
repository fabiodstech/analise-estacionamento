"""Etapa 4 — modelo preditivo de ocupação sobre o v13.

Dois alvos: média diária e ocupação por hora.
Split TEMPORAL 75/25, sem embaralhar — embaralhar série temporal vaza o futuro.

Features só de calendário: nenhuma usa passado recente, então o modelo serve para
qualquer data futura. A persistência de 7 dias entra como referência, mas ela PRECISA
de histórico — a comparação com ela não é justa no mesmo eixo.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from eda3_negocio import carregar_dados, ocupacao, MARCO, FERIADOS

RS = 42


def features(idx, com_hora):
    """Só calendário. Nada que dependa de observar o passado recente."""
    d = pd.DataFrame(index=idx)
    dia = pd.Series(idx.date, index=idx) if com_hora else pd.Series(idx.date, index=idx)
    d["dow"] = idx.dayofweek
    d["mes"] = idx.month
    d["dia_do_ano"] = idx.dayofyear
    d["fds"] = (idx.dayofweek >= 5).astype(int)
    d["domingo"] = (idx.dayofweek == 6).astype(int)
    d["feriado"] = pd.Series([x in FERIADOS for x in dia], index=idx).astype(int)
    # o marco de 01/06 é um fato de calendário conhecido de antemão, não uma
    # observação do passado recente — cabe como feature e como baseline.
    d["pos_marco"] = pd.Series([x >= MARCO for x in dia], index=idx).astype(int)
    if com_hora:
        d["hora"] = idx.hour
        d["hora_sin"] = np.sin(2 * np.pi * idx.hour / 24)
        d["hora_cos"] = np.cos(2 * np.pi * idx.hour / 24)
    return d


def avaliar(y, com_hora, rotulo):
    X = features(y.index, com_hora)
    n = len(y)
    corte = int(n * 0.75)
    Xtr, Xte = X.iloc[:corte], X.iloc[corte:]
    ytr, yte = y.iloc[:corte], y.iloc[corte:]

    preds = {}
    preds["Média global"] = np.full(len(yte), ytr.mean())

    # baseline sazonal: média histórica do (dia da semana [, hora])
    chaves = ["dow", "hora"] if com_hora else ["dow"]
    tab = ytr.groupby([Xtr[k] for k in chaves]).mean()
    idx_te = pd.MultiIndex.from_arrays([Xte[k] for k in chaves]) if com_hora else Xte["dow"]
    preds["Baseline sazonal"] = pd.Series(idx_te.map(tab)).fillna(ytr.mean()).values

    # ⚠ baseline sazonal + degrau: MESMA ideia, com uma média por regime.
    #   Continua sendo baseline — duas tabelas de média, sem treino. Serve para
    #   isolar quanto da vantagem das árvores é só ter aprendido o marco de 01/06.
    chaves_m = chaves + ["pos_marco"]
    tab_m = ytr.groupby([Xtr[k] for k in chaves_m]).mean()
    idx_m = pd.MultiIndex.from_arrays([Xte[k] for k in chaves_m])
    preds["Baseline sazonal + degrau"] = pd.Series(idx_m.map(tab_m)).fillna(ytr.mean()).values

    # persistência 7 dias — precisa de histórico, entra só como referência
    lag = 7 * (24 if com_hora else 1)
    preds["Persistência 7 dias"] = y.shift(lag).iloc[corte:].fillna(ytr.mean()).values

    for nome, mod in [("Random Forest", RandomForestRegressor(n_estimators=300, random_state=RS)),
                      ("Gradient Boosting", GradientBoostingRegressor(random_state=RS))]:
        mod.fit(Xtr, ytr)
        preds[nome] = mod.predict(Xte)

    res = pd.DataFrame({k: [mean_absolute_error(yte, v)] for k, v in preds.items()}).T
    res.columns = ["MAE"]
    res = res.sort_values("MAE")
    res["posição"] = range(1, len(res) + 1)

    print(f"\n{'=' * 74}\n{rotulo}")
    print(f"treino: {y.index[0]:%d/%m} a {y.index[corte-1]:%d/%m} ({corte} pontos) · "
          f"teste: {y.index[corte]:%d/%m} a {y.index[-1]:%d/%m} ({n-corte} pontos)")
    print(f"alvo: média {yte.mean():.1f} · amplitude semanal "
          f"{ytr.groupby(Xtr.dow).mean().max() - ytr.groupby(Xtr.dow).mean().min():.1f}\n")
    print(res.round(3).to_string())

    # o topo é separável?
    print("\nWilcoxon entre os quatro melhores (erro absoluto ponto a ponto):")
    top = list(res.index[:4])
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            a = np.abs(yte.values - preds[top[i]])
            b = np.abs(yte.values - preds[top[j]])
            p = stats.wilcoxon(a, b).pvalue
            ganho = (b.mean() - a.mean()) / b.mean() * 100
            sig = "SIM" if p < 0.05 else "não"
            print(f"  {top[i]:20} vs {top[j]:20} ganho {ganho:+5.1f}%  p={p:.3f}  significativo: {sig}")
    return res, preds, yte


if __name__ == "__main__":
    df = carregar_dados()
    occ = ocupacao(df, "Carro")
    occ.index = pd.DatetimeIndex(occ.index)

    diaria = occ.resample("D").mean()
    r1, p1, y1 = avaliar(diaria, False, "ALVO 1 — OCUPAÇÃO MÉDIA DIÁRIA (carros)")
    r2, p2, y2 = avaliar(occ, True, "ALVO 2 — OCUPAÇÃO POR HORA (carros)")

    print(f"\n{'=' * 74}\nCONTEXTO")
    cap = 378
    print(f"  erro do campeão diário : {r1.MAE.min():.2f} carros = "
          f"{r1.MAE.min()/cap*100:.2f} p.p. das {cap} vagas")
    print(f"  erro do campeão horário: {r2.MAE.min():.2f} carros = "
          f"{r2.MAE.min()/cap*100:.2f} p.p.")
    d = diaria.copy()
    print(f"  autocorrelação diária  : lag-1 {d.autocorr(1):.2f} · lag-7 {d.autocorr(7):.2f}")
