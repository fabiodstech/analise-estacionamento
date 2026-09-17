"""Escala real da operação e otimizador de cobertura de turnos.

A ESCALA É DADO REAL, informado por quem trabalha lá (06/09/2026). É a primeira
peça do painel que não depende do dataset sintético para existir.

⚠ A DEMANDA continua sendo sintética. Então tudo que compara escala com demanda
é "dada esta curva de demanda", não "a escala está errada".
"""
import numpy as np
# (o solver do otimizador saiu junto com ele — ver a nota abaixo)


# ============================================================================
# A ESCALA REAL
# ============================================================================
QUADRO = {"gerente": 1, "caixas": 2, "manobristas": 7}
JORNADA = {"36h": 5, "44h": 2}      # dos 7 manobristas

# Intervalo de almoço, em horas. ⚠ O HORÁRIO do intervalo não é fixo nem
# informado — só a duração. O modelo trata isso explicitamente (ver
# `cobertura_com_almoco`), porque quando o intervalo cai muda a cobertura no pico.
ALMOCO = {
    "Manobrista 1": 0.5, "Manobrista 3": 0.5, "Manobrista 4": 0.5,
    "Manobrista 5": 0.5, "Manobrista 6": 0.5,   # turnos de 6h30: 30 min
    "Manobrista 2": 1.0,                         # turno de 9h: 1 hora
    "Manobrista 7": 0.0,                         # noite, sem intervalo
    "Gerente": 1.0, "Caixa 1": 1.0, "Caixa 2": 1.0,
    "Turno manhã": 1.0, "Turno tarde": 1.0,
}

MANOBRISTAS = {
    "seg_sex": [
        ("Manobrista 1", 6.0, 12.5),
        ("Manobrista 2", 6.0, 15.0),
        ("Manobrista 3", 8.5, 15.0),
        ("Manobrista 4", 12.0, 18.5),
        ("Manobrista 5", 15.0, 21.5),
        ("Manobrista 6", 15.5, 22.0),
        ("Manobrista 7", 22.0, 30.0),      # 22h às 6h do dia seguinte
    ],
    "sabado": [
        ("Manobrista 1", 6.0, 12.5),
        ("Manobrista 5", 6.5, 13.0),
        ("Manobrista 3", 9.0, 15.5),
        ("Manobrista 6", 11.0, 17.5),
        ("Manobrista 4", 11.5, 18.0),
        ("Manobrista 2", 18.0, 30.0),      # 12h seguidas: cobre a folga do M7
    ],
    # domingo não tem escala fixa: dois turnos de 8h pagos por fora,
    # e os manobristas decidem entre si quem vem.
    "domingo": [("Turno manhã", 6.0, 14.0), ("Turno tarde", 14.0, 22.0)],
}

APOIO = {
    "seg_sex": [("Gerente", 8.0, 17.0), ("Caixa 1", 8.5, 17.5), ("Caixa 2", 10.5, 19.5)],
    "sabado": [("Gerente", 10.0, 14.0), ("Caixa 1", 8.0, 12.0), ("Caixa 2", 12.0, 16.0)],
    "domingo": [],
}


def cobertura(turnos):
    """Pessoas presentes em cada hora do dia. Trata turnos que viram a meia-noite."""
    c = np.zeros(24)
    for _, ini, fim in turnos:
        for h in range(24):
            for desloc in (0, -24):
                a, b = max(ini + desloc, h), min(fim + desloc, h + 1)
                if b > a:
                    c[h] += 1
    return c


def _janela_livre(ini, fim, dur):
    """Horas em que o intervalo pode começar: nunca na primeira nem na última hora."""
    passos = []
    h = ini + 1
    while h + dur <= fim - 1:
        passos.append(round(h, 1))
        h += 0.5
    return passos or [round((ini + fim) / 2 - dur / 2, 1)]


def cobertura_com_almoco(turnos, demanda, modo="otimo"):
    """Cobertura descontando o intervalo de cada pessoa.

    ⚠ A operação informou a DURAÇÃO do intervalo, não o horário. Então o modelo
    não pode afirmar como fica a cobertura — só o intervalo entre o melhor e o
    pior caso:

      'otimo'  — cada um almoça na hora de menor demanda do seu turno
      'pior'   — cada um almoça na hora de maior demanda do seu turno

    A diferença entre os dois é exatamente o que uma regra de intervalo
    resolveria, e o que a falta dela custa no pico.
    """
    c = cobertura(turnos).astype(float)
    demanda = np.asarray(demanda, dtype=float)
    for nome, ini, fim in turnos:
        dur = ALMOCO.get(nome, 0.0)
        if not dur:
            continue
        cands = _janela_livre(ini, fim, dur)
        chave = (lambda h: demanda[int(h) % 24]) if modo == "otimo" else \
                (lambda h: -demanda[int(h) % 24])
        inicio = min(cands, key=chave)
        for h in range(24):
            for desloc in (0, -24):
                a, b = max(inicio + desloc, h), min(inicio + dur + desloc, h + 1)
                if b > a:
                    c[h] -= (b - a)
    return np.maximum(c, 0)


def horas_efetivas(turnos):
    """Horas de presença menos os intervalos."""
    return horas_de(turnos) - sum(ALMOCO.get(n, 0.0) for n, _, _ in turnos)


def cobertura_caixa(dia):
    return cobertura([t for t in APOIO.get(dia, []) if t[0].startswith("Caixa")])


def tipo_de_escala(dow, feriado=False):
    if feriado or dow == 6:
        return "domingo"
    return "sabado" if dow == 5 else "seg_sex"


# ============================================================================
# NOTA — o otimizador de turnos foi REMOVIDO
# ============================================================================
# Havia aqui um solver de cobertura de turnos (programa inteiro) que calculava a
# "escala ideal" para uma dada curva de demanda e um ritmo por manobrista.
#
# Foi retirado porque exigia dois números que ninguém pode verificar:
#   1. a curva horária de movimento — que no dataset é design do gerador, não
#      observação (as janelas de chegada são constantes do código);
#   2. quantos carros um manobrista movimenta por hora — que nunca foi
#      cronometrado, e que quem trabalha na operação não consegue estimar
#      porque não segue padrão fixo.
#
# Multiplicar os dois devolvia uma recomendação de equipe com aparência de
# precisão. Era o único ponto do projeto que fazia o que o resto dele critica.
#
# O que sobrou aqui descreve a escala real e a ambiguidade do intervalo — tudo
# derivado de dado informado pela operação, sem nada calculado por cima.
#
# Para reativar seria preciso, antes, cronometrar algumas dezenas de manobras.

def horas_de(turnos):
    """Horas de presença somadas."""
    return sum(fim - ini for _, ini, fim in turnos)


def formata(h):
    h = h % 24
    return f"{int(h):02d}:{int(round((h - int(h)) * 60)):02d}"
