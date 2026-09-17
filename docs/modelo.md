# Etapa 4 — modelo preditivo de ocupação (v13)

Script: `modelo_ocupacao_v13.py` · gráficos em `graficos_etapa4/`
Base: `logs_estacionamento_v13.csv` · alvo: ocupação de **carro**

**Dois alvos, como combinado:** média diária e ocupação por hora.
**Split temporal 75/25, sem embaralhar** — embaralhar série temporal vaza o futuro.
**Features só de calendário**: dia da semana, mês, dia do ano, feriado, fim de semana,
domingo, marco de 01/06 e (no alvo horário) a hora. Nenhuma usa passado recente, então
o modelo serve para qualquer data futura.

---

## Resultado

### Alvo 1 — média diária
*135 dias de treino · 46 de teste · alvo médio 68,2 carros · amplitude semanal 22,4*

| Modelo | MAE (carros) |
|---|---|
| **Gradient Boosting** | **2,23** |
| Random Forest | 2,24 |
| Baseline sazonal + degrau | 2,71 |
| Persistência 7 dias | 3,25 |
| Baseline sazonal | 3,27 |
| Média global | 7,27 |

### Alvo 2 — ocupação por hora
*3.236 horas de treino · 1.079 de teste*

| Modelo | MAE (carros) |
|---|---|
| **Random Forest** | **3,42** |
| Gradient Boosting | 3,50 |
| Baseline sazonal + degrau | 3,66 |
| Baseline sazonal | 3,94 |
| Persistência 7 dias | 4,68 |
| Média global | 14,39 |

**As árvores ganham nos dois alvos.** Mas a conclusão interessante não é essa.

---

## 🔍 De onde vem a vantagem das árvores

O ranking acima esconde uma pergunta: **as árvores aprenderam estrutura, ou aprenderam
um fato?**

O v13 tem uma descontinuidade conhecida — o marco de 01/06/2026, quando a empresa de
logística saiu e o ERP entrou. E o período de teste está **inteiramente depois** dele,
enquanto 80% do treino está antes.

Para isolar isso, acrescentei um baseline que continua sendo baseline: **a mesma média
por dia da semana, calculada duas vezes — uma para cada regime.** Duas tabelas de
média, sem treino, sem hiperparâmetro.

| Alvo diário | MAE | Distância percorrida |
|---|---|---|
| Baseline sazonal | 3,27 | — |
| **Baseline sazonal + degrau** | **2,71** | **54% do caminho** |
| Gradient Boosting | 2,23 | 100% |

> **Mais da metade da vantagem das árvores é um fato binário que cabe numa linha de
> código.** O resto — 17,8% a mais — **não é estatisticamente significativo**
> (Wilcoxon, p = 0,150).

O mesmo vale por hora: Random Forest vence o baseline simples com folga
(p < 0,001), mas contra o baseline **com o degrau** o ganho cai para 6,7% e some na
significância (p = 0,330).

**Importância das features no Gradient Boosting:** domingo 51%, dia da semana 31%,
feriado 10%. Ou seja: o modelo gasta 92% da sua capacidade explicativa em três coisas
que qualquer pessoa escreveria à mão.

---

## O que isso significa para o app (Etapa 5)

**A escolha do baseline continua defensável — e agora por um motivo melhor que no v12.**

| | Baseline sazonal + degrau | Gradient Boosting |
|---|---|---|
| MAE diário | 2,71 carros | 2,23 carros |
| Erro sobre as 378 vagas | 0,72 p.p. | 0,59 p.p. |
| Precisa de treino | não | sim |
| Precisa de biblioteca | não | scikit-learn |
| Explicável para quem opera | "é a média daquele dia da semana" | "é um ensemble de árvores" |
| Diferença é significativa? | — | **não (p = 0,150)** |

Trocar por Gradient Boosting compra **0,5 carro de precisão** que o teste não distingue
de zero, ao custo de treino, dependência e opacidade.

⚠️ **Mas a recomendação tem prazo de validade.** O baseline + degrau depende de alguém
saber que existe um degrau, e onde ele está. Isso funciona porque 01/06 é um marco
documentado. **Numa quebra não documentada, as árvores achariam sozinhas e o baseline
não.**

---

## Comparação com o registrado no v12

| | v12 | v13 |
|---|---|---|
| Campeão no alvo diário | Gradient Boosting (2,36) | Gradient Boosting (2,23) |
| Baseline sazonal | 2,74 | 3,27 |
| Topo separável do baseline? | **não** (p = 0,222) | **não**, contra o baseline com degrau (p = 0,150) |
| Autocorrelação lag-1 | 0,10 | **−0,00** |
| Autocorrelação lag-7 | 0,67 | **0,84** |

**A estrutura semanal ficou mais forte e a diária desapareceu.** Faz sentido: o v13 deu
variação de fim de semana ao morador (regra 11.1b) e tirou a empresa de logística, que
tinha calendário invertido. O dia de ontem agora não diz literalmente nada — lag-1 é
zero.

✏️ **A pendência do `modelo_ocupacao_v12.md` morre aqui.** Aquele documento registrava
que a minha reprodução não batia com o resultado anotado ("o baseline superou o Random
Forest"), e que no v10 quem ganhava era a persistência de 7 dias. Com o v13 a
comparação foi refeita do zero, sobre uma base que passa em 25 asserções, e o resultado
é reproduzível pelo script. **Não vale mais perseguir o script antigo** — ele rodava
sobre um dataset com bug de pareamento.

---

## Limitações a declarar

1. **O erro é pequeno porque o alvo varia pouco.** A amplitude semanal é de 22 carros e
   o campeão erra 2,2 — mas a garagem opera a 18% da capacidade. Num cenário de
   ocupação alta o problema seria outro.
2. **O período de teste é curto** (46 dias) e está inteiramente num só regime. Nenhuma
   das comparações do topo se sustenta com significância nessa amostra.
3. **A ocupação é reconstruída, não medida.** Não existe snapshot no sistema (regra 23),
   e a reconstrução só é válida excluindo as tentativas bloqueadas.
4. **O alvo é carro.** A ocupação de moto tem um degrau de −43% no marco e precisaria de
   modelo próprio, ou de tratar o regime explicitamente.
5. **Nada disso valida o modelo contra a operação real** — valida contra um dataset
   sintético fiel às regras. O que se demonstra é o método, não a previsão.

---

## Para o post da Etapa 4

O gancho não é "qual modelo venceu". É:

> **Metade da vantagem do modelo era uma linha de código.**

A prévia prometeu "baseline vs. Random Forest, validação cronológica" — e o resultado
honesto é que as árvores vencem, mas quase todo o ganho vem de terem aprendido um fato
de calendário que o analista já conhecia. Quando o baseline recebe esse mesmo fato, a
diferença deixa de ser significativa.

**Gráficos:** `01_ranking` · `02_de_onde_vem_a_vantagem` · `03_previsto_vs_real` ·
`04_curva_horaria`.

O **02** é o slide central.
