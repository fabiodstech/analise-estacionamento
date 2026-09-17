"""Cadastro de clientes do v13.

Novidades em relação ao v12, todas confirmadas com o informante:
  - DORMENTE (seção 11.3): paga boleto e nunca movimenta o veículo.
  - CARRO-GARAGEM (11.2a): lojista com 2+ vagas deixa um veículo parado.
  - MORADOR VIAJANTE (11.2b): viaja levando o carro ou deixando-o guardado.
  - LOCAÇÃO DE ESPAÇO (seção 38): a empresa de logística, até 31/05.
"""
import random
from datetime import timedelta


def _sorteia(p, caminho):
    d = p[caminho]
    return random.choices(d["valores"], weights=d["pesos"])[0]


def montar(motor):
    p, m = motor.p, motor
    clientes = []

    n_loj = p["base_clientes.lojistas"]
    n_mor = p["base_clientes.moradores"]

    # ---------------- Trabalhador (Lojista / Escritório) ----------------
    for i in range(1, n_loj + 1):
        vagas = _sorteia(p, "base_clientes.vagas_lojista")
        tipo = "Carro" if random.random() < p["base_clientes.chance_carro_lojista"] else "Moto"
        clientes.append(dict(
            cliente_id=f"LOJ-{i:03d}", nome=f"Loja/Escritório {i}",
            perfil="Trabalhador", subcategoria="Lojista / Escritório",
            vagas=vagas, tipo_veiculo=tipo,
            is_ev=False, veiculos_ev=set(), ev_dependente=False, placa_danificada=False,
            usa_cartao_vaga=(tipo == "Carro"
                             and random.random() < p["identificacao.chance_cartao_vaga_trabalhador"]),
            ingresso=m.inicio, saida=None, dormente=False, carros_garagem=set(),
            viajante=False, modo_viagem=None))

    # ---------------- Morador ----------------
    n_dep = p["base_clientes.personas_ev_dependentes"]
    dependentes = set(random.sample(range(1, n_mor + 1), n_dep))
    for i in range(1, n_mor + 1):
        vagas = _sorteia(p, "base_clientes.vagas_morador")
        tipo = "Carro" if random.random() < p["base_clientes.chance_carro_morador"] else "Moto"
        ev_dep = i in dependentes
        if ev_dep:
            tipo, vagas = "Carro", 1
        clientes.append(dict(
            cliente_id=f"MOR-{i:03d}", nome=f"Morador {i}",
            perfil="Morador", subcategoria="Morador",
            vagas=vagas, tipo_veiculo=tipo,
            is_ev=ev_dep, veiculos_ev=({0} if ev_dep else set()),
            ev_dependente=ev_dep, placa_danificada=False,
            usa_cartao_vaga=(tipo == "Carro"
                             and random.random() < p["identificacao.chance_cartao_vaga_morador"]),
            ingresso=p.dt("marco_modernizacao.data") if ev_dep else m.inicio,
            saida=None, dormente=False, carros_garagem=set(),
            viajante=False, modo_viagem=None))

    # ---------------- frota elétrica: contada, não sorteada ----------------
    # O volume de recarga é ancorado na série real do app (seção 6.2), então o
    # que precisa ser fixo é o NÚMERO de veículos elétricos — não uma chance
    # por cliente cujo total varia com a seed.
    n_ev = p["base_clientes.frota_ev_mensalista"]
    peso = {"Trabalhador": p["base_clientes.chance_ev_lojista"],
            "Morador": p["base_clientes.chance_ev_morador"]}
    candidatos = [c for c in clientes
                  if c["perfil"] in peso and c["tipo_veiculo"] == "Carro" and not c["ev_dependente"]]
    escolhidos = random.choices(candidatos, weights=[peso[c["perfil"]] for c in candidatos],
                                k=min(n_ev * 3, len(candidatos)))
    vistos = []
    for c in escolhidos:
        if c not in vistos:
            vistos.append(c)
        if len(vistos) == n_ev:
            break
    for c in vistos:
        c["is_ev"] = True
        # ⚠ um cliente com 3 vagas não tem 3 elétricos. O EV é UM veículo.
        c["veiculos_ev"] = {0}

    # ---------------- 11.2a: lojista com carro-garagem ----------------
    # 2-3 clientes com 2+ vagas deixam UM veículo parado em definitivo.
    lo, hi = p.faixa("segmentos.trabalhador.clientes_com_carro_garagem")
    elegiveis = [c for c in clientes if c["perfil"] == "Trabalhador" and c["vagas"] >= 2]
    for c in random.sample(elegiveis, min(random.randint(lo, hi), len(elegiveis))):
        c["carros_garagem"] = {c["vagas"] - 1}   # o último veículo fica parado

    # ---------------- 11.2b: morador viajante ----------------
    lo, hi = p.faixa("segmentos.morador.clientes_viajantes")
    moradores = [c for c in clientes if c["perfil"] == "Morador" and not c["ev_dependente"]]
    for c in random.sample(moradores, min(random.randint(lo, hi), len(moradores))):
        c["viajante"] = True
        pesos = p["segmentos.morador.modos_de_viagem"]
        c["modo_viagem"] = random.choices(
            ["leva_o_carro", "deixa_o_carro"],
            weights=[pesos["leva_o_carro"]["peso"], pesos["deixa_o_carro"]["peso"]])[0]

    # ---------------- 11.3: dormentes ----------------
    # Pagam boleto todo mês e NUNCA passam pela cancela.
    veic = p["segmentos.dormente.veiculos"]
    idx = 1
    for tipo, qtd in (("Carro", veic["carro"]), ("Moto", veic["moto"])):
        for _ in range(qtd):
            clientes.append(dict(
                cliente_id=f"DOR-{idx:03d}", nome=f"Dormente {idx}",
                perfil="Dormente", subcategoria="Morador",
                vagas=1, tipo_veiculo=tipo, is_ev=False, ev_dependente=False,
                placa_danificada=False, usa_cartao_vaga=False,
                ingresso=m.inicio, saida=None, dormente=True, veiculos_ev=set(),
                carros_garagem=set(), viajante=False, modo_viagem=None))
            idx += 1
    # um dos dormentes de carro atrasa todo mês — e NUNCA é bloqueado,
    # porque o bloqueio acontece na cancela (seção 11.4)
    if p["segmentos.dormente.um_deles_atrasa_sempre"]:
        for c in clientes:
            if c["dormente"] and c["tipo_veiculo"] == "Carro":
                c["atrasa_sempre"] = True
                break

    # ---------------- seção 38: empresa de logística ----------------
    L = "segmentos.locacao_de_espaco"
    logistica = dict(
        cliente_id="LOG-001", nome="Empresa de Logística",
        perfil="Locacao", subcategoria="Locação de Espaço",
        vagas=p[f"{L}.motos"], tipo_veiculo="Moto", is_ev=False, ev_dependente=False,
        placa_danificada=False, usa_cartao_vaga=False,
        ingresso=m.inicio, saida=p.data(f"{L}.presente_ate"),
        dormente=False, carros_garagem=set(), viajante=False, modo_viagem=None,
        veiculos_ev=set(), mensalidade_fixa=float(p[f"{L}.valor_boleto"]))
    clientes.append(logistica)

    # ---------------- placa danificada (seção 23: 1-2 casos) ----------------
    n_dan = p["base_clientes.carros_com_placa_danificada"]
    for perfil in ("Trabalhador", "Morador"):
        carros = [c for c in clientes if c["perfil"] == perfil and c["tipo_veiculo"] == "Carro"]
        for c in random.sample(carros, min(n_dan, len(carros))):
            c["placa_danificada"] = True

    # ---------------- placas, veículos e mensalidade ----------------
    for c in clientes:
        prefixo = {"Trabalhador": "MEN", "Morador": "MEN", "Dormente": "DOR",
                   "Locacao": "LOG"}[c["perfil"]]
        if c["tipo_veiculo"] == "Moto":
            prefixo = "MOT" if c["perfil"] != "Locacao" else "LOG"
        c["placas"] = [m.placa(prefixo) for _ in range(c["vagas"])]
        c["lpr"] = (c["tipo_veiculo"] == "Carro" and not c["placa_danificada"]
                    and c["perfil"] != "Locacao")
        c["mensalidade"] = c.get("mensalidade_fixa") or m.mensalidade(c["vagas"], c["tipo_veiculo"])

    return clientes, logistica


def veiculo_id(cliente, v):
    """O que o sistema sabe identificar: a placa lida, ou o código do cartão.

    ⚠ Para a empresa de logística (seção 38) o cartão é fixo por MOTOBOY, mas
    cadastrado só com os dados da empresa — o ID é estável, mas identifica uma
    PESSOA, não um veículo.
    """
    if cliente["lpr"]:
        return cliente["placas"][v]
    return f"CARD-{cliente['cliente_id']}-{v+1}"
