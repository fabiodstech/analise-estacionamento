# Etapa 3 — EDA de negócio (v13)

Base: `logs_estacionamento_v13.csv` · 66.961 registros · 180 dias plenos · 33.060 estadias
Scripts: `eda3_negocio.py` (números) e `eda3_graficos.py` (as 9 figuras)
Perguntas definidas antes de rodar: `etapa3_perguntas.md`

Todas as oito passaram pelo filtro da auditoria de origem: **nenhuma resposta é um
parâmetro que o gerador escreveu.**

---

## 1. Onde está o dinheiro · `01_onde_esta_o_dinheiro.png`

| Segmento | Transações | Ticket médio | Receita |
|---|---|---|---|
| Hóspede Hotel | 677 | **R$ 103,98** | R$ 70,4 mil |
| Mensalista inadimplente | 9 | R$ 41,78 | R$ 0,4 mil |
| Avulso Regular | 3.863 | R$ 20,70 | R$ 80,0 mil |
| Carga e Descarga | 528 | R$ 6,04 | R$ 3,2 mil |
| Mensalidade (boleto) | 492 | **R$ 406,00** | R$ 199,8 mil |

**O hotel entrega quase a mesma receita que o avulso inteiro com 5,6× menos
transações.** R$ 70,4 mil contra R$ 80,0 mil — e cada transação de hotel vale 4,8×
uma de avulso.

Isso tem consequência operacional direta: **Passe Livre é Caixa obrigatório** (regra
2), então esse dinheiro passa todo por atendimento manual. O segmento mais rentável
por transação é também o que menos se automatiza.

✏️ **Mudou em relação ao v12**, e a correção é honesta: lá o hotel entregava 1,27× o
avulso. O v13 corrigiu a distribuição de diárias (o v12 não tinha hóspede de uma
noite, o caso mais comum), e o ticket caiu de R$ 157 para R$ 104. **A leitura antiga
superestimava o hotel em 45%.**

⚠️ Reportar **ticket**, não fatia da receita: a fatia depende de quantos clientes de
cada tipo o gerador cria; o ticket depende só da tabela de preços e da duração.

---

## 2. O convênio de selos custa mais do que rende · `02_margem_do_selo.png`

**1.825 selos no período. Vendidos por R$ 15,3 mil, abonaram R$ 16,6 mil.
Margem: −R$ 1,3 mil.**

O selo é vendido a R$ 9 e desconta o valor de 1 hora, R$ 15. Mas o desconto é
**limitado pela conta**, e é daí que vem o achado contraintuitivo:

| Selos apresentados | Abono médio | Preço de venda | Margem |
|---|---|---|---|
| 1 | R$ 13,22 | R$ 9,00 | **−R$ 4,22** |
| 2 | R$ 23,46 | R$ 18,00 | −R$ 5,46 |
| 3 | R$ 23,10 | R$ 27,00 | **+R$ 3,90** |

**Quem apresenta 3 selos gera lucro; quem apresenta 1 gera prejuízo.** Com 3 selos o
desconto transborda a conta e evapora.

E o piso é estrutural: **um selo isolado dá prejuízo em 100% dos casos**, porque
daria margem só numa conta abaixo de R$ 9 e o mínimo da tabela é R$ 10.

**Recomendação com número:** alinhar o preço à tarifa que ele desconta — vender a
R$ 12–13, ou criar um selo de meia hora (R$ 10 de abate). Zera o programa sem mudar
nada do que o lojista entrega ao cliente. O reajuste de R$ 8 para R$ 9 em 01/06 já
andou nessa direção.

---

## 3. Vaga vendida não é vaga ocupada · `03_vaga_vendida_vs_ocupada.png`

| | Carros |
|---|---|
| Capacidade | 378 |
| **Vagas contratadas por mensalistas** | **108** (29% da capacidade) |
| Ocupação física média | 67 |
| Pico | 119 · Piso noturno (3h) | 58 |

**A garagem opera a 62% do que já está vendido — e a 18% do que cabe.**

O piso noturno de 58 carros são os moradores, cujo contrato é justamente para o carro
dormir ali. A ociosidade **física** existe, mas a ociosidade **comercial** é uma
ordem de grandeza maior: 270 das 378 vagas não têm contrato nenhum.

⚠️ **Nenhuma das duas métricas é lida do sistema.** Não existe snapshot de ocupação
(regra 23) — ela é reconstruída somando entradas e saídas, e essa reconstrução só é
válida depois de excluir as tentativas bloqueadas.

⚠️ Os níveis dependem do tamanho da base, que é escolha de modelagem. **O que se
reporta é a distância entre as duas métricas**, não o percentual absoluto.

---

## 4. O sábado é mais pesado do que o volume sugere · `04_o_sabado.png`

| | Manobras/dia | Janela comercial | **Por hora** |
|---|---|---|---|
| Dia útil | 298 | 9,5 h | 21,7 |
| **Sábado** | 310 | **7,5 h** | **30,8** |

**+4% de volume, +42% de intensidade por hora.**

Cada manobra de carro custa manobrista e elevador; moto não entra na conta, porque o
cliente estaciona sozinho (regra 23). **O sábado é o dia que dimensiona a equipe**, e
quem olha só o total diário não percebe.

⚠️ **Que o sábado é o dia de maior movimento não é descoberta** — é o que o
informante descreveu e o gerador reproduz. O que a análise acrescenta é a
consequência por hora, que não é entrada de ninguém.

### 4b. E o reajuste apagou o prêmio do sábado · `05_premio_do_sabado.png`

| Ticket médio do avulso | Dia útil | Sábado | Prêmio |
|---|---|---|---|
| Tabela antiga | R$ 17,31 | R$ 22,82 | **+32%** |
| Tabela unificada | R$ 22,56 | R$ 22,92 | **+2%** |

**O sábado era o dia cheio E caro. Virou só o dia cheio** — e passou a render
ligeiramente *menos* por ticket que um dia útil, mantendo o dobro do volume e a maior
intensidade de manobra.

---

## 5. A recarga elétrica contra o app real · `06_ev_real_vs_v13.png`

**Volume 1,01× · energia 0,99×.** É a única validação externa do projeto.

| Mês | Simulado | Real | Razão |
|---|---|---|---|
| fev | 1,25 | 1,11 | 1,13× |
| mar | 1,29 | 1,23 | 1,05× |
| abr | 1,70 | 2,00 | 0,85× |
| mai | 1,55 | 1,84 | 0,84× |
| jun | 2,67 | 2,60 | 1,03× |
| jul | 2,81 | 2,65 | 1,06× |
| ago | 5,64 | 4,80 | 1,17× |

kWh/sessão: **10,63** contra 10,71 medidos no app.

⚠️ **A razão mensal é ruidosa por construção.** Com ~7 veículos elétricos na base, um
mês inteiro tem poucas dezenas de sessões, e mexer no parâmetro de calibração em
0,005 move meses individuais em até 40%. **A calibração é feita contra a taxa da
série inteira**, que é a estatística estável. Ler razão mensal como precisão é falsa
precisão.

---

## 6. Quantas tomadas o crescimento exige · `07_dimensionamento_tomadas.png`

Modelo de filas (Erlang B) sobre a duração medida no app: 1,82 h por sessão,
concentradas em ~12 h do dia.

| Recargas/dia | 2 tomadas | 3 tomadas | 4 tomadas | 6 tomadas |
|---|---|---|---|---|
| 2,6 (jul/2026) | 5,4% | 0,7% | 0,1% | 0,0% |
| **4,8 (ago/2026, real)** | **13,3%** | 3,1% | 0,6% | 0,0% |
| 8,3 (+3 meses) | 26,0% | 9,8% | 3,0% | 0,2% |
| 14,3 (+6 meses) | 42,7% | 23,5% | 11,3% | 1,7% |

*(% = chance de o motorista chegar e não achar tomada livre)*

**A obra da 3ª tomada chegou na hora.** Com o volume de agosto, 2 tomadas já deixam
1 em cada 8 motoristas sem vaga de recarga; a 3ª derruba para 3,1%.

**Mas ela satura em ~5 recargas/dia** — que é exatamente o volume de agosto. Compra
poucos meses no ritmo atual, e a demanda cresce ~8× ao ano.

**O achado não óbvio: potência rende mais que número de vagas.** Trocar as 3 tomadas
por trifásicas (22 kW) triplica a capacidade sem abrir vaga nova. Seis tomadas
comuns entregam quase o mesmo, ocupando o dobro do espaço.

⚠️ Um agravante que a regra 39.3.1 registra: **a demanda de recarga se concentra no
horário de maior movimento** do estacionamento. O modelo acima assume chegadas
espalhadas em 12 h — se estiverem empilhadas no pico, os números são otimistas.

---

## 7. Depois da 3ª hora, a vaga é de graça · `08_teto_da_terceira_hora.png`

A tabela para de subir na 3ª hora. O que ela chama de "12 horas" **não é uma faixa —
é o teto** da soma de horas adicionais:

| Permanência | Valor | Δ |
|---|---|---|
| 30 min | R$ 10 | — |
| 1 h | R$ 15 | +5 |
| 2 h | R$ 23 | +8 |
| **3 h** | **R$ 30** | +7 · **teto** |
| 4 h … 12 h | R$ 30 | **+0** |

E não é caso raro:

| Faixa | Estadias | % |
|---|---|---|
| até 30 min | 504 | 11,2% |
| 30 min–1 h | 558 | 12,3% |
| 1 h–3 h · tarifa ainda sobe | 2.351 | 52,0% |
| **3 h–12 h · teto** | **1.107** | **24,5%** |

**Um quarto das estadias de avulso passa das 3 horas** e ocupa a vaga sem custo
marginal nenhum. São **998 horas de vaga** entregues acima do teto no período.

Cobrando a hora adicional até a 12ª: **+R$ 13,1 mil, ou 16% da receita de avulso.**

**Não é recomendação de subir preço** — o teto pode ser exatamente o que atrai o
cliente de meio-período. É a quantificação do que ele custa, que ninguém tinha.

⚠️ **A faixa de 24 h nunca é acionada no dataset** (permanência máxima de avulso:
7,9 h). Na operação real ela tem público próprio — quem passa a noite e não está em
hotel conveniado. **É uma limitação declarada: o v13 não gera pernoite de avulso.**

---

## 8. A inadimplência aparece como receita · `09_inadimplencia_como_receita.png`

9 bloqueios, **4 clientes distintos** no período em que o bloqueio existe
(junho em diante — antes disso o ERP não existia).

| | Valor |
|---|---|
| Mensalidade média que deixou de entrar | R$ 406,00 |
| Ticket que o bloqueado paga na saída | R$ 41,78 |

**O cliente que não pagou continua entrando, e passa a gerar linha positiva no
caixa.** Antes de junho virava juros no boleto; depois, ticket de avulso. Nos dois
regimes, a inadimplência **nunca aparece como perda**.

Um painel de faturamento diário não enxerga o problema — é preciso cruzar com o ERP.
É uma métrica que engana pelo sinal.

⚠️ **E há um ponto cego pior**, documentado na regra 11.4: existe um cliente que
atrasa todo mês e **nunca é bloqueado**, porque o veículo está com defeito na garagem
e não passa pela cancela. O bloqueio acontece no portão; quem não passa pelo portão é
invisível. **A taxa de inadimplência medida pelo log de movimento subestima
sistematicamente — e subestima justamente o caso crônico.**

---

## O que mudou em relação à leitura do v12

| Achado | v12 | v13 | Por quê |
|---|---|---|---|
| Ticket do hotel | R$ 157 | **R$ 104** | o v12 não tinha hóspede de 1 diária, o caso mais comum |
| Hotel vs avulso (receita) | 1,27× | **0,88×** | consequência do mesmo |
| Clientes com bloqueio | 20 | **4** | o bloqueio só existe a partir de 06/2026, e com reincidência |
| Faixa de 12 h | "nunca usada" | **teto atingido em 24,5% das estadias** | era leitura errada minha: é teto, não faixa |

---

## 🔍 Revisão crítica dos achados

Feita antes de publicar. Encontrou **um erro de método** e uma fragilidade que
atravessa metade da lista.

### O erro: a mesma comparação de EV dava três números

A validação contra o app pode ser resumida de três formas, e elas **não coincidem**:

| Forma de resumir | Resultado |
|---|---|
| Soma das taxas mensais (peso igual por mês) | 0,96× ← *foi para o gráfico* |
| Total de sessões ÷ 180 dias, contra a média das taxas | 1,02× ← *foi para o script* |
| **Sessões observadas ÷ esperadas, ponderando pelos dias cobertos** | **0,93×** ← *correta* |

As duas primeiras estavam ambas no material, em lugares diferentes. E as três diferem
porque **a janela cobre fevereiro pela metade e agosto por um terço** — meses com
taxas muito distintas.

A terceira é a correta: 388 sessões contra 386 esperadas. **Corrigido nos dois
scripts, e a calibração foi refeita contra esse alvo** (`chance_base` 0,118 → 0,126),
fechando em **1,01×**.

Lição para o resto do projeto: quando um resumo pode ser calculado de três jeitos,
escrever qual foi usado — senão dois números verdadeiros e diferentes acabam na mesma
apresentação.

### A fragilidade: mecanismo é sólido, magnitude nem sempre

Auditei **de onde vem cada número**, não cada achado. O resultado incomoda:

| Achado | O mecanismo | A magnitude |
|---|---|---|
| 1 · ticket do hotel × avulso | ✅ tabela de preços + diárias | ⚠️ "5,7× menos transações" depende dos volumes inventados |
| 2 · margem do selo por quantidade | ✅ preço do selo + tabela | ⚠️ o total de −R$ 1,3 mil depende de quantos selos o gerador sorteia |
| 3 · contratado × físico | ✅ comportamento documentado | ⚠️ 108 vagas e 18% dependem do tamanho da base |
| 4 · sábado mais intenso por hora | ✅ volume ≥ dia útil em janela menor | ⚠️ o "+42%" depende da taxa de avulso por tipo de dia |
| 4b · prêmio de preço perdido | ✅ as duas tabelas | ✅ |
| 5 · EV contra o app | ✅ fonte externa | ✅ |
| 6 · saturação das tomadas | ✅ duração medida | ✅ |
| 7 · teto na 3ª hora | ✅ tabela de preços | ⚠️ "24,5%" e "+R$ 13 mil" dependem da distribuição de permanência |
| 8 · inadimplência vira receita | ✅ regra 36 + tabela | ✅ a ordem de grandeza vem dos 2–3/mês do informante |

**Dez números são seguros, seis são ilustrativos.** Nenhum é falso — mas seis deles
mudariam se eu tivesse inventado uma base de outro tamanho.

**Regra de publicação que sai daí:**

> Publicar o **mecanismo** como achado e a **magnitude** como ilustração.
> "Um selo isolado dá prejuízo sempre, por construção" é afirmação.
> "O programa perdeu R$ 1,3 mil no semestre" é ilustração da ordem de grandeza.

É a versão fina do erro que já apareceu três vezes neste projeto — antes eu publicava
o parâmetro como achado; agora o risco é publicar a **consequência de um parâmetro**
com a mesma confiança de uma consequência de uma regra.

### O que isso muda na prática

- **Nos quatro slides do carrossel**, usar só achados de mecanismo seguro: o selo
  (2), o teto da 3ª hora (7), o prêmio do sábado (4b) e a validação de EV (5).
- **No relatório**, manter as magnitudes com a marcação de ilustrativas.
- **A intensidade do sábado (4)** entra pela *direção*, que é garantida: mesmo volume
  em janela menor implica mais manobras por hora, sempre. O percentual é ilustração.


---

## Limitações a declarar no relatório

1. **A faixa de 24 h não tem cobertura** — o v13 não gera pernoite de avulso.
2. **A razão mensal do EV é ruidosa** com uma frota de ~7 veículos; só a série
   inteira é estável.
3. **Os níveis de ocupação dependem do tamanho da base**, que é arbitrado. A
   distância entre contratado e físico é o que se reporta.
4. **A inadimplência medida por bloqueio subestima** — a fonte correta é o ERP.
5. **O perfil horário do dataset é design do gerador**, não evidência. Nenhum achado
   deste documento se apoia nele.
6. **Seis das magnitudes são ilustrativas** (ver a revisão crítica acima): elas
   mudariam com uma base de outro tamanho. Os mecanismos, não.

---

## Gráficos

`01_onde_esta_o_dinheiro` · `02_margem_do_selo` · `03_vaga_vendida_vs_ocupada` ·
`04_o_sabado` · `05_premio_do_sabado` · `06_ev_real_vs_v13` ·
`07_dimensionamento_tomadas` · `08_teto_da_terceira_hora` ·
`09_inadimplencia_como_receita`

**São 9 figuras para 8 perguntas** — o sábado usa duas (intensidade e prêmio de
preço). A prévia do projeto prometeu 8 visualizações; entregar 9 cumpre com folga.

Para o carrossel, os quatro mais visuais: **02** (a margem que inverte), **08** (o
teto da 3ª hora), **04/05** (o sábado) e **06** (a validação externa).
