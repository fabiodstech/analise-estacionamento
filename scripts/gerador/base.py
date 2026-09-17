"""v13 — camada de tarifas, calendário e cadastro. Zero número literal.

Todo valor vem de parametros.yaml via `params.Parametros`. Se faltar, quebra.
"""
import math
import random
from datetime import datetime, timedelta

import numpy as np


class Motor:
    """Estado compartilhado do gerador: parâmetros, calendário e log."""

    COLS = ["ID", "Data", "Hora", "Terminal", "Sentido", "Placa", "Tipo_Veiculo",
            "Credencial", "Categoria_Principal", "Subcategoria", "Status", "Motivo",
            "Elevador", "Andar", "Vaga", "Usa_Cartao_Fisico", "Selos_Apresentados",
            "Local_Pagamento", "Forma_Pagamento", "KWh_Consumido", "Valor_Recarga_EV",
            "Valor_Cobrado_Total", "Cliente_ID", "Veiculo_ID"]
    # v13: 'Regra_Acesso' removida — tinha valor único desde o v10 (asserção
    # colunas_constantes).

    def __init__(self, p):
        self.p = p
        seed = p["meta.seed"]
        random.seed(seed)
        np.random.seed(seed)

        self.inicio = p.dt("meta.janela.inicio")
        self.fim = p.dt("meta.janela.fim")
        self.dias = (self.fim - self.inicio).days
        self.marco = p.data("marco_modernizacao.data")
        self.feriados = p.feriados()

        self.logs = []
        self._id = 86000
        self._placas = set()
        self._tickets = set()

    # ---------- calendário ----------
    def tipo_de_dia(self, d):
        if d.date() in self.feriados:
            return "feriado"
        return {5: "sabado", 6: "domingo"}.get(d.weekday(), "dia_util")

    def regime(self, d):
        """'nova' a partir do marco de modernização, 'antiga' antes."""
        dd = d.date() if isinstance(d, datetime) else d
        return "nova" if dd >= self.marco else "antiga"

    def dia_util_seguinte(self, d, n):
        contados = 0
        while contados < n:
            d += timedelta(days=1)
            if d.weekday() < 5 and d.date() not in self.feriados:
                contados += 1
        return d.date()

    # ---------- identificadores únicos ----------
    def placa(self, prefixo):
        while True:
            v = f"{prefixo}{random.randint(100, 999)}"
            if v not in self._placas:
                self._placas.add(v)
                return v

    def ticket(self, prefixo, lo, hi):
        while True:
            v = f"{prefixo}{random.randint(lo, hi)}"
            if v not in self._tickets:
                self._tickets.add(v)
                return v

    # ---------- tarifas ----------
    def _tabela(self, tipo_veiculo, dt_saida):
        p, reg = self.p, self.regime(dt_saida)
        v = "carro" if tipo_veiculo == "Carro" else "moto"
        if reg == "nova":
            return p[f"precos.nova.{v}"]
        fds = dt_saida.weekday() >= 5 or dt_saida.date() in self.feriados
        return p[f"precos.antiga.{v}_{'fds' if fds else 'seg_sex'}"]

    def tarifa(self, minutos, tipo_veiculo, dt_saida):
        """Modelo da seção 29, idêntico nas duas tabelas."""
        t = self._tabela(tipo_veiculo, dt_saida)
        if minutos <= 30:
            return float(t["meia_hora"])
        if minutos <= 60:
            return float(t["uma_hora"])
        if minutos <= 12 * 60:
            excedentes = math.ceil((minutos - 60) / 60)
            return float(min(t["uma_hora"] + excedentes * t["hora_adicional"],
                             t["diaria_12h"]))
        return float(math.ceil(minutos / (24 * 60)) * t["diaria_24h"])

    def desconto_selo(self, qtd, tipo_veiculo, dt_saida):
        """1 selo = valor de 1 hora da tabela vigente (seção 29)."""
        return float(qtd * self._tabela(tipo_veiculo, dt_saida)["uma_hora"])

    def preco_selo(self, dt):
        p = self.p
        return float(p["selo.preco_venda_apos"] if self.regime(dt) == "nova"
                     else p["selo.preco_venda_antes"])

    def tarifa_ev(self, d):
        """Reajuste trimestral desde a instalação — seção 6.4b."""
        tabela = self.p["recarga_ev.tarifa_por_kwh"]
        chave = f"{d.year}-{d.month:02d}"
        if chave in tabela:
            return float(tabela[chave])
        anteriores = sorted(k for k in tabela if isinstance(k, str) and k < chave)
        if not anteriores:
            raise KeyError(f"sem tarifa de recarga declarada para {chave}")
        return float(tabela[anteriores[-1]])

    def mensalidade(self, vagas, tipo_veiculo):
        """Seção 29.1. Moto: 180 legado ou 200 atual. Carro: 310 com desconto
        discricionário que cresce com o número de vagas."""
        p = self.p
        if tipo_veiculo == "Moto":
            legado = p["precos.mensalidade.moto.valor_legado"]
            atual = p["precos.mensalidade.moto.valor_atual"]
            return float(random.choice([legado, atual]) * vagas)
        tabela = float(p["precos.mensalidade.carro.valor_tabela"])
        desc = p["precos.mensalidade.carro.desconto_medido_v12"]
        chave = {1: "1_vaga", 2: "2_vagas"}.get(vagas, "3_vagas")
        piso = float(p.faixa("precos.mensalidade.carro.faixa_praticada")[0])
        por_vaga = max(piso, round(tabela * (1 - float(desc[chave])), 0))
        return float(por_vaga * vagas)

    # ---------- cancelas ----------
    def terminal_saida(self, tipo_veiculo, is_carga, dt):
        p = self.p
        if tipo_veiculo == "Moto" or is_carga:
            return "Terminal 2 (Saída Subsolo)"   # seção 17: nunca pelo térreo
        hora = dt.hour + dt.minute / 60
        if dt.date() in self.feriados or dt.weekday() == 6:
            return "Terminal 2 (Saída Subsolo)"
        chave = "sabado" if dt.weekday() == 5 else "seg_sex"
        ini, fim = p.janela(f"cancelas.cancela_3.{chave}")
        return ("Terminal 3 (Saída Térreo)" if ini <= hora < fim
                else "Terminal 2 (Saída Subsolo)")

    @property
    def terminal_entrada(self):
        return "Terminal 1 (Entrada Subsolo)"

    # ---------- pagamento ----------
    def canal_e_forma(self, *, obrigatorio_caixa, valor_zerado_por_selo=False):
        """⚠ v13: sorteia a FORMA e DERIVA o canal — nunca os dois em paralelo.

        Foi o sorteio independente que produziu 'moto no Totem' (v10) e
        'PIX no Totem' (v12), 21 casos que os 12 checks não pegavam.
        """
        p = self.p
        if valor_zerado_por_selo:
            return "Caixa", "Selo (100% Abonado)"
        cartoes = list(p["pagamento.totem.formas_aceitas"])
        nomes = {"cartao_credito": "Cartão de Crédito", "cartao_debito": "Cartão de Débito"}
        if obrigatorio_caixa:
            forma = random.choice([nomes[c] for c in cartoes] + ["Dinheiro", "PIX"])
            return "Caixa", forma
        if random.random() < p["pagamento.chance_cartao_avulso"]:
            forma = random.choice([nomes[c] for c in cartoes])
            canal = "Totem" if random.random() < p["pagamento.chance_totem_dado_cartao"] else "Caixa"
            return canal, forma
        return "Caixa", random.choice(["Dinheiro", "PIX"])

    # ---------- recarga ----------
    def duracao_recarga(self, max_horas=None):
        p = self.p
        media = p["recarga_ev.duracao_h_media"]
        desvio = p["recarga_ev.duracao_h_desvio"]
        lo, hi = p.faixa("recarga_ev.duracao_h_limites")
        h = min(max(np.random.normal(media, desvio), lo), hi)
        return min(h, max_horas) if max_horas is not None else h

    def kwh(self, max_horas=None):
        lo, hi = self.p.faixa("recarga_ev.potencia_kw")
        return self.duracao_recarga(max_horas) * random.uniform(lo, hi)

    def chance_ev_do_mes(self, d):
        p = self.p
        fator = p["recarga_ev.fator_adocao_mes"].get(d.month, 1.0)
        return p["recarga_ev.chance_base"] * fator

    # ---------- escrita ----------
    def log(self, dt, terminal, sentido, placa, tipo_veiculo, credencial, categoria,
            subcategoria, status, motivo, elevador, andar, vaga, cartao, selos=0,
            local_pag="N/A", forma_pag="N/A", kwh=0.0, valor_ev=0.0, valor_total=0.0,
            cliente_id="N/A", veiculo_id="N/A"):
        self.logs.append([
            self._id, dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M:%S"), terminal, sentido,
            placa, tipo_veiculo, credencial, categoria, subcategoria, status, motivo,
            elevador, andar, vaga, cartao, selos, local_pag, forma_pag,
            round(kwh, 2), round(valor_ev, 2), round(valor_total, 2), cliente_id, veiculo_id])
        self._id += 1


def hora(dia0, hora_decimal):
    return dia0 + timedelta(hours=float(hora_decimal))
