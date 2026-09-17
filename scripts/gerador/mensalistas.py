"""Mensalistas e locação de espaço — v13."""
import random
from datetime import timedelta

from .base import hora
from .clientes import veiculo_id


class Mensalistas:
    def __init__(self, motor, clientes, faturamento):
        self.m, self.p = motor, motor.p
        self.clientes = clientes
        self.fat = faturamento
        self.dentro = {}
        self.ticket_aberto = {}
        self.viagem_ate = {}      # placa -> data de volta (seção 11.2b)
        self.freq_alta = set()    # clientes de alta frequência (seção 11.1b)
        vpd = self.p.faixa("segmentos.morador.viagens_por_dia")
        for c in clientes:
            if c["perfil"] == "Morador" and random.random() < 0.3:
                self.freq_alta.add(c["cliente_id"])
        self.max_viagens = vpd[1]

    # ---------------- eventos elementares ----------------
    def _ctx(self, c, v):
        tipo_v = c["tipo_veiculo"]
        cred = "Leitura de Placa (LPR)" if c["lpr"] else "Cartão de Acesso Físico"
        if tipo_v == "Carro":
            elevador, andar, vaga = "Não Registrado", "Manual", "Manual"
            cartao = "Sim" if c["usa_cartao_vaga"] else "Não"
        else:
            elevador, andar, vaga, cartao = "Subsolo", "N/A", "N/A", "Não"
        placa_log = c["placas"][v] if c["lpr"] else "N/A (S/ Leitura)"
        return dict(tipo_v=tipo_v, cred=cred, elevador=elevador, andar=andar,
                    vaga=vaga, cartao=cartao, placa_log=placa_log,
                    veic_id=veiculo_id(c, v), placa_real=c["placas"][v])

    def entrar(self, c, ctx, dt):
        m = self.m
        if self.fat.bloqueado(c):
            m.log(dt, m.terminal_entrada, "Entrada", ctx["placa_log"], ctx["tipo_v"],
                  ctx["cred"], "Mensalista", c["subcategoria"], "Bloqueado",
                  "INADIMPLÊNCIA ERP", ctx["elevador"], ctx["andar"], ctx["vaga"],
                  ctx["cartao"], cliente_id=c["cliente_id"], veiculo_id=ctx["veic_id"])
            dt_tk = dt + timedelta(seconds=15)
            tk = m.ticket("Ticket-", 10000, 999999)
            m.log(dt_tk, m.terminal_entrada, "Entrada", ctx["placa_log"], ctx["tipo_v"], tk,
                  "Avulso", "Mensalista Inadimplente", "Liberado", "TICKET EMITIDO",
                  ctx["elevador"], ctx["andar"], ctx["vaga"], ctx["cartao"],
                  cliente_id=c["cliente_id"], veiculo_id=ctx["veic_id"])
            self.ticket_aberto[ctx["placa_real"]] = (tk, dt_tk)
        else:
            m.log(dt, m.terminal_entrada, "Entrada", ctx["placa_log"], ctx["tipo_v"],
                  ctx["cred"], "Mensalista", c["subcategoria"], "Liberado", "PODE ENTRAR",
                  ctx["elevador"], ctx["andar"], ctx["vaga"], ctx["cartao"],
                  forma_pag="Plano Mensal", cliente_id=c["cliente_id"],
                  veiculo_id=ctx["veic_id"])

    def sair(self, c, ctx, dt):
        m = self.m
        term = m.terminal_saida(ctx["tipo_v"], False, dt)
        if ctx["placa_real"] in self.ticket_aberto:
            tk, dt_ent = self.ticket_aberto.pop(ctx["placa_real"])
            minutos = (dt - dt_ent).total_seconds() / 60
            # ⚠ v13: canal DERIVADO da forma. Era aqui que nascia o PIX no Totem
            #   (21 casos no v12) — canal e forma sorteados em paralelo.
            canal, forma = m.canal_e_forma(obrigatorio_caixa=(ctx["tipo_v"] == "Moto"))
            m.log(dt, term, "Saída", ctx["placa_log"], ctx["tipo_v"], tk, "Avulso",
                  "Mensalista Inadimplente", "Liberado", "PAGO/LIBERADO", ctx["elevador"],
                  ctx["andar"], ctx["vaga"], ctx["cartao"], local_pag=canal, forma_pag=forma,
                  valor_total=m.tarifa(minutos, ctx["tipo_v"], dt),
                  cliente_id=c["cliente_id"], veiculo_id=ctx["veic_id"])
        else:
            m.log(dt, term, "Saída", ctx["placa_log"], ctx["tipo_v"], ctx["cred"],
                  "Mensalista", c["subcategoria"], "Liberado", "SAÍDA LIBERADA",
                  ctx["elevador"], ctx["andar"], ctx["vaga"], ctx["cartao"],
                  forma_pag="Plano Mensal", cliente_id=c["cliente_id"],
                  veiculo_id=ctx["veic_id"])

    def recarregar(self, c, ctx, dt_saida):
        m = self.m
        kwh = m.kwh()
        val = kwh * m.tarifa_ev(dt_saida)
        canal, forma = m.canal_e_forma(obrigatorio_caixa=True)   # lançamento manual
        m.log(dt_saida - timedelta(minutes=15), "Caixa / Administração", "Serviço Avulso",
              ctx["placa_log"], ctx["tipo_v"], "Anotação WhatsApp", "Mensalista",
              c["subcategoria"], "Faturado", "LANÇAMENTO MANUAL - RECARGA EV",
              ctx["elevador"], ctx["andar"], ctx["vaga"], ctx["cartao"],
              local_pag=canal, forma_pag=forma, kwh=kwh, valor_ev=val, valor_total=val,
              cliente_id=c["cliente_id"], veiculo_id=ctx["veic_id"])

    # ---------------- o dia ----------------
    def dia(self, d, dia0, tipo_dia, chance_ev):
        p = self.p
        for c in self.clientes:
            if d.date() < c["ingresso"].date():
                continue
            if c["perfil"] in ("Dormente", "Locacao"):
                continue      # ⚠ dormente NUNCA passa pela cancela (seção 11.3)
            for v in range(c["vagas"]):
                ctx = self._ctx(c, v)
                # ⚠ 11.2a: o veículo-garagem do lojista fica parado em definitivo
                if v in c["carros_garagem"]:
                    if not self.dentro.get(ctx["placa_real"]):
                        self.entrar(c, ctx, hora(dia0, random.uniform(7, 9)))
                        self.dentro[ctx["placa_real"]] = True
                    continue
                recarga = (v in c["veiculos_ev"] and random.random() <
                           (p["recarga_ev.persona_ev_dependente_recargas_dia"]
                            if c["ev_dependente"] else chance_ev))
                if c["perfil"] == "Trabalhador":
                    self._trabalhador(c, ctx, dia0, tipo_dia, recarga)
                else:
                    self._morador(c, ctx, d, dia0, tipo_dia, recarga)

    def _trabalhador(self, c, ctx, dia0, tipo_dia, recarga):
        p = self.p
        if tipo_dia == "domingo":
            return
        if tipo_dia == "feriado":
            if random.random() >= p["segmentos.trabalhador.chance_trabalha_feriado"]:
                return
            j_in = p.janela("segmentos.trabalhador.feriado_chegada")
            j_out = p.janela("segmentos.trabalhador.feriado_saida")
        elif tipo_dia == "sabado":
            if random.random() >= p["segmentos.trabalhador.chance_trabalha_sabado"]:
                return
            j_in = p.janela("segmentos.trabalhador.sabado_chegada")
            j_out = p.janela("segmentos.trabalhador.sabado_saida")
        else:
            j_in = p.janela("segmentos.trabalhador.chegada")
            j_out = p.janela("segmentos.trabalhador.saida")
        t_in = hora(dia0, random.uniform(*j_in))
        t_out = hora(dia0, random.uniform(*j_out))
        self.entrar(c, ctx, t_in)
        if recarga:
            self.recarregar(c, ctx, t_out)
        self.sair(c, ctx, t_out)   # o carro passa a noite FORA

    def _morador(self, c, ctx, d, dia0, tipo_dia, recarga):
        p, placa = self.p, ctx["placa_real"]

        # ---- 11.2b: viagens ----
        volta = self.viagem_ate.get(placa)
        if volta and d.date() < volta:
            return                      # em viagem: nenhum evento
        if volta and d.date() >= volta:
            self.viagem_ate.pop(placa)
            if c["modo_viagem"] == "leva_o_carro":
                self.entrar(c, ctx, hora(dia0, random.uniform(*p.janela(
                    "segmentos.morador.chegada_inicial"))))
                self.dentro[placa] = True
            return
        if c["viajante"] and random.random() < _chance_viagem_diaria(p):
            lo, hi = p.faixa("segmentos.morador.duracao_viagem_dias")
            self.viagem_ate[placa] = d.date() + timedelta(days=random.randint(lo, hi))
            if c["modo_viagem"] == "leva_o_carro":
                # sai com o carro: a VAGA FICA VAZIA e não há mais eventos
                if self.dentro.get(placa):
                    self.sair(c, ctx, hora(dia0, random.uniform(6, 10)))
                    self.dentro[placa] = False
            # 'deixa_o_carro': vaga OCUPADA, zero eventos — assinatura oposta
            return

        limite = hora(dia0, p["segmentos.morador.limite_retorno_h"])
        cursor = dia0
        if not self.dentro.get(placa, False):
            chegada = hora(dia0, random.uniform(*p.janela("segmentos.morador.chegada_inicial")))
            self.entrar(c, ctx, chegada)
            self.dentro[placa] = True
            cursor = chegada + timedelta(hours=1)

        # ⚠ 11.1b: no fim de semana a MAIORIA reduz as saídas, mas quem tem
        #   alta frequência mantém. A redução é inversamente ligada à frequência.
        red = p["segmentos.morador.reducao_fim_de_semana"]
        fator = 1.0
        if tipo_dia in ("sabado", "domingo", "feriado"):
            fator = (red["alta_frequencia"] if c["cliente_id"] in self.freq_alta
                     else red["demais"])

        lo, hi = p.faixa("segmentos.morador.viagens_por_dia")
        n = random.randint(lo, hi)
        if random.random() > fator:
            n = max(0, n - 1)

        i_lo, i_hi = p.faixa("segmentos.morador.intervalo_entre_viagens_h")
        d_lo, d_hi = p.faixa("segmentos.morador.duracao_da_viagem_h")
        prim_lo, prim_hi = p.janela("segmentos.morador.primeira_saida")
        primeira = True
        for _ in range(n):
            base = (max(cursor, hora(dia0, random.uniform(prim_lo, prim_hi))) if primeira
                    else cursor + timedelta(hours=random.uniform(i_lo, i_hi)))
            primeira = False
            t_out = base
            t_in = t_out + timedelta(hours=random.uniform(d_lo, d_hi))
            if t_out >= limite:
                break
            if t_in > limite:
                t_in = limite - timedelta(minutes=random.randint(0, 45))
                if t_in <= t_out:
                    break
            if recarga:
                self.recarregar(c, ctx, t_out)
                recarga = False
            self.sair(c, ctx, t_out)
            self.entrar(c, ctx, t_in)
            cursor = t_in


def _intervalo(agenda, dur_lo, dur_hi):
    """Um afastamento inteiramente contido entre a chegada e a partida."""
    dur = random.randint(dur_lo, dur_hi) / 60
    ini = random.uniform(agenda["chegada"] + 0.25, max(agenda["chegada"] + 0.25,
                                                       agenda["partida"] - dur - 0.25))
    return (ini, ini + dur)


def _sem_sobreposicao(intervalos):
    """Descarta os que colidem: um veículo não pode sair duas vezes seguidas."""
    saida, fim_anterior = [], -1
    for ini, fim in sorted(intervalos):
        if ini > fim_anterior:
            saida.append((ini, fim))
            fim_anterior = fim
    return saida


def _chance_viagem_diaria(p):
    """viagens_por_semestre / dias da janela."""
    lo, hi = p.faixa("segmentos.morador.viagens_por_semestre")
    return ((lo + hi) / 2) / p["meta.janela.dias_plenos"]


# ============================================================================
# EMPRESA DE LOGÍSTICA — seção 38
# ============================================================================
class Logistica:
    """⚠ O ponto central (38.2): os motoboys usavam o cartão de acesso da MOTO
    para passar pela rampa com o CARRINHO DE CARGA, a pé. O log registra
    movimento de moto; a moto não sai do lugar.
    """

    def __init__(self, motor, cliente):
        self.m, self.p, self.c = motor, motor.p, cliente
        self.L = "segmentos.locacao_de_espaco"
        self.dentro = {}

    def _ctx(self, v):
        return dict(tipo_v="Moto", cred="Cartão de Acesso Físico",
                    elevador="Subsolo", andar="N/A", vaga="N/A", cartao="Não",
                    placa_log="N/A (S/ Leitura)", veic_id=veiculo_id(self.c, v))

    def _ev(self, dt, sentido, ctx, motivo, tipo_v=None):
        m = self.m
        term = (m.terminal_entrada if sentido == "Entrada"
                else m.terminal_saida(tipo_v or ctx["tipo_v"], True, dt))
        m.log(dt, term, sentido, ctx["placa_log"], tipo_v or ctx["tipo_v"], ctx["cred"],
              "Mensalista", "Locação de Espaço", "Liberado", motivo, ctx["elevador"],
              ctx["andar"], ctx["vaga"], ctx["cartao"], forma_pag="Plano Mensal",
              cliente_id=self.c["cliente_id"], veiculo_id=ctx["veic_id"])

    def dia(self, d, dia0, tipo_dia):
        """⚠ Constrói uma LINHA DO TEMPO por cartão e só depois escreve.

        As passagens de carrinho (movimento fantasma) precisam cair DENTRO da
        janela em que a moto daquele cartão está estacionada — senão o log
        registra saída de um veículo que ainda não chegou, e a máquina de
        estado por Veiculo_ID quebra.
        """
        p, m = self.p, self.m
        if d.date() > self.c["saida"]:
            return                        # saiu em 01/06 (recusou o reajuste)
        if tipo_dia == "domingo":
            return                        # opera de segunda a sábado
        ativos = self.c["vagas"]
        if tipo_dia in ("sabado", "feriado"):
            ativos = int(round(ativos * p[f"{self.L}.atividade_sabado"]))
        j_lo, j_hi = p.janela(f"{self.L}.janela_principal")

        # --- linha do tempo de cada motoboy: chegada, ausências, partida ---
        agenda = {}
        for v in range(ativos):
            chegada = random.uniform(j_lo - 2, j_lo + 1)
            partida = random.uniform(j_hi, j_hi + 3)
            agenda[v] = dict(chegada=chegada, partida=partida, ausencias=[])

        # voltas REAIS de moto — poucos motoboys, 2 a 3 por dia
        lo, hi = p.faixa(f"{self.L}.voltas_reais_por_moto")
        for v in range(min(p[f"{self.L}.motos_com_voltas_reais"], ativos)):
            for _ in range(random.randint(lo, hi)):
                agenda[v]["ausencias"].append(_intervalo(agenda[v], 20, 60))

        # --- MOVIMENTO FANTASMA (38.2): pedestre com carrinho ---
        # 5 carrinhos alternados entre os motoboys. Cada passagem usa o cartão
        # de uma moto QUE CONTINUA ESTACIONADA. Como os carrinhos rodam entre
        # todos, o fantasma se espalha e nenhum cartão fica anômalo sozinho.
        carrinhos = p[f"{self.L}.carrinhos_de_carga"]
        voltas = p[f"{self.L}.voltas_por_carrinho_por_dia"]
        if tipo_dia in ("sabado", "feriado"):
            voltas = max(1, int(round(voltas * p[f"{self.L}.atividade_sabado"])))
        for _ in range(carrinhos * voltas):
            v = random.randrange(ativos)
            agenda[v]["ausencias"].append(_intervalo(agenda[v], 15, 45))

        for v, ag in agenda.items():
            ctx = self._ctx(v)
            self._ev(hora(dia0, ag["chegada"]), "Entrada", ctx, "PODE ENTRAR")
            for t_out, t_in in _sem_sobreposicao(ag["ausencias"]):
                self._ev(hora(dia0, t_out), "Saída", ctx, "SAÍDA LIBERADA")
                self._ev(hora(dia0, t_in), "Entrada", ctx, "PODE ENTRAR")
            self._ev(hora(dia0, ag["partida"]), "Saída", ctx, "SAÍDA LIBERADA")

        # --- Kangoo: vaga de carro normal, com elevador e manobrista ---
        k = p[f"{self.L}.carro"]
        ctx_k = dict(tipo_v="Carro", cred="Cartão de Acesso Físico",
                     elevador="Não Registrado", andar="Manual", vaga="Manual",
                     cartao="Sim", placa_log="N/A (S/ Leitura)",
                     veic_id=f"CARD-{self.c['cliente_id']}-KANGOO")
        if not self.dentro.get("kangoo"):
            self._ev(hora(dia0, random.uniform(j_lo - 2, j_lo)), "Entrada", ctx_k,
                     "PODE ENTRAR", tipo_v="Carro")
            self.dentro["kangoo"] = True
        lo, hi = p.faixa(f"{self.L}.carro.coletas_por_dia")
        jan = dict(chegada=j_lo, partida=j_hi + 2)
        coletas = [_intervalo(jan, 45, 120) for _ in range(random.randint(lo, hi))]
        for t_out, t_in in _sem_sobreposicao(coletas):
            self._ev(hora(dia0, t_out), "Saída", ctx_k, "SAÍDA LIBERADA", tipo_v="Carro")
            self._ev(hora(dia0, t_in), "Entrada", ctx_k, "PODE ENTRAR", tipo_v="Carro")
        if d.date() == self.c["saida"]:
            self._ev(hora(dia0, 20), "Saída", ctx_k, "SAÍDA LIBERADA", tipo_v="Carro")
            self.dentro["kangoo"] = False
