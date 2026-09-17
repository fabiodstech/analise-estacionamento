"""Fluxos diários do v13. Nenhum número literal — tudo vem do YAML."""
import random
from datetime import timedelta

import numpy as np

from .base import hora
from .clientes import veiculo_id


# ============================================================================
# FATURAMENTO E INADIMPLÊNCIA — seção 36
# ============================================================================
class Faturamento:
    """⚠ v13: cadeia de Markov de dois estados no lugar do sorteio independente.

    O v12 sorteava 5%/mês por cliente, sem memória: dava a taxa mensal certa
    (3,3/mês) e um acumulado absurdo — 25% da base no semestre, com ZERO
    reincidentes. Fabio: atrasam 2-3 por mês, e geralmente são os mesmos.
    """

    def __init__(self, motor, clientes):
        self.m, self.p, self.clientes = motor, motor.p, clientes
        self.atrasou = {c["cliente_id"]: False for c in clientes}
        self.status = {}
        self.mes_faturado = None
        self.limite_bloqueio = None

    def virada_de_mes(self, d):
        p, m = self.p, self.m
        chave = d.strftime("%Y-%m")
        if chave == self.mes_faturado:
            return
        self.mes_faturado = chave
        venc = d.replace(day=p["inadimplencia.dia_vencimento"])
        self.limite_bloqueio = m.dia_util_seguinte(
            venc, p["inadimplencia.bloqueio_dias_uteis_apos_vencimento"])

        p_em_dia = p["inadimplencia.p_atrasa_dado_em_dia"]
        p_atrasou = p["inadimplencia.p_atrasa_dado_atrasou"]
        lo, hi = p.faixa("inadimplencia.dias_ate_regularizar_apos_bloqueio")

        self.status = {}
        for c in self.clientes:
            if d.date() < c["ingresso"].date():
                continue
            cid = c["cliente_id"]
            if c.get("atrasa_sempre"):
                atrasa = True                      # dormente crônico (seção 11.4)
            else:
                atrasa = random.random() < (p_atrasou if self.atrasou[cid] else p_em_dia)
            self.atrasou[cid] = atrasa
            if atrasa:
                pago = self.limite_bloqueio + timedelta(days=random.randint(lo, hi))
            else:
                pago = d.replace(day=random.randint(5, p["inadimplencia.dia_vencimento"])).date()
            self.status[cid] = {"pago_em": pago, "bloqueado": False}

    def atualiza_e_emite(self, d, dia0):
        """Atualiza o estado de bloqueio e emite os boletos pagos hoje."""
        m, p = self.m, self.p
        marco = p.data("inadimplencia.bloqueio_automatico_a_partir_de")
        for c in self.clientes:
            if d.date() < c["ingresso"].date():
                continue
            if c.get("saida") and d.date() > c["saida"]:
                continue
            st = self.status.get(c["cliente_id"])
            if st is None:
                continue
            atrasado = self.limite_bloqueio < d.date() < st["pago_em"]
            # ⚠ o bloqueio automático SÓ existe a partir do marco (seção 36.2).
            #   Antes disso o boleto corria com juros e o cliente entrava normal.
            st["bloqueado"] = atrasado and d.date() >= marco
            if d.date() == st["pago_em"]:
                m.log(hora(dia0, 8), "Integração ERP", "Renovação Mensal", "N/A",
                      c["tipo_veiculo"], "Boleto ERP", "Mensalista", c["subcategoria"],
                      "Faturado", "BOLETO PAGO", "N/A", "N/A", "N/A", "Não",
                      local_pag="ERP", forma_pag="Boleto",
                      valor_total=c["mensalidade"], cliente_id=c["cliente_id"])

    def bloqueado(self, cliente):
        st = self.status.get(cliente["cliente_id"])
        return bool(st and st["bloqueado"])


# ============================================================================
# AVULSO — seções 13 e 30
# ============================================================================
def _hora_de_entrada(p, tipo_dia):
    cfg = p[f"segmentos.avulso_regular.hora_entrada.{tipo_dia}"]
    lo, hi = cfg["limites"]
    # ⚠ v13: cauda fora do horário comercial (seção 13) — visitantes de
    #   moradores do entorno e prestadores de serviço. O v12 tinha corte duro.
    if random.random() < p["segmentos.avulso_regular.cauda_fora_do_horario_fracao"]:
        return random.choice([random.uniform(5, lo), random.uniform(hi, 23.5)])
    if cfg["tipo"] == "normal":
        return max(lo, min(hi, np.random.normal(cfg["media"], cfg["desvio"])))
    return random.uniform(lo, hi)


def avulsos(motor, dia0, tipo_dia, chance_ev):
    m, p = motor, motor.p
    lo, hi = p.faixa(f"segmentos.avulso_regular.entradas_por_dia.{tipo_dia}")
    for _ in range(random.randint(lo, hi)):
        entrada = hora(dia0, _hora_de_entrada(p, tipo_dia))
        tipo_v = ("Carro" if random.random() < p["segmentos.avulso_regular.chance_carro"]
                  else "Moto")
        is_carga = random.random() < p["segmentos.carga_descarga.fracao_dos_avulsos"]
        # ⚠ v13: Carga e Descarga ganha SUBCATEGORIA PRÓPRIA (seção 30).
        #   No v12 ficava escondido dentro de Avulso Regular e só era
        #   identificável por permanência + cancela.
        subcat = "Carga e Descarga" if is_carga else "Avulso Regular"

        s_lo, s_hi = p.faixa("segmentos.avulso_regular.selos_por_uso")
        selos = (random.randint(s_lo, s_hi)
                 if (not is_carga and random.random() < p["segmentos.avulso_regular.chance_selo"])
                 else 0)
        ticket = m.ticket("Ticket-", 10000, 999999)

        if tipo_v == "Moto":
            elevador, andar, vaga, cartao = "Subsolo", "N/A", "N/A", "Não"
        elif is_carga:
            elevador, andar, vaga, cartao = "Não Utilizado (Pátio)", "Pátio/Térreo", "Sem Vaga", "Não"
        else:
            elevador, andar, vaga, cartao = "Não Registrado", "Manual", "Manual", "Sim"

        if tipo_v == "Moto":
            placa = "N/A (S/ Leitura)"
        else:
            placa = ("N/A (S/ Leitura)"
                     if random.random() < p["identificacao.chance_carro_placa_danificada"]
                     else f"XYZ{random.randint(1000, 9999)}")

        m.log(entrada, m.terminal_entrada, "Entrada", placa, tipo_v, ticket, "Avulso",
              subcat, "Liberado", "TICKET EMITIDO", elevador, andar, vaga, cartao)

        if is_carga:
            c_lo, c_hi = p.faixa("segmentos.carga_descarga.permanencia_minutos")
            minutos = random.randint(c_lo, c_hi)
        else:
            n = p["segmentos.avulso_regular.permanencia_normal"]
            minutos = max(n["minimo_min"], abs(np.random.normal(n["media_min"], n["desvio_min"])))
        saida = entrada + timedelta(minutes=minutos)

        valor = m.tarifa(minutos, tipo_v, saida)
        if selos:
            valor = max(0.0, valor - m.desconto_selo(selos, tipo_v, saida))
        if is_carga and random.random() < p["segmentos.carga_descarga.aderencia_operador"]:
            valor = float(p["precos.carga_descarga.tarifa_fixa"])

        kwh = valor_ev = 0.0
        if (tipo_v == "Carro" and minutos >= 60
                and random.random() < chance_ev * p["segmentos.avulso_regular.chance_recarga_ev"]):
            kwh = m.kwh(minutos / 60.0)
            valor_ev = kwh * m.tarifa_ev(saida)

        total = valor + valor_ev
        obriga_caixa = bool(selos or is_carga or valor_ev > 0 or tipo_v == "Moto")
        canal, forma = m.canal_e_forma(obrigatorio_caixa=obriga_caixa,
                                       valor_zerado_por_selo=(total == 0 and selos > 0))
        # ⚠ v13: Motivo derivado do VALOR FINAL, não do nº de selos.
        #   No v12 três saídas com selo mas valor residual saíam como
        #   CONVÊNIO/LIBERADO com valor > 0.
        motivo = "CONVÊNIO/LIBERADO" if total == 0 else "PAGO/LIBERADO"

        m.log(saida, m.terminal_saida(tipo_v, is_carga, saida), "Saída", placa, tipo_v,
              ticket, "Avulso", subcat, "Liberado", motivo, elevador, andar, vaga, cartao,
              selos=selos, local_pag=canal, forma_pag=forma, kwh=kwh, valor_ev=valor_ev,
              valor_total=total)


# ============================================================================
# HOTEL (Passe Livre) — seções 25 e 25.1
# ============================================================================
def hotel(motor, dia0, chance_ev):
    m, p = motor, motor.p
    lo, hi = p.faixa("segmentos.hospede_hotel.chegadas_por_dia")
    h_lo, h_hi = p.faixa("segmentos.hospede_hotel.hora_entrada")
    dist = p["segmentos.hospede_hotel.diarias_distribuicao"]
    # ⚠ v13: a distribuição vem do YAML e inclui hóspede de 1 DIÁRIA.
    #   O v12 usava randint(2,4): média 3,0 e nenhum pernoite de uma noite,
    #   num segmento que é ~29% da receita.
    opcoes, pesos = [], []
    for k, v in dist.items():
        opcoes.append((5, 7) if isinstance(k, str) and "-" in k else (int(k), int(k)))
        pesos.append(v)

    for _ in range(random.randint(lo, hi)):
        entrada = hora(dia0, random.uniform(h_lo, h_hi))
        faixa = random.choices(opcoes, weights=pesos)[0]
        diarias = random.randint(*faixa)
        # ⚠ v13: a diária termina no CHECK-OUT do dia seguinte, não em 24h
        #   cheias. No v12 uma estadia de 1 diária durava 24h+, o que tornava
        #   impossível existir hóspede de uma noite — e ele é o caso mais comum.
        c_lo, c_hi = p.janela("segmentos.hospede_hotel.checkout")
        saida = hora(dia0 + timedelta(days=diarias), random.uniform(c_lo, c_hi))
        extras = 0
        if random.random() < p["segmentos.hospede_hotel.chance_late_checkout"]:
            e_lo, e_hi = p.faixa("segmentos.hospede_hotel.late_checkout_h")
            extras = int(random.uniform(e_lo, e_hi) * 60)
            saida += timedelta(minutes=extras)
        placa = ("N/A (S/ Leitura)"
                 if random.random() < p["identificacao.chance_carro_placa_danificada"]
                 else f"HOS{random.randint(1000, 9999)}")
        cred = m.ticket("Ticket-Hotel-", 1000, 99999)

        m.log(entrada, m.terminal_entrada, "Entrada", placa, "Carro", cred, "Avulso",
              "Hóspede Hotel", "Liberado", "PODE ENTRAR", "Não Registrado", "Manual",
              "Manual", "Sim")

        kwh = valor_ev = 0.0
        if random.random() < chance_ev * p["segmentos.hospede_hotel.chance_recarga_ev"]:
            kwh = m.kwh()
            valor_ev = kwh * m.tarifa_ev(saida)

        diaria = float(p["precos.hotel_diaria.apos_o_marco"] if m.regime(saida) == "nova"
                       else p["precos.hotel_diaria.antes_do_marco"])
        total = diarias * diaria + (m.tarifa(extras, "Carro", saida) if extras else 0.0) + valor_ev

        canal, forma = m.canal_e_forma(obrigatorio_caixa=True)   # Passe Livre: Caixa
        m.log(saida, m.terminal_saida("Carro", False, saida), "Saída", placa, "Carro",
              cred, "Avulso", "Hóspede Hotel", "Liberado", "PAGO/LIBERADO",
              "Não Registrado", "Manual", "Manual", "Sim", local_pag=canal,
              forma_pag=forma, kwh=kwh, valor_ev=valor_ev, valor_total=total)
