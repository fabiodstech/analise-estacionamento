# ⚠️ Antes de copiar arquivos para cá

O `docs/regras_de_negocio.md` desta pasta é a **versão pública anonimizada**.

Se você copiar por cima a versão de trabalho, **o nome do estabelecimento, o endereço
e os hotéis conveniados voltam** — isso já aconteceu uma vez.

## O que precisa ser removido, sempre

| Onde aparece | Trocar por |
|---|---|
| Nome do estabelecimento | "este estacionamento" |
| Endereço com número | "Centro Histórico de São Paulo" |
| Nomes dos quatro hotéis conveniados | "quatro hotéis próximos" / "o hotel mais próximo" |
| Nome de cortesia do cartão mestre | "o nome de cortesia" |
| `hoteis:` no `parametros.yaml` | `[hotel_a, hotel_b, hotel_c, hotel_d]` |

E o cabeçalho `> ⚠️ **Versão pública.**` precisa estar nas primeiras linhas do arquivo.

## O dataset também não sobe

`logs_estacionamento_*.csv` está no `.gitignore` — são 15 MB e é **gerado**, não
versionado. Se aparecer em `scripts/`, foi de uma execução local: apague antes do
commit. Quem clona roda `python scripts/Dataset_Final_v13.py`.

## Como conferir antes de subir

```bash
grep -rniE "<nome-do-estabelecimento>|<nome-do-hotel>|<endereço>" .
```

Deve retornar zero.
