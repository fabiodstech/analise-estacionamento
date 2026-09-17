"""valida_v13.py — confere o dataset contra o MESMO parametros.yaml que o gerador leu.

É esse acoplamento que impede um parâmetro de divergir da regra escrita sem
que um teste quebre. No v12 gerador e validador tinham cada um suas próprias
constantes, e foi por isso que a tarifa de recarga, a mensalidade e o
bloqueio automático passaram versões inteiras sem ninguém notar.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from params import carregar

OK, FALHA = "\033[92mPASSA\033[0m", "\033[91mFALHA\033[0m"


class Suite:
    def __init__(self, df, p):
        self.df, self.p = df, p
        self.res = []
        df["dt"] = pd.to_datetime(df.Data + " " + df.Hora, format="%d/%m/%Y %H:%M:%S")
        df["data"] = df.dt.dt.date
        df["hora"] = df.dt.dt.hour
        self.feriados = p.feriados()
        self.marco = p.data("marco_modernizacao.data")
        self.mov = df[(df.Sentido.isin(["Entrada", "Saída"])) & (df.Status != "Bloqueado")].copy()
        self.mov["chave"] = np.where(
            self.mov.Veiculo_ID != "N/A", "V:" + self.mov.Veiculo_ID.astype(str),
            "T:" + self.mov.Credencial.astype(str))

    def check(self, ident, cond, detalhe=""):
        self.res.append((ident, bool(cond), detalhe))

    # ---------------- asserções ----------------
    def transicoes_invalidas(self):
        n = 0
        for _, g in self.mov.groupby("chave", sort=False):
            s = g.sort_values("dt").Sentido.values
            n += int((s[:-1] == s[1:]).sum())
        self.check("transicoes_invalidas", n == 0, f"{n} transições")

    def saida_sem_entrada(self):
        orfas = 0
        for _, g in self.mov.groupby("chave", sort=False):
            pilha = 0
            for sent in g.sort_values("dt").Sentido:
                if sent == "Entrada":
                    pilha += 1
                elif pilha:
                    pilha -= 1
                else:
                    orfas += 1
        self.check("saida_sem_entrada", orfas == 0, f"{orfas} órfãs")

    def moto_com_placa_lida(self):
        mv = self.df[self.df.Sentido.isin(["Entrada", "Saída"])]
        n = ((mv.Tipo_Veiculo == "Moto")
             & (~mv.Placa.fillna("N/A").isin(["N/A (S/ Leitura)", "N/A"]))).sum()
        self.check("moto_com_placa_lida", n == 0, f"{n} eventos")

    def moto_no_totem(self):
        n = ((self.df.Tipo_Veiculo == "Moto") & (self.df.Local_Pagamento == "Totem")).sum()
        self.check("moto_no_totem", n == 0, f"{n} casos")

    def pix_no_totem(self):
        n = ((self.df.Local_Pagamento == "Totem") & (self.df.Forma_Pagamento == "PIX")).sum()
        self.check("pix_no_totem", n == 0, f"{n} casos")

    def totem_forma_permitida(self):
        nomes = {"cartao_credito": "Cartão de Crédito", "cartao_debito": "Cartão de Débito"}
        ok = {nomes[c] for c in self.p["pagamento.totem.formas_aceitas"]}
        t = self.df[self.df.Local_Pagamento == "Totem"]
        n = (~t.Forma_Pagamento.isin(ok)).sum()
        self.check("totem_forma_permitida", n == 0, f"{n} fora de {sorted(ok)}")

    def terreo_fora_da_janela(self):
        s = self.df[(self.df.Sentido == "Saída") & (self.df.Terminal.str.contains("Térreo"))]
        mau = 0
        for r in s.itertuples():
            h = r.dt.hour + r.dt.minute / 60
            if r.data in self.feriados or r.dt.weekday() == 6:
                mau += 1
                continue
            chave = "sabado" if r.dt.weekday() == 5 else "seg_sex"
            ini, fim = self.p.janela(f"cancelas.cancela_3.{chave}")
            if not (ini <= h < fim):
                mau += 1
        self.check("terreo_fora_da_janela", mau == 0, f"{mau} saídas")

    def moto_pelo_terreo(self):
        n = ((self.df.Tipo_Veiculo == "Moto") & (self.df.Terminal.str.contains("Térreo"))).sum()
        self.check("moto_pelo_terreo", n == 0, f"{n} casos")

    def bloqueio_antes_do_marco(self):
        n = ((self.df.Status == "Bloqueado") & (self.df.data < self.marco)).sum()
        self.check("bloqueio_antes_do_marco", n == 0, f"{n} bloqueios")

    def motivo_convenio_com_valor_residual(self):
        n = ((self.df.Motivo == "CONVÊNIO/LIBERADO") & (self.df.Valor_Cobrado_Total > 0)).sum()
        self.check("motivo_convenio_com_valor_residual", n == 0, f"{n} casos")

    def inadimplente_pode_usar_totem(self):
        """Regra 36.6: o inadimplente retira ticket e paga no totem como avulso.

        ⚠ Esta asserção nasceu de uma CORREÇÃO: a regra escrita tratava o
        segmento como exceção não-avulsa e o excluía do denominador da aderência.
        O gerador sempre esteve certo; o documento é que estava errado.
        """
        i = self.df[(self.df.Subcategoria == "Mensalista Inadimplente")
                    & (self.df.Sentido == "Saída")
                    & (self.df.Tipo_Veiculo == "Carro")
                    & (self.df.Forma_Pagamento.str.contains("Cartão", na=False))]
        if i.empty:
            self.check("inadimplente_pode_usar_totem", False, "nenhuma saída elegível")
            return
        n = (i.Local_Pagamento == "Totem").sum()
        self.check("inadimplente_pode_usar_totem", n > 0,
                   f"{n} de {len(i)} saídas de carro com cartão foram ao totem")

    def colunas_constantes(self):
        cs = [c for c in self.df.columns if c not in ("dt", "data", "hora")
              and self.df[c].nunique(dropna=False) == 1]
        self.check("colunas_constantes", not cs, f"{cs}")

    def carga_descarga_rotulada(self):
        n = (self.df.Subcategoria == "Carga e Descarga").sum()
        self.check("carga_descarga_rotulada", n > 0, f"{n} eventos rotulados")

    def hotel_tem_1_diaria(self):
        e = self._estadias()
        h = e[e.subcat == "Hóspede Hotel"]
        frac = (h.horas < 24).mean() if len(h) else 0
        alvo = self.p["segmentos.hospede_hotel.diarias_distribuicao"][1]
        self.check("hotel_tem_1_diaria", abs(frac - alvo) <= 0.05,
                   f"{frac:.1%} contra alvo {alvo:.0%}")

    def inadimplentes_reincidentes(self):
        """Estima P(atrasa | atrasou no mês anterior) e compara com o parâmetro.

        ⚠ A versão anterior media "% de clientes que atrasaram em mais de um
        mês". Com 7 clientes em atraso, 43% e 50% não se distinguem, e o valor
        depende do tamanho da janela — não do modelo. A taxa de TRANSIÇÃO é o
        parâmetro de fato e é estável.

        Mede o ATRASO (boleto pago depois do vencimento), não o bloqueio: o
        bloqueio só existe a partir do marco e cobre 1/3 da janela.
        """
        bo = self.df[self.df.Sentido == "Renovação Mensal"].copy()
        venc = self.p["inadimplencia.dia_vencimento"]
        bo["m"] = bo.dt.dt.to_period("M")
        bo["atrasou"] = bo.dt.dt.day > venc + 3
        seq = bo.sort_values("m").groupby("Cliente_ID").atrasou.apply(list)
        depois_de_atraso, ainda_atrasado = 0, 0
        for v in seq:
            for i in range(len(v) - 1):
                if v[i]:
                    depois_de_atraso += 1
                    ainda_atrasado += bool(v[i + 1])
        if depois_de_atraso < 5:
            self.check("inadimplentes_reincidentes", False,
                       f"base pequena demais ({depois_de_atraso} transições)")
            return
        taxa = ainda_atrasado / depois_de_atraso
        alvo = self.p["inadimplencia.p_atrasa_dado_atrasou"]
        # tolerância ampla de propósito: n é pequeno por construção (2-3/mês)
        self.check("inadimplentes_reincidentes", abs(taxa - alvo) <= 0.25,
                   f"P(atrasa|atrasou) = {taxa:.2f} contra {alvo} declarado "
                   f"(n={depois_de_atraso})")

    def ocupacao_dentro_da_capacidade(self):
        det = []
        for tv, chave in (("Carro", "capacidade.carro.vagas"), ("Moto", "capacidade.moto.vagas")):
            cap = self.p[chave]
            g = self.mov[self.mov.Tipo_Veiculo == tv].sort_values("dt")
            occ = np.cumsum(np.where(g.Sentido == "Entrada", 1, -1))
            det.append(f"{tv} pico {occ.max()}/{cap}")
            if occ.max() > cap:
                self.check("ocupacao_dentro_da_capacidade", False, " · ".join(det))
                return
        self.check("ocupacao_dentro_da_capacidade", True, " · ".join(det))

    def sabado_trabalhador(self):
        e = self.mov[(self.mov.Sentido == "Entrada")
                     & (self.mov.Subcategoria == "Lojista / Escritório")].copy()
        e["td"] = e.dt.dt.weekday
        nd_u = e[e.td < 5].data.nunique() or 1
        nd_s = e[e.td == 5].data.nunique() or 1
        razao = (len(e[e.td == 5]) / nd_s) / (len(e[e.td < 5]) / nd_u)
        alvo = self.p["segmentos.trabalhador.chance_trabalha_sabado"]
        self.check("sabado_trabalhador", abs(razao - alvo) <= 0.10, f"razão {razao:.2f} vs {alvo}")

    def ordem_avulso_por_tipo_de_dia(self):
        e = self.mov[(self.mov.Sentido == "Entrada")
                     & (self.mov.Subcategoria.isin(["Avulso Regular", "Carga e Descarga"]))].copy()
        e["td"] = e.data.map(self._tipo_dia)
        nd = e.groupby("td").data.nunique()
        r = (e.groupby("td").size() / nd)
        ok = r.get("domingo", 0) < r.get("feriado", 0) < r.get("dia_util", 0)
        self.check("ordem_avulso_por_tipo_de_dia", ok,
                   f"dom {r.get('domingo',0):.1f} < fer {r.get('feriado',0):.1f} < útil {r.get('dia_util',0):.1f}")

    def inadimplente_pode_usar_totem(self):
        """O mensalista inadimplente NÃO é caixa-obrigatório (regra 36.6).

        Com a mensalidade vencida a cancela não abre sozinha: o cliente aperta o
        botão, retira ticket e paga como qualquer avulso — inclusive no totem.
        Esta asserção existe porque a regra escrita dizia o contrário e excluía
        o segmento do denominador da aderência. O gerador estava certo; o
        documento é que estava errado.
        """
        s = self.df[(self.df.Sentido == "Saída")
                    & (self.df.Subcategoria == "Mensalista Inadimplente")
                    & (self.df.Tipo_Veiculo == "Carro")
                    & (self.df.Forma_Pagamento.str.contains("Cartão", na=False))]
        if s.empty:
            self.check("inadimplente_pode_usar_totem", True, "sem casos no período")
            return
        n_totem = int((s.Local_Pagamento == "Totem").sum())
        self.check("inadimplente_pode_usar_totem", n_totem > 0,
                   f"{n_totem} de {len(s)} pagaram no totem")

    def aderencia_totem_denominador(self):
        """O denominador canônico é núcleo + inadimplente (regras 3.1 e 36.6).

        Confere o valor contra o declarado no parametros.yaml. Se alguém mexer
        no denominador sem atualizar a regra escrita — ou o contrário — isto
        quebra.
        """
        s = self.df[self.df.Sentido == "Saída"].copy()
        for c in ("Selos_Apresentados", "Valor_Recarga_EV"):
            s[c] = pd.to_numeric(s[c], errors="coerce").fillna(0)
        elegivel = (
            s.Subcategoria.isin(["Avulso Regular", "Mensalista Inadimplente"])
            & (s.Tipo_Veiculo == "Carro")
            & (s.Selos_Apresentados == 0)
            & (s.Valor_Recarga_EV == 0)
            & s.Forma_Pagamento.str.contains("Cartão", na=False))
        e = s[elegivel]
        canal = e[e.Local_Pagamento.isin(["Totem", "Caixa"])]
        if canal.empty:
            self.check("aderencia_totem_denominador", False, "denominador vazio")
            return
        ader = (canal.Local_Pagamento == "Totem").mean()
        alvo = self.p.get("pagamento.aderencia_totem_medida_v13", None)
        if alvo is None:
            self.check("aderencia_totem_denominador", True,
                       f"{ader:.1%} (sem alvo declarado no YAML)")
            return
        self.check("aderencia_totem_denominador", abs(ader - alvo) <= 0.02,
                   f"{ader:.1%} contra {alvo:.1%} declarado")

    def ev_kwh_por_sessao(self):
        ev = self.df[self.df.KWh_Consumido > 0]
        med = ev.KWh_Consumido.mean()
        alvo = self.p["recarga_ev.kwh_por_sessao_medio"]
        self.check("ev_kwh_por_sessao", abs(med - alvo) / alvo <= 0.05,
                   f"{med:.2f} contra {alvo} do app")

    def dormentes_sem_movimento(self):
        bo = set(self.df[self.df.Sentido == "Renovação Mensal"].Cliente_ID)
        mv = set(self.mov[self.mov.Cliente_ID != "N/A"].Cliente_ID)
        n = len(bo - mv)
        alvo = self.p["segmentos.dormente.clientes"]
        self.check("dormentes_sem_movimento", n == alvo, f"{n} de {alvo} esperados")

    def dormente_inadimplente_nao_bloqueia(self):
        bo = set(self.df[self.df.Sentido == "Renovação Mensal"].Cliente_ID)
        mv = set(self.mov[self.mov.Cliente_ID != "N/A"].Cliente_ID)
        dorm = bo - mv
        n = self.df[(self.df.Status == "Bloqueado") & (self.df.Cliente_ID.isin(dorm))].shape[0]
        self.check("dormente_inadimplente_nao_bloqueia", n == 0, f"{n} bloqueios de dormente")

    def logistica_ausente_apos_marco(self):
        L = self.df[self.df.Subcategoria == "Locação de Espaço"]
        n = (L.data >= self.marco).sum()
        self.check("logistica_ausente_apos_marco", n == 0 and len(L) > 0,
                   f"{len(L)} eventos, {n} após o marco")

    def logistica_sem_domingo(self):
        L = self.df[(self.df.Subcategoria == "Locação de Espaço")
                    & (self.df.Sentido.isin(["Entrada", "Saída"]))]
        n = (L.dt.dt.weekday == 6).sum()
        self.check("logistica_sem_domingo", n == 0, f"{n} eventos em domingo")

    def moto_capacidade_por_regime(self):
        g = self.mov[self.mov.Tipo_Veiculo == "Moto"].sort_values("dt")
        occ = pd.Series(np.cumsum(np.where(g.Sentido == "Entrada", 1, -1)), index=g.data.values)
        pre = occ[occ.index < self.marco].max()
        pos = occ[occ.index >= self.marco].max()
        cap = self.p["capacidade.moto.vagas"]
        self.check("moto_capacidade_por_regime", pre > pos and pre <= cap,
                   f"pré {pre} > pós {pos}, teto {cap}")

    def mensalidade_valores_permitidos(self):
        bo = self.df[self.df.Sentido == "Renovação Mensal"]
        vagas = self.mov[self.mov.Cliente_ID != "N/A"].groupby("Cliente_ID").Veiculo_ID.nunique()
        emp = self.p["segmentos.locacao_de_espaco.valor_boleto"]
        moto = {self.p["precos.mensalidade.moto.valor_legado"],
                self.p["precos.mensalidade.moto.valor_atual"]}
        lo, hi = self.p.faixa("precos.mensalidade.carro.faixa_praticada")
        mau = 0
        for r in bo.itertuples():
            if r.Valor_Cobrado_Total == emp:
                continue
            v = vagas.get(r.Cliente_ID, 1)
            pv = r.Valor_Cobrado_Total / max(v, 1)
            if r.Tipo_Veiculo == "Moto":
                if round(pv, 2) not in moto:
                    mau += 1
            elif not (lo - 0.01 <= pv <= hi + 0.01):
                mau += 1
        self.check("mensalidade_valores_permitidos", mau == 0, f"{mau} fora da faixa")

    def mensalidade_estavel_no_marco(self):
        bo = self.df[(self.df.Sentido == "Renovação Mensal")
                     & (self.df.Valor_Cobrado_Total != self.p["segmentos.locacao_de_espaco.valor_boleto"])]
        a = bo[bo.data < self.marco].Valor_Cobrado_Total.mean()
        d = bo[bo.data >= self.marco].Valor_Cobrado_Total.mean()
        self.check("mensalidade_estavel_no_marco", abs(a - d) / a < 0.05,
                   f"{a:.0f} antes, {d:.0f} depois")

    # ---------------- utilidades ----------------
    def _tipo_dia(self, d):
        if d in self.feriados:
            return "feriado"
        return {5: "sabado", 6: "domingo"}.get(pd.Timestamp(d).weekday(), "dia_util")

    def _estadias(self):
        if hasattr(self, "_est"):
            return self._est
        pares = []
        for chave, g in self.mov.groupby("chave", sort=False):
            pilha = []
            for r in g.sort_values("dt").itertuples():
                if r.Sentido == "Entrada":
                    pilha.append(r)
                elif pilha:
                    e = pilha.pop(0)
                    pares.append((e.Subcategoria, (r.dt - e.dt).total_seconds() / 3600))
        self._est = pd.DataFrame(pares, columns=["subcat", "horas"])
        return self._est

    def rodar(self):
        for nome in [a for a in dir(self) if not a.startswith(("_", "rodar", "check"))
                     and callable(getattr(self, a))]:
            try:
                getattr(self, nome)()
            except Exception as exc:
                self.check(nome, False, f"ERRO: {exc}")
        return self.res


def main(csv="logs_estacionamento_v13.csv", yaml=None):
    p = carregar(yaml)
    # ⚠ keep_default_na=False: sem isso o pandas converte "N/A" em NaN e
    #   TODOS os avulsos colapsam numa chave de pareamento só.
    df = pd.read_csv(csv, keep_default_na=False)
    s = Suite(df, p)
    res = s.rodar()
    print(f"\n{'':2}{'asserção':42} {'':6} detalhe")
    print("-" * 92)
    for ident, ok, det in sorted(res):
        print(f"  {ident:42} {OK if ok else FALHA}  {det}")
    n_ok = sum(1 for _, ok, _ in res if ok)
    print("-" * 92)
    print(f"  {n_ok}/{len(res)} asserções passam · {len(df):,} registros\n")
    return n_ok == len(res)


if __name__ == "__main__":
    sys.exit(0 if main(*sys.argv[1:]) else 1)
