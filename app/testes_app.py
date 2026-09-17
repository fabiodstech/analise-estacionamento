"""Testes do painel — a mesma disciplina do gerador, aplicada ao app.

O gerador tem 25 asserções; o app tinha zero. Estas checam as três coisas que
podem quebrar em silêncio: o contrato do `modelo.json`, as contas de tarifa e
de fila, e a cobertura de turnos.

    python testes_app.py          (roda tudo e imprime o resultado)
    pytest testes_app.py          (se preferir pytest)

Nenhum teste abre o Streamlit — por isso as contas moram em `regras.py`.
"""
import json
from datetime import date
from pathlib import Path

import regras
from escala import (MANOBRISTAS, APOIO, ALMOCO, cobertura, cobertura_com_almoco,
                    horas_de, horas_efetivas, tipo_de_escala)

BASE = Path(__file__).parent
M = json.loads((BASE / "modelo.json").read_text(encoding="utf-8"))
VERSAO_MINIMA = 5   # o app aceita esta versão ou mais nova


# ---------------------------------------------------------------- contrato
def test_schema_do_modelo():
    """O app quebra com KeyError seco se o artefato vier de outra versão."""
    # ⚠ o app compara com `<`, não com `==`: um artefato MAIS NOVO é válido.
    #   Exigir igualdade aqui reprovava o v6, que traz a correção do
    #   denominador da aderência (mensalista inadimplente, regra 36.6).
    assert M["meta"]["versao_artefato"] >= VERSAO_MINIMA, (
        f'artefato v{M["meta"]["versao_artefato"]}, mínimo v{VERSAO_MINIMA}')
    for bloco in ("capacidade", "capacidade_moto", "manobras", "curva_atual",
                  "curva_feriado", "moto_atual", "receita", "recarga_ev",
                  "precos", "feriados", "experimento_denominador",
                  "experimento_bloqueado", "experimento_modelo", "projeto"):
        assert bloco in M, f"falta o bloco {bloco}"
    for veic in ("carro", "moto"):
        for campo in ("meia_hora", "uma_hora", "hora_adicional",
                      "diaria_12h", "diaria_24h"):
            assert campo in M["precos"][veic], f"falta precos.{veic}.{campo}"


def test_curvas_cobrem_a_semana_inteira():
    for nome in ("curva_atual", "moto_atual"):
        faltando = [f"{d}-{h}" for d in range(7) for h in range(24)
                    if f"{d}-{h}" not in M[nome]]
        assert not faltando, f"{nome} não tem {len(faltando)} células"


def test_feriados_sao_datas_validas():
    for f in M["feriados"]:
        date.fromisoformat(f)


def test_ocupacao_nao_passa_da_capacidade():
    """Era o sintoma do bug de pareamento do v12: 62 motos em 60 vagas."""
    cap = M["capacidade"]["carro"]
    for nome in ("curva_atual", "curva_antiga", "curva_feriado"):
        assert max(M[nome].values()) <= cap, f"{nome} estoura as {cap} vagas"
    assert max(M["moto_atual"].values()) <= M["capacidade_moto"]["vagas"]


# ---------------------------------------------------------------- tarifa
def _preco(minutos, veiculo="Carro"):
    return regras.tarifa(minutos, veiculo, M["precos"])[0]


def test_faixas_da_tarifa():
    p = M["precos"]["carro"]
    assert _preco(1) == p["meia_hora"]
    assert _preco(30) == p["meia_hora"]
    assert _preco(31) == p["uma_hora"]
    assert _preco(60) == p["uma_hora"]
    assert _preco(61) == p["uma_hora"] + p["hora_adicional"]


def test_teto_da_diaria_de_12h():
    """O teto é atingido bem antes das 12 horas, e não pode ser ultrapassado."""
    p = M["precos"]["carro"]
    for minutos in range(61, 721):
        assert _preco(minutos) <= p["diaria_12h"], f"{minutos} min passou do teto"
    assert _preco(720) == p["diaria_12h"]
    assert _preco(721) == p["diaria_24h"]
    assert _preco(1441) == 2 * p["diaria_24h"]


def test_tarifa_nunca_diminui_com_o_tempo():
    anterior = 0
    for minutos in range(1, 2881, 5):
        atual = _preco(minutos)
        assert atual >= anterior, f"caiu em {minutos} min"
        anterior = atual


def test_moto_e_mais_barata_que_carro():
    for minutos in (30, 60, 300, 720):
        assert _preco(minutos, "Moto") <= _preco(minutos, "Carro")


# ---------------------------------------------------------------- Erlang B
def _bloqueio(taxa, tomadas):
    return regras.erlang_b(taxa, tomadas, M["recarga_ev"]["duracao_h"])


def test_erlang_dentro_da_faixa():
    for taxa in (0.5, 5, 20):
        for tomadas in (1, 2, 3, 6):
            assert 0 <= _bloqueio(taxa, tomadas) <= 100


def test_mais_tomadas_bloqueiam_menos():
    for taxa in (2, 5, 10, 20):
        valores = [_bloqueio(taxa, n) for n in range(1, 8)]
        assert valores == sorted(valores, reverse=True), f"não caiu em taxa={taxa}"


def test_mais_demanda_bloqueia_mais():
    for tomadas in (2, 3, 4):
        valores = [_bloqueio(t, tomadas) for t in range(1, 21)]
        assert valores == sorted(valores), f"não subiu com {tomadas} tomadas"


def test_sem_demanda_nao_ha_bloqueio():
    assert _bloqueio(0, 2) == 0


# ---------------------------------------------------------------- escala
def test_cobertura_tem_24_horas_e_nao_e_negativa():
    for dia in ("seg_sex", "sabado", "domingo"):
        c = cobertura(MANOBRISTAS[dia])
        assert len(c) == 24
        assert min(c) >= 0


def test_turno_da_noite_atravessa_a_meia_noite():
    """Manobrista 7 entra 22h e sai 6h: as duas pontas precisam ser contadas."""
    c = cobertura([("Manobrista 7", 22.0, 30.0)])
    assert c[23] == 1 and c[0] == 1 and c[5] == 1
    assert c[12] == 0


def test_intervalo_reduz_a_presenca():
    turnos = MANOBRISTAS["seg_sex"]
    assert horas_efetivas(turnos) < horas_de(turnos)
    esperado = horas_de(turnos) - sum(ALMOCO.get(n, 0) for n, _, _ in turnos)
    assert abs(horas_efetivas(turnos) - esperado) < 1e-9


def test_almoco_muda_a_cobertura_onde_importa():
    """O "ótimo" é melhor NA DEMANDA, não hora a hora.

    Fora do pico o ótimo chega a ficar abaixo do pior caso — é justamente ali
    que ele manda todo mundo almoçar. O que precisa valer é: mesma quantidade
    de intervalo, mais gente disponível no pico, e melhor cobertura ponderada
    pela demanda. A diferença entre os dois é o custo de não ter regra.
    """
    dem = [10] * 8 + [40] * 8 + [10] * 8
    turnos = MANOBRISTAS["seg_sex"]
    oti = cobertura_com_almoco(turnos, dem, "otimo")
    pio = cobertura_com_almoco(turnos, dem, "pior")
    assert abs(sum(oti) - sum(pio)) < 1e-9, "o intervalo total mudou entre os casos"
    h_pico = dem.index(max(dem))
    assert pio[h_pico] < oti[h_pico], "o pior caso não piorou no pico"
    assert sum(o * d for o, d in zip(oti, dem)) > sum(p * d for p, d in zip(pio, dem))


def test_escala_por_tipo_de_dia():
    assert tipo_de_escala(0) == "seg_sex"
    assert tipo_de_escala(5) == "sabado"
    assert tipo_de_escala(6) == "domingo"
    assert tipo_de_escala(2, feriado=True) == "domingo"   # feriado usa domingo
    assert APOIO["domingo"] == []


# ---------------------------------------------------------------- curvas
def test_feriado_usa_a_curva_de_feriado():
    feriado = date.fromisoformat(M["feriados"][1])
    normal = date(2026, 8, 13)
    assert regras.curva_ocupacao(feriado, M, set(M["feriados"])) != \
        regras.curva_ocupacao(normal, M, set(M["feriados"]))


def test_feriado_tem_menos_manobra():
    feriado = date.fromisoformat(M["feriados"][1])
    igual = date(2026, 8, 13)   # mesma quinta-feira, sem feriado
    fer = sum(regras.curva_manobras(feriado, M, set(M["feriados"])))
    nor = sum(regras.curva_manobras(igual, M, set(M["feriados"])))
    assert fer < nor


if __name__ == "__main__":
    testes = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("test_") and callable(f)]
    falhas = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"  ok    {nome}")
        except AssertionError as e:
            falhas += 1
            print(f"  FALHA {nome}: {e}")
        except Exception as e:  # noqa: BLE001
            falhas += 1
            print(f"  ERRO  {nome}: {type(e).__name__}: {e}")
    print(f"\n{len(testes) - falhas}/{len(testes)} passando")
    raise SystemExit(1 if falhas else 0)
