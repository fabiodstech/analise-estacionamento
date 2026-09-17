"""Regras de cálculo do painel, sem nenhuma dependência de Streamlit.

Este arquivo existe para que as contas do app possam ser TESTADAS — é o mesmo
princípio do gerador: se a regra vale a pena, vale uma asserção. Ver
`testes_app.py`.

Nada aqui lê arquivo nem guarda estado: tudo entra por parâmetro.
"""
import math


def tarifa(minutos, veiculo, precos):
    """Valor cobrado por uma estadia, e a explicação da faixa aplicada.

    O teto da diária de 12h é atingido bem antes das 12 horas: a partir dele,
    hora adicional não é mais cobrada.
    """
    t = precos["carro" if veiculo == "Carro" else "moto"]
    if minutos <= 30:
        return t["meia_hora"], "tarifa de meia hora"
    if minutos <= 60:
        return t["uma_hora"], "tarifa de 1 hora"
    if minutos <= 720:
        adicionais = math.ceil((minutos - 60) / 60)
        bruto = t["uma_hora"] + adicionais * t["hora_adicional"]
        if bruto >= t["diaria_12h"]:
            return t["diaria_12h"], "no teto — horas adicionais não são mais cobradas"
        return bruto, f"1 hora + {adicionais}x hora adicional"
    return math.ceil(minutos / 1440) * t["diaria_24h"], "diária de 24 horas"


def erlang_b(taxa_dia, n_tomadas, duracao_h, janela_h=12):
    """Chance (%) de o motorista chegar e achar todas as tomadas ocupadas."""
    a = taxa_dia * duracao_h / janela_h
    b = 1.0
    for i in range(1, n_tomadas + 1):
        b = a * b / (i + a * b)
    return b * 100


def curva_ocupacao(dia, modelo, feriados, tipo="carro"):
    """Ocupação por hora. Feriado tem curva própria; moto tem tabela própria."""
    if tipo == "moto":
        base = fb = modelo["moto_atual"]
    else:
        base = modelo["curva_feriado"] if str(dia) in feriados else modelo["curva_atual"]
        fb = modelo["curva_atual"]
    return [base.get(f"{dia.weekday()}-{h}", fb.get(f"{dia.weekday()}-{h}", 0))
            for h in range(24)]


def curva_manobras(dia, modelo, feriados):
    f = 0.5 if str(dia) in feriados else 1.0   # feriado: ~45% das lojas abrem
    return [modelo["manobras"].get(f"{dia.weekday()}-{h}", 0) * f for h in range(24)]
