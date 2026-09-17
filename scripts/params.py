"""Carregador do parametros.yaml — fonte única de verdade numérica.

REGRA DE OURO: um número que não está no YAML não pode existir no gerador.

O acesso é feito por caminho pontilhado e **falha alto** se a chave não
existir. Isso é deliberado: se alguém acrescentar um comportamento novo no
gerador sem declarar o parâmetro, o gerador quebra na hora em vez de rodar
com uma constante escondida no código. Foi assim que a tarifa de recarga, a
mensalidade e a taxa de inadimplência ficaram anos sem documentação.
"""
import yaml
from datetime import datetime, date
from pathlib import Path

# procura o YAML ao lado do script ou em ../dados — assim funciona tanto no
# repositório publicado quanto durante o desenvolvimento.
def _localiza():
    for c in (Path(__file__).with_name("parametros.yaml"),
              Path(__file__).parent.parent / "dados" / "parametros.yaml"):
        if c.exists():
            return c
    return Path(__file__).with_name("parametros.yaml")


_CAMINHO_PADRAO = _localiza()


class ParametroAusente(KeyError):
    """Erro explícito: o gerador pediu um número que não está declarado."""


class Parametros:
    def __init__(self, caminho=None):
        self.caminho = Path(caminho or _CAMINHO_PADRAO)
        with open(self.caminho, encoding="utf-8") as fh:
            self._d = yaml.safe_load(fh)
        self._lidos = set()

    def get(self, caminho, default=...):
        """p.get('segmentos.morador.viagens_por_dia')"""
        no = self._d
        for parte in caminho.split("."):
            if not isinstance(no, dict) or parte not in no:
                if default is not ...:
                    return default
                raise ParametroAusente(
                    f"'{caminho}' não está em {self.caminho.name}. "
                    "Declare o parâmetro antes de usá-lo no gerador."
                )
            no = no[parte]
        self._lidos.add(caminho)
        return no

    __getitem__ = get

    def data(self, caminho):
        v = self.get(caminho)
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        return datetime.strptime(str(v), "%Y-%m-%d").date()

    def dt(self, caminho):
        d = self.data(caminho)
        return datetime(d.year, d.month, d.day)

    def faixa(self, caminho):
        """Devolve (lo, hi) de uma lista de dois elementos."""
        v = self.get(caminho)
        if not (isinstance(v, list) and len(v) == 2):
            raise ValueError(f"'{caminho}' deveria ser [lo, hi], é {v!r}")
        return v[0], v[1]

    def janela(self, caminho):
        """'07:00-09:30' -> (7.0, 9.5) em horas decimais."""
        ini, fim = str(self.get(caminho)).split("-")
        def _h(t):
            hh, mm = t.split(":")
            return int(hh) + int(mm) / 60
        return _h(ini), _h(fim)

    def feriados(self):
        return {self.data(f"feriados_2026.{i}") if False else
                (v.date() if isinstance(v, datetime) else v)
                for i, v in enumerate(self.get("feriados_2026"))}

    # ---- rastreabilidade ----
    def lidos(self):
        return sorted(self._lidos)

    def pendencias(self):
        return self.get("pendencias", [])

    def arbitrados(self):
        """Lista os blocos marcados como origem: arbitrado — os que precisam de fonte."""
        achados = []
        def _anda(no, prefixo=""):
            if isinstance(no, dict):
                for k, v in no.items():
                    if isinstance(k, str) and k.startswith("origem") and v == "arbitrado":
                        achados.append(prefixo.rstrip("."))
                    _anda(v, f"{prefixo}{k}.")
        _anda(self._d)
        return sorted(set(achados))


def carregar(caminho=None):
    return Parametros(caminho)


if __name__ == "__main__":
    p = carregar()
    print(f"{p.caminho.name} — {len(p._d)} blocos")
    print(f"versão alvo : {p['meta.versao_alvo']}")
    print(f"janela      : {p.data('meta.janela.inicio')} a {p.data('meta.janela.fim')}")
    print(f"marco       : {p.data('marco_modernizacao.data')}")
    print(f"feriados    : {len(p.get('feriados_2026'))}")
    print(f"asserções   : {len(p.get('asercoes'))}")
    print("\nblocos ainda ARBITRADOS (sem respaldo externo):")
    for a in p.arbitrados():
        print("  -", a or "(raiz)")
    print("\npendências declaradas:")
    for x in p.pendencias():
        print("  -", x[:100])
