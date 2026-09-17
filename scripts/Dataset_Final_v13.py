"""Dataset_Final_v13.py — gerador dirigido por parâmetros.

MUDANÇA ESTRUTURAL EM RELAÇÃO AO v12
------------------------------------
Não há nenhum número literal neste código. Tudo vem de `parametros.yaml`,
que é lido também pelo validador. Se um parâmetro não estiver declarado, o
gerador quebra na hora em vez de rodar com uma constante escondida.

Isso existe porque a EDA do v12 encontrou CINCO números que viviam só no
código e ninguém sabia: a tarifa de recarga, os valores de mensalidade, os
90% de sábado do trabalhador, a taxa de inadimplência e o bloqueio
automático. Todos contradiziam ou faltavam no regras_de_negocio.md.

O QUE MUDA NO CONTEÚDO (v12 -> v13)
-----------------------------------
 1. Empresa de logística (seção 38), presente até 31/05 — inclui o
    MOVIMENTO FANTASMA: motoboy passando a pé com carrinho usando o cartão
    da moto.
 2. Bloqueio de inadimplência só a partir do marco de 01/06 (seção 36.2).
    122 dos 157 bloqueios do v12 eram anacrônicos.
 3. Inadimplência com memória (cadeia de Markov) — o v12 tinha ZERO
    reincidentes, o oposto do real.
 4. Carga e Descarga com Subcategoria própria (seção 30).
 5. Canal de pagamento DERIVADO da forma — mata o PIX no Totem (seção 2).
 6. Hóspede de hotel de 1 diária (seção 25.1). O v12 tinha mínimo de 2.
 7. Mensalistas dormentes (seção 11.3): pagam e nunca movimentam.
 8. Perfis híbridos (seção 11.2): lojista com carro-garagem, morador que viaja.
 9. Morador com variação de fim de semana (seção 11.1b).
10. Cauda de avulso fora do horário comercial (seção 13).
11. `Motivo` derivado do valor final, não do nº de selos.
12. Coluna `Regra_Acesso` removida (constante desde o v10).
"""
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from params import carregar
from gerador.base import Motor
from gerador.clientes import montar
from gerador.fluxos import Faturamento, avulsos, hotel
from gerador.mensalistas import Mensalistas, Logistica


def gerar(caminho_yaml=None, saida="logs_estacionamento_v13.csv"):
    p = carregar(caminho_yaml)
    m = Motor(p)
    clientes, empresa = montar(m)
    fat = Faturamento(m, clientes)
    mens = Mensalistas(m, clientes, fat)
    log = Logistica(m, empresa)

    for i in range(m.dias):
        d = m.inicio + timedelta(days=i)
        dia0 = d.replace(hour=0, minute=0, second=0, microsecond=0)
        tipo_dia = m.tipo_de_dia(d)
        chance_ev = m.chance_ev_do_mes(d)

        fat.virada_de_mes(d)
        fat.atualiza_e_emite(d, dia0)

        avulsos(m, dia0, tipo_dia, chance_ev)
        hotel(m, dia0, chance_ev)
        mens.dia(d, dia0, tipo_dia, chance_ev)
        log.dia(d, dia0, tipo_dia)

    df = pd.DataFrame(m.logs, columns=Motor.COLS)
    df["_dt"] = pd.to_datetime(df["Data"] + " " + df["Hora"], format="%d/%m/%Y %H:%M:%S")
    df = df.sort_values("_dt", ascending=False).drop(columns=["_dt"]).reset_index(drop=True)
    df.to_csv(saida, index=False, encoding="utf-8")

    print(f"v13 gerado: {len(df):,} registros -> {saida}")
    print(f"  janela      : {m.inicio.date()} a {m.fim.date()} ({m.dias} dias)")
    print(f"  clientes    : {len(clientes)} · veículos: {sum(c['vagas'] for c in clientes)}")
    print(f"  parâmetros  : {len(p.lidos())} chaves lidas do YAML")
    return df, p


if __name__ == "__main__":
    gerar()
