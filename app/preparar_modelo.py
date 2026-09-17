"""Prepara o artefato que o app consome.

⚠ O app NÃO lê o CSV de 15 MB. Ele lê este JSON de alguns KB.

O modelo escolhido é o **baseline sazonal com degrau** (ver
`modelo_ocupacao_v13.md`): média histórica por dia da semana e hora, calculada
separadamente para cada regime. Ele erra 2,71 carros contra 2,23 do Gradient
Boosting, e a diferença não é estatisticamente significativa (p = 0,150) — mas
ele não precisa de treino, de biblioteca nem de explicação.

⚠ Para prever o FUTURO, só a tabela do regime atual (pós 01/06) importa. A do
regime antigo fica no artefato apenas como contexto histórico.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from params import carregar
from eda3_negocio import carregar_dados, ocupacao, MARCO, FERIADOS

SAIDA = Path(__file__).parent / "app" / "modelo.json"


def main():
    P = carregar()
    df = carregar_dados()
    occ = ocupacao(df, "Carro")
    occ.index = pd.DatetimeIndex(occ.index)

    d = pd.DataFrame({"occ": occ.values}, index=occ.index)
    d["dow"] = d.index.dayofweek
    d["hora"] = d.index.hour
    d["pos"] = (pd.Series(d.index.date, index=d.index) >= MARCO).astype(int).values
    d["feriado"] = pd.Series([x in FERIADOS for x in d.index.date], index=d.index).astype(int).values

    def tabela(sub):
        t = sub.groupby(["dow", "hora"]).occ.mean().round(2)
        return {f"{k[0]}-{k[1]}": float(v) for k, v in t.items()}

    atual = d[d.pos == 1]
    antigo = d[d.pos == 0]

    # feriado tem curva própria: o comércio abre parcialmente (regra 13)
    fer = d[(d.pos == 1) & (d.feriado == 1)]
    if len(fer) < 24:                       # pouca amostra pós-marco: usa a série toda
        fer = d[d.feriado == 1]

    men = df[(df.Categoria_Principal == "Mensalista") & (df.Tipo_Veiculo == "Carro")]

    # ---- ARMADILHA 1: quanto cada segmento move a aderência ao totem ----------
    sai = df[df.Sentido == "Saída"]
    card = sai[sai.Forma_Pagamento.str.contains("Cartão", na=False)].copy()
    grupos = {
        "hotel": card.Subcategoria == "Hóspede Hotel",
        "moto": card.Tipo_Veiculo == "Moto",
        "selo": card.Selos_Apresentados > 0,
        "recarga": card.Valor_Recarga_EV > 0,
        "inadimplente": card.Subcategoria == "Mensalista Inadimplente",
        "carga": card.Subcategoria == "Carga e Descarga",
    }
    aderencia = {}
    for nome, mask in grupos.items():
        g = card[mask]
        aderencia[nome] = {"totem": int((g.Local_Pagamento == "Totem").sum()),
                           "caixa": int((g.Local_Pagamento == "Caixa").sum())}
    puro = card[~np.any(list(grupos.values()), axis=0)]
    aderencia["elegivel"] = {"totem": int((puro.Local_Pagamento == "Totem").sum()),
                             "caixa": int((puro.Local_Pagamento == "Caixa").sum())}

    # ---- ARMADILHA 2: a entrada bloqueada, medida no v12 ----------------------
    # É onde o erro aconteceu, e é o registro histórico dele. No v13 o bloqueio
    # só existe a partir de junho, então o efeito seria pequeno demais para ver.
    ocup_v12 = {
        "com_bloqueio": {"moto": 62, "carro": 222},
        "sem_bloqueio": {"moto": 21, "carro": 109},
    }
    armadilhas = {"aderencia": aderencia, "ocupacao_v12": ocup_v12}

    # ---- MANOBRAS: o driver de custo da operação -----------------------------
    # Cada evento de CARRO é uma manobra: manobrista + viagem de elevador.
    # Moto não entra — o cliente estaciona sozinho (regra 23).
    mov = df[(df.Sentido.isin(["Entrada", "Saída"])) & (df.Status != "Bloqueado")]
    car = mov[(mov.Tipo_Veiculo == "Carro") & (mov.data >= MARCO)].copy()
    car["dow"] = car.dt.dt.dayofweek
    nd = car.groupby("dow").data.nunique()
    man = (car.groupby(["dow", "hora"]).size() / car.groupby("dow").data.nunique()).round(2)
    manobras = {f"{k[0]}-{k[1]}": float(v) for k, v in man.items()}

    # ---- OCUPAÇÃO DE MOTO, por regime ---------------------------------------
    om = ocupacao(df, "Moto")
    om.index = pd.DatetimeIndex(om.index)
    dm = pd.DataFrame({"occ": om.values}, index=om.index)
    dm["pos"] = (pd.Series(dm.index.date, index=dm.index) >= MARCO).astype(int).values
    dm["dow"] = dm.index.dayofweek
    dm["hora"] = dm.index.hour
    moto_atual = {f"{k[0]}-{k[1]}": float(v) for k, v in
                  dm[dm.pos == 1].groupby(["dow", "hora"]).occ.mean().round(2).items()}

    # ---- RECEITA por segmento (para o painel) -------------------------------
    est_pagas = []
    tot_dias = df.data.nunique()
    rec = {}
    for sub, g in df[df.Valor_Cobrado_Total > 0].groupby("Subcategoria"):
        rec[sub] = {"total": round(float(g.Valor_Cobrado_Total.sum()), 2),
                    "n": int(len(g)),
                    "ticket": round(float(g.Valor_Cobrado_Total.mean()), 2)}

    artefato = {
        "meta": {
            # ⚠ Bater com VERSAO_ESPERADA no app.py. Serve para detectar o caso de
            #   alguém baixar um app.py novo e ficar com um modelo.json antigo.
            "versao_artefato": 3,
            "gerado_de": "logs_estacionamento_v13.csv",
            "modelo": "baseline sazonal com degrau (dia da semana x hora, por regime)",
            "mae_diario": 2.71,
            "mae_horario": 3.66,
            "marco": str(MARCO),
            "obs_por_celula": int(atual.groupby(["dow", "hora"]).size().min()),
        },
        "capacidade": {
            "carro": int(P["capacidade.carro.vagas"]),
            "contratadas": int(men.Veiculo_ID.nunique()),
        },
        "curva_atual": tabela(atual),
        "manobras": manobras,
        "moto_atual": moto_atual,
        "receita": rec,
        "dias_periodo": int(tot_dias),
        "curva_antiga": tabela(antigo),
        "curva_feriado": tabela(fer),
        "feriados": sorted(str(x) for x in FERIADOS),
        "precos": {
            "carro": dict(P["precos.nova.carro"]),
            "moto": dict(P["precos.nova.moto"]),
            "carga_descarga": float(P["precos.carga_descarga.tarifa_fixa"]),
            "limite_carga_min": int(P["precos.carga_descarga.limite_minutos"]),
        },
        "selo": {
            "preco_venda": float(P["selo.preco_venda_apos"]),
            "desconto": "uma_hora_tabela_vigente",
        },
        # ---- dados das armadilhas interativas (aba "Erre você mesmo") ----
        "armadilhas": armadilhas,
        "capacidade_moto": {
            "vagas": int(P["capacidade.moto.vagas"]),
            "contratadas": int(df[(df.Categoria_Principal == "Mensalista")
                                  & (df.Tipo_Veiculo == "Moto")].Veiculo_ID.nunique()),
        },
        "recarga_ev": {
            "tomadas": int(P["capacidade.tomadas_ev.instaladas"]),
            "em_obra": int(P["capacidade.tomadas_ev.em_obra"]),
            "duracao_h": float(P["recarga_ev.duracao_h_media"]),
            "kwh_sessao": float(P["recarga_ev.kwh_por_sessao_medio"]),
            "tarifa": float(list(P["recarga_ev.tarifa_por_kwh"].values())[-1])
                      if isinstance(list(P["recarga_ev.tarifa_por_kwh"].values())[-1], (int, float))
                      else 2.50,
            "serie_real": {"2026-02": 1.11, "2026-03": 1.23, "2026-04": 2.00,
                           "2026-05": 1.84, "2026-06": 2.60, "2026-07": 2.65,
                           "2026-08": 4.80},
            "recargas_dia_atual": 4.80,
        },
    }

    # ---- dados dos experimentos interativos (aba "Faça o erro") -------------
    sa = df[df.Sentido == "Saída"].copy()
    card = sa.Forma_Pagamento.str.contains("Cartão", na=False)
    sa = sa[card]

    def _tc(mask):
        x = sa[mask]
        return [int((x.Local_Pagamento == "Totem").sum()),
                int((x.Local_Pagamento == "Caixa").sum())]

    av = sa.Subcategoria == "Avulso Regular"
    # ⚠ O MENSALISTA INADIMPLENTE ENTRA NO NÚCLEO (seção 36.6). Ele retira ticket
    #   na cancela e paga no totem como qualquer avulso — é elegível, e por isso
    #   pertence ao denominador da aderência. A versão anterior o tratava como
    #   exclusão, e a regra escrita é que estava errada: o gerador sempre sorteou
    #   o canal dele entre totem e caixa.
    inad = sa.Subcategoria == "Mensalista Inadimplente"
    artefato["experimento_denominador"] = {
        "nucleo": _tc(((av & (sa.Selos_Apresentados == 0) & (sa.Valor_Recarga_EV == 0))
                       | inad) & (sa.Tipo_Veiculo == "Carro")),
        "hotel": _tc(sa.Subcategoria == "Hóspede Hotel"),
        "moto": _tc(av & (sa.Tipo_Veiculo == "Moto")),
        "selo": _tc(av & (sa.Selos_Apresentados > 0)),
        "recarga": _tc(av & (sa.Valor_Recarga_EV > 0) & (sa.Selos_Apresentados == 0)),
        "carga": _tc(sa.Subcategoria == "Carga e Descarga"),
    }

    # ⚠ medido no v12, ANTES da correção — é a demonstração do bug que foi achado.
    #   No v13 o bloqueio só existe a partir de junho e o efeito seria pequeno.
    artefato["experimento_bloqueado"] = {
        "fonte": "v12 (antes da correção)",
        "moto": {"sem": [21, 8.9], "com": [62, 36.6], "capacidade": 60},
        "carro": {"sem": [109, 70.3], "com": [222, 137.5], "capacidade": 378},
    }

    artefato["experimento_modelo"] = {
        "Média global": 7.27, "Persistência 7 dias": 3.25,
        "Baseline sazonal": 3.27, "Baseline sazonal + degrau": 2.71,
        "Random Forest": 2.24, "Gradient Boosting": 2.23,
        "p_gb_vs_baseline_degrau": 0.150, "p_gb_vs_baseline_simples": 0.021,
    }

    artefato["projeto"] = {
        "secoes_de_regra": 39, "asercoes": 25, "asercoes_antes": 12,
        "numeros_so_no_codigo": 8, "achados_auditados": 15, "achados_reprovados": 8,
        "validacao_externa": 1.01, "versoes_do_gerador": 13,
    }

    SAIDA.parent.mkdir(exist_ok=True)
    # encoding explícito nos dois lados: escrita aqui, leitura no app.
    SAIDA.write_text(json.dumps(artefato, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    kb = SAIDA.stat().st_size / 1024
    print(f"{SAIDA.name}: {kb:.0f} KB · {len(artefato['curva_atual'])} células "
          f"· mínimo de {artefato['meta']['obs_por_celula']} observações por célula")


if __name__ == "__main__":
    main()
