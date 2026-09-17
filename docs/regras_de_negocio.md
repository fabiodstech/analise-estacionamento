> ⚠️ **Versão pública.** Este documento é o núcleo do projeto: são as regras de
> operação mapeadas em conversa com quem trabalha no estabelecimento, e é delas que
> sai cada distribuição do gerador.
>
> **Foram removidos desta versão:** o nome do estabelecimento, o endereço exato e os
> nomes dos hotéis conveniados. Nada disso afeta a análise — as regras, os percentuais
> e as tabelas de preço estão íntegros.
>
> A publicação foi autorizada pela gestão. A omissão do nome é **decisão do autor**:
> o conteúdo inclui política comercial e envolve terceiros que não autorizaram nada.

# Regras de Negócio — Projeto Estacionamento

Documento de referência com todas as regras operacionais mapeadas em
conversas com Fabio (funcionário do estacionamento). Consultar antes de
qualquer etapa de limpeza, EDA ou modelagem — várias dessas regras mudam
a forma como o dado deve ser interpretado.

---

## 1. Segmentos de cliente

| Segmento | Descrição |
|---|---|
| **Mensalista** | Paga mensalidade fixa, não é cobrado por ticket individual |
| **Avulso** | Paga por permanência, sem vínculo prévio |
| **Passe Livre** | Convênio com hotéis próximos — hóspede paga estacionamento antecipado (embutido na diária) e tem acesso liberado enquanto dentro do valor pago |
| **Convênio Selo** | Convênio com lojistas — lojista compra cartela de 50 selos e distribui livremente aos seus clientes; cada selo = 1h de desconto |
| **Carga e Descarga** | Cliente que só deixa/retira mercadoria, não estaciona o carro — giro rápido, tarifa fixa de R$5,00 até 15 minutos (ver seção 30) |
| **Locação de espaço** | Cliente corporativo que aluga **área**, não vagas — não tem número fixo de veículos. Único caso conhecido: a empresa de logística que saiu em 01/06/2026 (ver seção 38) |
| **Cartão Mestre / Cortesia** | Uso administrativo/interno (passagem de pedestre com carrinho/malas, veículo de funcionário) — não representa receita real (ver seção 34) |

---

## 2. Forma de pagamento e canal

O canal de pagamento **não é uma escolha livre do cliente** — é determinado
pela combinação de segmento + forma de pagamento + orientação da diretoria
(nem sempre seguida na prática).

| Segmento | Onde paga | Observação |
|---|---|---|
| Mensalista | Não paga na hora | — |
| Avulso + Cartão | **Deveria** ser Totem (orientação da diretoria) | Na prática pode acabar pago no Caixa (desvio da orientação — ver seção 3) |
| Avulso + Pix ou Dinheiro | Caixa (única opção) | Totem não aceita Pix ainda |
| Convênio Selo | Caixa (obrigatório) | Desconto de selo aplicado manualmente pelo operador |
| Passe Livre | Caixa (obrigatório) | Ativação do passe é manual no sistema, feita pelo operador no momento do pagamento |

**Totem:** uso exclusivo para Avulso pagando em **Cartão**. Não aceita Pix.
Não é usado por Mensalista, Passe Livre ou Convênio Selo (todos exigem
atendimento manual no Caixa).

**Caixa:** aceita Pix, Dinheiro e Cartão (via maquininha própria). É o único
canal para Selo e Passe Livre, e também recebe avulsos-cartão que deveriam
ter ido ao Totem mas não seguiram a orientação.

---

## 3. Aderência à orientação do Totem

A diretoria orienta indicar o Totem para avulsos que querem pagar no
cartão, mas isso **não é uma trava do sistema** — é uma diretriz que pode
não ser seguida na prática (fila, urgência, hábito do atendente, etc.).

**Métrica de negócio derivada:** taxa de aderência = % de avulsos-cartão
que efetivamente pagou no Totem vs. os que acabaram no Caixa.

Isso é diferente de "preferência do cliente" — é adesão a um processo
operacional definido pela gestão.

### 3.1 Denominador canônico (definido em 28/08/2026 após a EDA do v12)

**Este é o ponto mais delicado da métrica.** A EDA mostrou que a aderência
varia **29 pontos percentuais** conforme quem se define como "avulso", e
que a maior parte dessa variação são pagamentos que a **seção 2 obriga a
ir ao Caixa** sendo contados como desvio do atendente.

| Denominador testado | Aderência medida |
|---|---|
| `Categoria_Principal = 'Avulso'` + cartão | 54,2% |
| `Subcategoria = 'Avulso Regular'` + cartão | 63,8% |
| + só carro | 75,6% |
| + sem selo e sem recarga EV | 83,1% |
| **+ sem Carga e Descarga** | **90,3%** |

> **Definição canônica — usar sempre esta:**
> Avulso Regular **e Mensalista Inadimplente** · Carro · **sem selo** · **sem
> recarga EV** · **sem Carga e Descarga** · pagando em cartão.
> Numerador: os que pagaram no Totem. Denominador: esses mesmos, no Totem
> ou no Caixa.

⚠️ **Carga e Descarga é a exclusão mais fácil de esquecer**, porque o
segmento **não tem rótulo no sistema** (seção 30). Ele fica escondido dentro
de Avulso Regular e só é identificável por permanência ≤ 15 min + saída pelo
subsolo. Sem esse filtro a métrica cai 7 pontos.

→ **Consequência operacional:** enquanto Carga e Descarga não tiver
categoria própria no Softcase, **a aderência ao Totem não é calculável
corretamente em nenhum relatório**, incluindo o Power BI. Rotular o
segmento é pré-requisito da métrica, não melhoria cosmética.

**Motivo de cada exclusão** (todas derivam da seção 2, não são escolha
analítica):

⚠️ **Correção de 13/09/2026:** o **mensalista inadimplente entrava na lista de
exclusões e não devia.** Ele retira ticket na cancela e paga no totem como
qualquer avulso (ver 36.6). Incluí-lo move a métrica de 89,3% para **89,2%** —
efeito numérico desprezível, mas a definição estava errada, e uma definição
errada que dá quase o mesmo número é pior que uma que dá diferente: passa
despercebida.

| Excluído | Por quê |
|---|---|
| Hóspede Hotel (Passe Livre) | Caixa obrigatório — ativação manual do passe |
| Moto | Totem cobraria valor de carro (seção 4) |
| Convênio Selo | Caixa obrigatório — desconto aplicado manualmente |
| Recarga EV avulsa | Lançamento manual do serviço no caixa |
| ~~Mensalista inadimplente~~ | ⚠️ **CORRIGIDO em 13/09/2026 — ele NÃO se exclui.** Ver 36.6: o inadimplente retira ticket e **paga no totem normalmente**. É elegível, e pertence ao denominador |

A armadilha mais fácil é que **`Categoria_Principal = 'Avulso'` inclui o
Hóspede Hotel**, que por regra nunca pode usar o Totem — ele sozinho
derruba a métrica em 9 pontos.

### 3.2 Limite conhecido da métrica

A aderência é **estável no tempo** (regressão no período do v12: p = 0,24)
e **estável ao longo do dia** (qui-quadrado por hora: p = 0,53). Não há
como atribuir o desvio a atendente ou turno, porque o **login de operador
não é registrado nas cobranças comuns** (seção 17). A leitura defensável é
*"a aderência gira em torno de 90% e o dado disponível não identifica onde o
desvio se concentra"*.

⚠️ **Armadilha registrada:** uma análise anterior encontrou variação por
faixa horária (55% às 8h contra 93% à noite, p = 0,025) e a atribuiu a fila
na abertura e atendente sozinho de madrugada. **Era composição, não
comportamento.** Carga e Descarga sai em minutos, sempre pelo Caixa, e
representa 32% das saídas das 8h contra 0% depois das 19h. Excluindo o
segmento, o padrão some (p = 0,53). **Não reportar variação horária de
aderência sem antes remover Carga e Descarga.**

→ **Recomendação de negócio derivada:** registrar o operador na transação
transformaria uma métrica agregada numa recomendação acionável.

### 3.3 Teto estrutural do Totem

Vale reportar junto: no v12 o Caixa processa **R$ 167,8 mil** e o Totem
**R$ 43,0 mil** — o Totem responde por ~20% do dinheiro da operação. Selo,
Passe Livre, moto, Pix, dinheiro e Carga e Descarga são todos
obrigatoriamente manuais. **O teto do Totem no desenho atual é baixo por
regra, não por falta de adesão** — 83% de aderência num universo pequeno.
Habilitar Pix no Totem é a alavanca com maior efeito sobre esse teto.

---

## 4. Identificação de veículo (carro vs. moto)

O sistema **ainda não diferencia** carro de moto automaticamente (sensor
de classificação está em implantação futura). Hoje, todos os veículos são
tratados como "carro" no sistema.

- **Câmera captura placa apenas pela frente do veículo.**
- Moto tem placa só na traseira → **não é capturada na entrada**.
- Carro com placa danificada/ilegível → **também pode não ser capturado**
  (caso mais raro, mas ocorre).

**Consequência:** `placa_vazia` é um proxy IMPERFEITO para moto:
- Maioria dos casos de placa vazia = moto (padrão esperado)
- Minoria = carro com placa danificada (exceção, mas existe e não é
  possível distinguir com certeza usando só esse campo)

**Regra de cobrança de moto:**
- Moto **precisa** sair pelo Caixa — o valor de moto é diferente do de
  carro e precisa ser ajustado manualmente pelo operador na hora da
  cobrança.
- Se um cliente de moto for por engano ao Totem, o sistema cobra o
  **valor de carro** (cobrança incorreta, sem intervenção manual possível
  no totem).

**Sinal de possível cobrança incorreta:** registro com `placa_vazia = True`
e `canal = Totem` — indício de moto mal direcionada (mas pode também ser
falso positivo: carro com placa danificada que foi corretamente ao Totem).

---

## 5. Campos derivados sugeridos para o dataset

| Campo | Como calcular | Observação |
|---|---|---|
| `canal` | Totem / Caixa | Dado observado, não derivável só pela regra (por causa dos desvios de orientação) |
| `elegivel_totem` | `Subcategoria = 'Avulso Regular'` E `Tipo_Veiculo = 'Carro'` E `Selos_Apresentados = 0` E `Valor_Recarga_EV = 0` E forma de pagamento em cartão | **Corrigido em 28/08/2026.** Isola quem *podia* ter usado o Totem — ver seção 3.1 |
| `seguiu_orientacao_totem` | True se (`elegivel_totem` E canal=Totem); False se (`elegivel_totem` E canal=Caixa); **N/A para os demais** | Mede aderência ao processo, não preferência do cliente. A versão anterior desta fórmula usava só "Avulso + Cartão" e **contradizia a seção 2**, classificando como desvio pagamentos que a regra obriga a ir ao Caixa |
| `entrada_efetiva` | `Sentido = 'Entrada'` E `Status ≠ 'Bloqueado'` | **Novo em 28/08/2026.** A tentativa bloqueada é logada como Entrada mas o veículo não entrou — contá-la infla o movimento e quebra o pareamento entrada→saída. Ver seção 36 |
| `placa_vazia` | True/False conforme o registro de entrada | Proxy imperfeito de moto — tratar como aproximação, não certeza |
| `possivel_cobranca_incorreta` | `placa_vazia = True` E `canal = Totem` | Sinal de atenção, não confirmação — comunicar como estimativa no relatório |

---

## 6. Recarga de veículos elétricos (Clamper Mobi)

> **Seção revisada em 26/08/2026** com a série mensal real extraída do app.
> A estimativa anterior de "~60 recargas/mês" foi **corrigida** — ver abaixo.

O estacionamento oferece 2 vagas com recarga de veículo elétrico, usando um
sistema à parte do Softcase: **Clamper Mobi**.

- **Clamper Mobi Driver**: app do usuário final (motorista) — controla
  início/fim da recarga e vê o próprio consumo. Fabio não tem acesso a
  dados agregados por aqui.
- **Clamper Mobi Manager**: plataforma web administrativa, à qual Fabio
  **tem acesso**. É onde ficam os relatórios de gestão.

### 6.1 O que é possível extrair (atualizado)

A tela **"Consumo Total Mensal"** do Mobi Manager **foi localizada** e entrega,
por mês, três métricas: **kWh consumidos**, **número de recargas** e **tempo de
uso acumulado**. Isso é mais do que se supunha antes — não é granularidade de
sessão, mas permite derivar por divisão as médias de kWh/sessão, duração/sessão
e potência média, que é o suficiente para calibrar a simulação.

**O que continua indisponível:** granularidade de sessão (horário de início/fim
de cada recarga). Sem isso, seguem inviáveis: horário de pico de uso das
tomadas, taxa de ocupação das 2 vagas ao longo do dia, e eventual fila/espera.
As análises de EV do projeto ficam, portanto, no nível **mensal agregado**.

**Método de extração usado:** leitura manual das telas, mês a mês (não há
export). Rápido para uma série de ~12 meses; inviável de manter atualizado com
frequência alta.

### 6.2 Série real medida (set/2025 – ago/2026)

| Mês | kWh | Recargas | Tempo de uso | kWh/sessão | h/sessão | kW médio |
|---|---|---|---|---|---|---|
| set/2025 | 85,01 | 10 | 16:06 | 8,50 | 1,61 | 5,28 |
| out/2025 | 241,95 | 27 | 38:18 | 8,96 | 1,42 | 6,32 |
| nov/2025 | 144,57 | 21 | 24:28 | 6,88 | 1,17 | 5,91 |
| dez/2025 | 205,91 | 20 | 35:21 | 10,30 | 1,77 | 5,82 |
| jan/2026 | 274,10 | 25 | 52:42 | 10,96 | 2,11 | 5,20 |
| fev/2026 | 191,80 | 31 | 35:39 | **6,19** | 1,15 | 5,38 |
| mar/2026 | 455,04 | 38 | 78:45 | 11,97 | 2,07 | 5,78 |
| abr/2026 | 712,03 | 60 | 118:06 | 11,87 | 1,97 | 6,03 |
| mai/2026 | 529,03 | 57 | 87:09 | 9,28 | 1,53 | 6,07 |
| jun/2026 | 853,20 | 78 | 141:34 | 10,94 | 1,81 | 6,03 |
| jul/2026 | 978,13 | 82 | 159:08 | 11,93 | 1,94 | 6,15 |
| ago/2026 * | 618,79 | 59 | 115:00 | 10,49 | 1,95 | 5,38 |

\* **ago/2026 é parcial e a leitura é do início do mês (~12/08), não do fim.**
Vale 12 dias, não 31 — normalizar por dia antes de comparar com qualquer coisa.
Leitura posterior em **25/08/2026: ~120 recargas**, o que dá 4,80/dia contra os
4,92/dia da leitura de 12/08 — as duas batem, confirmando o patamar novo.

**Médias de referência (fev–ago/2026):**

| Indicador | Valor |
|---|---|
| Energia por sessão | **10,71 kWh** |
| Duração por sessão | **1,82 h** |
| Potência média de entrega | **5,90 kW** |

### 6.3 Correção do volume: é uma curva, não um patamar

**A afirmação anterior de "~60 recargas/mês" está incorreta como descrição da
operação.** Ela é a média aritmética de fev–jul/2026, mas esconde o que o dado
realmente mostra: uma **curva de adoção em crescimento contínuo**, de
**10 recargas em set/2025 a 82 em jul/2026** — 8× em 11 meses.

Consequências práticas:

- **Não usar um valor único de "recargas/mês"** em nenhuma análise, calibração
  ou projeção. Usar a série, ou o valor do mês específico em questão.
- **Existem três saltos** na série, e os três têm a mesma natureza: entrada de
  veículo elétrico novo na base de mensalistas.

  | Salto | Recargas/dia | Causa (confirmada por Fabio) |
  |---|---|---|
  | mar → abr/2026 | 1,23 → 2,00 | um mensalista antigo trocou de carro por um elétrico, e um mensalista novo entrou já com elétrico |
  | mai → jun/2026 | 1,84 → 2,60 | 2 moradores EV-dependentes entraram como mensalistas em 01/06 |
  | jul → ago/2026 | 2,65 → ~4,8 | mesma dinâmica — mais elétricos na base |

  **A leitura de negócio importa mais que os saltos individuais:** isso não é
  uma sequência de eventos pontuais, é a **eletrificação da frota em São Paulo
  chegando à base de clientes do estacionamento**. A demanda por recarga deve
  continuar subindo por conta própria, sem nenhuma ação comercial. Agosto/2026
  quase **dobrou** julho.
- **Frequência por veículo:** o salto de junho (+0,76 recargas/dia para 2
  veículos novos) indica que um usuário dependente de recarga carrega cerca de
  **1 vez a cada 2,6 dias**, não diariamente.
- **Ocupação das tomadas.** Com 82 recargas em jul/2026 e 2 vagas, são ~1,4
  recarga por vaga por dia; com a duração média de 1,82h, dá ~2,6h de uso por
  vaga por dia. Em ago/2026, com ~4,8 recargas/dia, sobe para ~4,4h por vaga.

**Peso relativo:** o segmento segue representando fatia pequena do volume total
de veículos do estacionamento (~1-2%), o que **não** o torna irrelevante — a
tendência de crescimento é o dado interessante aqui, não o nível absoluto.

### 6.4 Capacidade das tomadas — situação e roadmap

**Estado confirmado por Fabio (26/08/2026):**
1. A **3ª tomada já está em elaboração** (obra em andamento).
2. Depois dela, será necessária **reforma da estrutura elétrica** para comportar
   mais tomadas.
3. Há a possibilidade de instalar uma **tomada de carregamento rápido**.

**O que o dado medido diz sobre isso.** Modelando as chegadas como aleatórias
(Erlang B) com a duração real de 1,82h/sessão e assumindo que a recarga se
concentra em ~12h do dia:

| Recargas/dia | 2 tomadas | 3 tomadas | 4 tomadas | 6 tomadas |
|---|---|---|---|---|
| 2,65 (jul/2026) | 5,4% | 0,7% | 0,1% | 0,0% |
| 4,80 (ago/2026) | **13,3%** | 3,1% | 0,6% | 0,0% |
| 8,3 (+3 meses a +20%/mês) | 25,9% | 9,8% | 3,0% | 0,2% |
| 14,3 (+6 meses) | 42,7% | 23,6% | 11,4% | 1,7% |

(% = chance de um motorista chegar e encontrar todas as tomadas ocupadas)

- **A obra da 3ª tomada está certa e chegou na hora.** Com o volume de agosto,
  2 tomadas já deixam ~1 em cada 8 motoristas sem vaga de recarga. A 3ª derruba
  isso para ~3%.
- **Ela satura em torno de 6 recargas/dia** (limite de 5% de bloqueio) — ou
  seja, compra poucos meses no ritmo de crescimento atual. Faz sentido tratar a
  reforma elétrica como o passo seguinte já planejado, não como contingência.

**A vaga de recarga é rotativa (confirmado por Fabio).** O veículo fica plugado
**apenas durante a carga**; assim que termina, o manobrista tira o carro da
tomada e o guarda em outra vaga. Isso valida o modelo acima — o "Tempo de Uso"
do app é, de fato, o tempo em que a vaga fica indisponível.

Vale notar que essa rotatividade **só é possível porque o estacionamento opera
com manobrista** (seção 15/17). Num autoestacionamento a vaga de recarga ficaria
presa ao carro pelo tempo todo da permanência, e a capacidade seria uma fração
desta. É uma vantagem estrutural do modelo de operação, e vale citar no
relatório.

**Sobre o carregamento rápido.** Como a sessão média entrega só 10,71 kWh, o
tempo de carga cai proporcionalmente à potência — mas o tempo de vaga ocupada
**não**, porque soma o tempo até o manobrista chegar para liberar a tomada:

| Tempo de resposta do manobrista | AC 5,9 kW | DC 50 kW | Ganho real |
|---|---|---|---|
| 0 min (ideal) | 109 min | 13 min | 8,5× |
| 5 min | 114 min | 18 min | 6,4× |
| **10 min** | **119 min** | **23 min** | **5,2×** |
| 20 min | 129 min | 33 min | 3,9× |
| 30 min | 139 min | 43 min | 3,2× |

**Este é o ponto não óbvio do dimensionamento:** com carga lenta, um atraso de
10 min na manobra custa 9% da capacidade e é irrelevante. Com carga rápida, o
mesmo atraso quase dobra o tempo de vaga e **derruba o ganho de 8,5× para
5,2×**. Quanto mais rápido o carregador, mais o tempo de resposta do manobrista
vira o gargalo — o investimento em DC só se paga se o processo de retirada
acompanhar.

**Capacidade por configuração** (recargas/dia a 5% de bloqueio, manobra de 10 min):

| Vagas | AC 5,9 kW | AC 22 kW | DC 50 kW |
|---|---|---|---|
| 2 (hoje) | 2,3 | 7,0 | 12,0 |
| **3 (em obra)** | **5,4** | 16,5 | 28,3 |
| 4 | 9,2 | 28,0 | 48,0 |
| 6 | 17,9 | 54,4 | 93,3 |

Duas leituras para a reforma:

- **Potência rende mais que número de vagas.** Trocar as 3 vagas de AC comum
  por AC trifásico (22 kW) triplica a capacidade sem abrir uma vaga nova —
  16,5 contra 5,4 recargas/dia. Seis vagas AC comuns entregam 17,9, praticamente
  o mesmo, ocupando o dobro do espaço e exigindo mais obra.
- **Medir o tempo de retirada antes de escolher a potência.** É o parâmetro que
  decide entre 22 kW e 50 kW, e hoje ninguém tem esse número. Cronometrar
  algumas dezenas de recargas resolve.

**Custo operacional escondido:** cada recarga gera **uma manobra a mais** (tirar
da tomada, guardar noutra vaga). Hoje são ~4,8 manobras extras/dia, desprezível
frente às ~300 manobras diárias da operação. Com 3 vagas DC no limite seriam
~28/dia, ou **+9%** de carga de manobra — ainda absorvível, mas deixa de ser
ruído e passa a ser algo a considerar na escala da equipe.

### 6.4b Tarifa cobrada pela recarga — confirmado em 28/08/2026

> **Dado novo.** A tarifa existia **apenas no código do gerador** e não
> estava documentada. Confirmada por Fabio, com o cronograma completo.

**Reajuste trimestral desde a instalação:**

| Vigência | R$/kWh |
|---|---|
| set–nov/2025 (instalação) | **1,99** |
| dez/2025–fev/2026 | 2,20 |
| mar–mai/2026 | 2,40 |
| jun/2026 em diante | **2,50** |

**+25,6% em 9 meses**, em reajustes trimestrais regulares. É a única tarifa
da casa com cadência definida — o avulso mudou uma vez (seção 9), o selo uma
vez (25.1) e a mensalidade não mudou no período.

### 6.4c Custo do kWh e margem estimada da recarga

⚠️ **O custo real do estacionamento continua desconhecido** — não há acesso
à conta de energia. O que existe é **referência pública de mercado**, e ela
deve ser usada como ordem de grandeza, nunca como dado da operação.

**Tarifa Enel SP, residencial, após o reajuste de julho/2026:**

| Componente | R$/kWh |
|---|---|
| TUSD (uso do sistema de distribuição) | 0,472 |
| TE (tarifa de energia) | 0,317 |
| **Subtotal sem impostos** | **0,789** |
| Com ICMS, PIS e COFINS (+25% a 30%) | **~0,99 a 1,03** |

*(Valores de bandeira verde; bandeira amarela ou vermelha elevam o custo.)*

⚠️ **Três ressalvas, e a primeira é importante:**

1. **Esta é a tarifa residencial. O estacionamento é consumidor
   comercial**, e com três elevadores e geração própria pode estar em
   Grupo A, onde existe **demanda contratada** — uma componente fixa que
   não aparece no R$/kWh. A conta real pode ter estrutura bem diferente.
2. O valor é de **julho/2026**; a série de tarifas cobradas pela recarga
   (6.4b) começa em set/2025, quando a energia custava menos.
3. **Com geração solar (seção 39) o custo marginal não é um número único**
   — depende da hora do dia.

**Margem estimada por sessão (10,71 kWh a R$ 2,50):**

| | Por kWh | Por sessão |
|---|---|---|
| Receita | R$ 2,50 | R$ 26,78 |
| Custo marginal (rede, com impostos) | ~R$ 1,01 | ~R$ 10,78 |
| **Margem estimada** | **~R$ 1,49 (60%)** | **~R$ 16,00** |

⚠️ **A margem é a mesma em qualquer horário.** A geração solar reduz o
custo **médio** da energia do prédio, mas o estacionamento é importador
líquido o tempo todo (seção 39.2) — então o próximo kWh consumido vem
sempre da rede, ao preço cheio. **Não existe cenário de "energia própria a
custo zero" para a recarga.**

*(Uma versão anterior desta seção apresentava três cenários de margem, de
60% a 100%, conforme o horário da recarga. Estava errada e foi retirada —
ver 39.2.)*

→ **A estimativa que Fabio deu de memória (~R$ 0,80) estava certa** — é
exatamente a tarifa base sem impostos. Com impostos vai a ~R$ 1,00.

### 6.5 fev/2026 é outlier — não usar como base de comparação

fev/2026 registrou **6,19 kWh/sessão**, quase metade da média da série (10,71),
com duração média de apenas 1,15h. É o mês mais atípico dos doze. Qualquer
validação, calibração ou gráfico comparativo ancorado só em fevereiro estará
comparando contra o pior mês possível da série. Usar a série completa.

### 6.6 Uso na simulação

Estes números são a fonte de verdade do módulo EV do gerador desde o **v12**:
duração por sessão como distribuição centrada em 1,82h aplicada a **todos** os
segmentos, potência de 5,4 a 6,4 kW, e um fator de adoção mensal crescente no
lugar de um patamar fixo. Ver `v12_ev_recalibrado.md`.

---

## 9. O marco de 01/06/2026 — três mudanças simultâneas

> **Seção ampliada em 28/08/2026.** O que era registrado só como "mudança
> de tabela de preços" é, na verdade, **um único projeto de modernização
> com três efeitos ao mesmo tempo**. Confirmado por Fabio: a tabela nova e
> o ERP foram idealizados para serem lançados juntos.

**O dataset tem um único ponto de descontinuidade, não vários.** Isso
simplifica a metodologia e fortalece a narrativa do relatório: é um
"antes e depois da modernização", não uma sequência de coincidências.

| # | O que mudou em 01/06/2026 | Detalhe |
|---|---|---|
| 1 | **Tabela de preços unificada** | Ver o resto desta seção e a seção 29 |
| 2 | **Faturamento passa a rodar no ERP** | Ver seção 36 |
| 3 | **Bloqueio automático de inadimplente** | Antes disso **não havia bloqueio** — ver seção 36 |
| 4 | **Saída da empresa de logística** | Recusou o reajuste proposto e foi operar em outro estacionamento — ver seção 38 |

⚠️ **O efeito 4 é de natureza diferente dos outros três.** Os três primeiros
mudam **preço e registro**; o quarto muda **volume, ocupação e sazonalidade
semanal**. É o único que altera quanto movimento existe no pátio.

**Não confundir com elasticidade de demanda do avulso.** O reajuste do
avulso passou sem reação de volume; o reajuste do contrato corporativo
custou o maior cliente da garagem. A elasticidade existiu — no contrato, não
no ticket.

**Consequência crítica para qualquer análise temporal:** três séries mudam
de regime na mesma data por três motivos diferentes. Ao comparar "antes e
depois", declarar qual dos três efeitos está sendo medido — atribuir a
variação inteira ao preço é erro de leitura.

**Alerta específico — artefato de início de coleta.** A série de bloqueios
por inadimplência sai de **zero** e só passa a existir em junho. Isso
**não** significa que a inadimplência apareceu em junho: significa que a
*medição* começou em junho. O atraso de pagamento existia antes e era
tratado com aviso e juros. Ver seção 36.

### 9.1 A mudança de tabela em si

**Data do corte confirmada: 01/06/2026.** Registros com data de
entrada/cobrança anterior a essa data seguem a tabela antiga (dia útil vs.
fim de semana/feriado); a partir dessa data (inclusive), vale a tabela
unificada atual. Ver valores completos das duas tabelas na seção 29.

**Antes (até 31/05/2026):**
- Preço diferente para dias úteis (`SEG A SEX`) vs. fim de semana/feriado
  (`FIM DE SEMANA`) — para cada tipo de veículo (ex: `CARRO SEG A SEX` e
  `CARRO FIM DE SE`, `MOTO SEG A SEX` e `MOTO FIM DE SEM`).

**Agora (a partir de 01/06/2026):**
- Tabela unificada: **todos os dias cobram o mesmo valor**.
- A tabela de fim de semana foi **excluída** do sistema.
- Todos os valores foram **reajustados** (não é só a fusão das duas
  tabelas antigas — os preços mudaram).
- **A tabela "SEG A SEX" permanece com esse nome apesar de agora valer
  para todos os dias da semana** — o nome é legado, não reflete mais a
  regra atual.

**Implicações práticas para o projeto:**
- **Não assumir que o nome da tabela reflete a regra vigente** — o nome
  `CARRO SEG A SEX` hoje não significa "só cobra em dia útil".
- Ao analisar dado histórico (que atravessa a mudança de tabela), usar
  01/06/2026 como data de corte para aplicar a tabela de preço correta
  (antiga ou nova) — não dá para aplicar uma única tabela de preços
  universal para validar `valor_cobrado` em todo o histórico.
- Isso também é um ponto interessante para o relatório final: comparar
  receita/comportamento antes e depois da unificação de tabela pode virar
  uma análise própria (ex: "a unificação de preços impactou o volume de
  fim de semana?").

---

## 11. Subsegmentação de Mensalistas: Trabalhador da Região vs. Morador

O grupo "Mensalista" não é homogêneo — existem dois perfis de comportamento
claramente distintos, relevantes tanto para a EDA real quanto para a
simulação de dados.

| Perfil | Dias de uso | Padrão de entrada/saída |
|---|---|---|
| **Trabalhador da região** | Segunda a sexta; **90% também abre no sábado** (confirmado por Fabio, 28/08/2026). Domingo não trabalha; feriado ~45% | Uma entrada + uma saída por dia — rotina fixa. Inclui funcionários de escritório (horário comercial fixo) e trabalhadores/donos de loja (horário comercial, pode ter mais variação) |
| **Morador de prédio próximo** | Todos os dias, incluindo domingo/feriado | Múltiplas entradas e saídas no mesmo dia, horários variáveis — usa a vaga como garagem residencial |

**Implicações para análise:**
- Essa variabilidade de horários dentro do grupo "Mensalista" não é ruído —
  é comportamento genuíno de dois públicos distintos dentro do mesmo rótulo.
- Essa distinção pode ser **descoberta a partir do dado** (ex: clustering
  por frequência/padrão de horário) em vez de depender de um campo que
  categorize isso explicitamente no sistema — é provável que o sistema não
  tenha esse rótulo pronto.

### 11.1 Features de separação — corrigido em 28/08/2026

> **A versão anterior desta seção recomendava "número de entradas por dia
> por cliente". A EDA do v12 mostrou que essa feature não separa os
> perfis.** O motivo: ela está confundida com o **número de vagas
> contratadas** — correlação de **0,81**. Ela mede quantas vagas o cliente
> aluga, não como ele se comporta.

| Vagas contratadas | entradas/dia — Trabalhador | entradas/dia — Morador |
|---|---|---|
| 1 | 1,00 | 1,50 |
| 2 | 1,79 | 3,03 |
| 3 | 2,70 | 4,58 |

**Normalizar por veículo, não por cliente.** Assim a separação fica limpa:
Trabalhador em 1,00 e Morador entre 1,44 e 1,57.

**Ordem de utilidade das features, medida no v12:**

| # | Feature | Separa? |
|---|---|---|
| 1 | % de entradas em **domingo** | Sim — Trabalhador 0%, Morador 12–16% |
| 2 | % de entradas entre **6h e 10h** | Sim — Trabalhador alto, Morador baixo |
| 3 | Cobertura (% de dias com uso) | Sim — Trabalhador ~81%, Morador ~97% |
| 4 | entradas/dia por **veículo** | Sim |
| 5 | entradas/dia por **cliente** | **Não** — faixas sobrepostas |

Uma regra de uma linha (`% domingo > 5% ⇒ Morador`) classifica corretamente
todos os clientes do v12.

**Ressalva para a etapa de clustering:** essa separação perfeita é uma
propriedade do **dado sintético**, cujo gerador dá ao trabalhador uma
janela de chegada rígida. Na operação real haverá sobreposição — e a
seção 11.2 mostra exatamente de onde ela vem. **Levar a ordem das features
para a modelagem, não a acurácia.**

### 11.2 Os dois perfis não são estanques — confirmado em 28/08/2026

> **Dado novo, e importante para o clustering.** Os rótulos "Trabalhador" e
> "Morador" descrevem a maioria, mas existem clientes com comportamento
> misto. São poucos, e é justamente por serem poucos que passariam
> despercebidos numa análise agregada.

**a) O lojista que usa a garagem como garagem.**

Alguns mensalistas lojistas têm **mais de um carro**. Deixam um deles
estacionado de forma permanente — como garagem residencial — e circulam
com o outro. **Dois ou três clientes** têm esse costume.

Assinatura no dado, e por que ela é traiçoeira:

- O veículo parado **não faz uma entrada e uma saída por dia**, que é a
  regra da tabela acima. Ele fica dias ou semanas sem nenhum evento.
- Isso gera **estadias muito longas para um cliente rotulado como
  Trabalhador** — que é exatamente o padrão que, no v12, foi sintoma de um
  bug de pareamento. ⚠️ **Cuidado ao validar:** "permanência de lojista
  acima de 24h" deixa de ser sinal automático de erro. A distinção tem que
  ser feita por veículo/cliente, não por duração isolada.
- Ele **explica parte da correlação de 0,81** registrada em 11.1 entre
  entradas/dia por cliente e número de vagas: quando um dos veículos do
  cliente quase não se move, a média por cliente desanda.

**b) O morador que viaja.**

Moradores viajam, **com pouca frequência**. **Dois ou três clientes** têm
esse costume, e o comportamento se divide em dois casos **de assinatura
oposta**:

| Caso | O que acontece | Vaga | Eventos |
|---|---|---|---|
| Viaja **com** o carro | Fica alguns dias sem usar a garagem | **Vazia** | Zero |
| Viaja **sem** o carro | Deixa o veículo guardado durante a viagem | **Ocupada** | Zero |

→ **Implicação analítica direta:** "ausência de movimento" **não** é um
sinal único. Nos dois casos o cliente some do log por dias, mas a ocupação
real do estacionamento é oposta. Uma reconstrução de ocupação por soma
cumulativa de entradas e saídas (seção 23) captura a diferença
corretamente — mas qualquer métrica baseada só em *contagem de eventos*
trata os dois como o mesmo cliente inativo, e erra num deles.

**Implicações para a simulação:**

- Modelar os dois comportamentos, com a proporção informada: ~2 a 3
  clientes de cada tipo, não uma fração da base inteira.
- **Não** transformar isso em ruído distribuído entre todos os clientes. É
  um punhado de pessoas com um hábito específico, e é assim que aparece no
  dado real.

**Implicação para o clustering (Etapa 3):** estes são os clientes que vão
cair na fronteira entre os dois grupos, e é bom que caiam. Um resultado que
separa 100% dos clientes é sinal de que o gerador é rígido demais, não de
que o modelo é bom. **Cinco ou seis clientes ambíguos numa base de 80 é o
comportamento esperado**, e vale reportar como validação do modelo, não
como erro.

### 11.3 O terceiro perfil: o mensalista dormente — confirmado em 28/08/2026

> **Existe um terceiro grupo que não é nem Trabalhador nem Morador: o
> cliente que paga e não usa.** Não estava documentado, e é invisível em
> qualquer análise baseada em movimento.

**São 3 clientes** (dado de Fabio, 28/08/2026):

| Veículo | Situação |
|---|---|
| 2 carros | **Com defeito.** Os donos não têm verba para o conserto no momento |
| 1 moto | Comprada nova, usada por poucas semanas, **nunca mais utilizada** — motivo desconhecido |

**Os três seguem pagando o boleto todos os meses.**

**Assinatura no dado — e é aqui que está o problema:**

- **Zero eventos de entrada e saída.** O veículo nunca passa pela cancela.
- O único rastro é a **Renovação Mensal** (boleto). Existem na receita e
  **não existem no log de movimento**.
- A vaga fica **ocupada 24/7**, sem nenhuma transação que o revele.

→ **Consequência metodológica direta:** a contagem de mensalistas derivada
do log de movimento **não é a base de clientes**. Ela subestima. Qualquer
métrica do tipo "entradas por cliente mensalista", "cobertura de uso" ou
"veículos ativos" precisa declarar se o denominador é a base **contratada**
ou a base **observada em movimento** — são coisas diferentes, e a diferença
é justamente o grupo mais silencioso.

→ **Para o clustering:** a cobertura de uso do dormente é **0%**, abaixo do
Trabalhador (~81%) e do Morador (~97%). É um cluster próprio, pequeno mas
perfeitamente separável — e descobri-lo a partir do dado é um bom resultado
de Etapa 3, porque é um grupo que ninguém teria pensado em rotular.

### 11.1b Comportamento do Morador no fim de semana — confirmado em 28/08/2026

O Morador usa a vaga todos os dias (tabela acima), **mas não com a mesma
intensidade**. E o padrão não é uniforme dentro do grupo:

- **A maioria diminui** a quantidade de saídas no fim de semana.
- **Os de maior volume durante a semana mantêm o mesmo volume** no fim de
  semana.

→ **Isso cria subestrutura dentro do perfil Morador**, e é relevante para o
clustering: o morador de alta frequência é **consistente** entre semana e
fim de semana; o de baixa frequência é **enviesado para dias úteis**. A
redução no fim de semana é, portanto, **inversamente relacionada à
frequência de base** — quem usa mais, varia menos.

→ **Para a simulação:** não aplicar um fator de redução único ao segmento.
O fator precisa depender da frequência do próprio cliente.

⚠️ **Limite de observação:** este padrão vem da observação de Fabio, não de
medição. Ver 11.5b sobre por que a operação não consegue medir isso hoje.

### 11.3b ⚠️ Um quarto caso: o cliente corporativo (seção 38)

Até 31/05/2026 havia um mensalista que não é Trabalhador, nem Morador, nem
dormente: a **empresa de logística** com ~30 credenciais de moto e uma
Kangoo (seção 38).

**Por que ele importa para o clustering:**

- Seria **outlier de uma ordem de grandeza** nas duas features de 11.1 —
  ~31 credenciais sob um `Cliente_ID` e dezenas de entradas por dia, contra
  um máximo de 3 veículos e 8 entradas/dia no resto da base.
- Suas ~30 credenciais teriam, individualmente, **padrão de idas e vindas
  ao longo da tarde** — o que num agrupamento por frequência cairia como
  "morador hiperativo". **É uma pessoa andando a pé com um carrinho**
  (38.2), não um veículo circulando.
- **Calendário semanal invertido**: mais movimento em dia útil, menos no
  sábado (38.4), ao contrário de todo o resto da garagem.

→ Ao rodar clustering sobre a janela inteira, **este cliente precisa ser
tratado à parte ou o período segmentado em 01/06** — caso contrário ele
domina a estrutura dos grupos e injeta um perfil que nem é humano no
sentido usual: é movimento de carrinho.

### 11.5b ⚠️ O limite de observação: ninguém percebe um cliente que sumiu

Perguntado sobre a duração das viagens dos moradores, Fabio respondeu que
**não segue padrão e que, com a quantidade de clientes, nem sempre é
possível reparar que um cliente está há dias sem entrar ou sair.**

Isso é mais que uma lacuna de dado — é uma **lacuna de percepção da
operação**, e vale registrar como tal:

- A ausência de um cliente **não gera nenhum evento**. O sistema é
  orientado a transações; não existe alerta de "não aconteceu nada".
- Com ~80 clientes e ~300 movimentos por dia, um veículo parado há duas
  semanas é indistinguível do ruído normal.
- É a mesma cegueira que mantém os **dormentes** (11.3) invisíveis por
  meses.

→ **Recomendação, e ela resolve três problemas de uma vez:** um relatório
recorrente de **"mensalistas sem nenhum movimento nos últimos N dias"**
identificaria (a) os dormentes, (b) os moradores em viagem, e (c) o
cliente em vias de cancelar. É uma consulta simples sobre dado que já
existe, e é a coisa de menor esforço e maior retorno operacional apontada
por este projeto.

### 11.4 ⚠️ O ponto cego da métrica de inadimplência

**Um dos clientes de carro dormentes paga sempre com atraso.** Mas como o
veículo não entra nem sai, **o bloqueio nunca é acionado** — o bloqueio
acontece na cancela, e ele nunca chega à cancela. Ele apenas paga os juros
do atraso.

Isso significa que **a inadimplência medida por `Status = Bloqueado`
subestima sistematicamente a inadimplência real** — e subestima
justamente o caso crônico, o cliente que atrasa todo mês.

| Onde o atraso aparece | Onde não aparece |
|---|---|
| No ERP / financeiro (boleto em aberto) | No log de cancela |

→ **Regra para o relatório:** nunca reportar taxa de inadimplência a partir
do log de movimento. O log de cancela mede **bloqueios efetivados**, não
atrasos. A fonte correta é o ERP. Ver seção 36.

→ É a terceira métrica do projeto que mede a exceção e perde o fenômeno —
ao lado da aderência ao Totem (seção 3.2) e do aviso de cobrança
(seção 36.3).

### 11.5 A leitura de negócio dos dormentes

Vale para o relatório final, e é contraintuitiva nos dois sentidos:

- **São os clientes com melhor margem operacional da base.** Pagam
  mensalidade integral e consomem **zero** custo de operação: nenhuma
  manobra, nenhum uso de elevador, nenhum tempo de manobrista (seção 15/23).
- **E são os de maior risco de churn.** Dois estão parados por falta de
  verba para consertar o carro, e um simplesmente perdeu o interesse pelo
  veículo. Um cliente que não usa o serviço é um cliente que, mais cedo ou
  mais tarde, pergunta por que está pagando por ele.
- **Ocupam estoque que não pode ser revendido.** Numa operação com ~25% das
  vagas contratadas e ~17% de ocupação física (seção 23), três vagas presas
  a veículos imobilizados são três vagas que nunca rotacionam.

→ **Recomendação:** vale a operação saber quem são. Um relatório simples de
"mensalistas sem nenhum movimento nos últimos 60 dias" identifica esse
grupo automaticamente — e é uma lista de contato preventivo, não de
cobrança.

**Implicações para a simulação de dados:**
- O gerador não pode mais tratar "Mensalista" como uma distribuição de
  eventos soltos — precisa simular **clientes individuais com identidade
  ao longo do tempo** (um `cliente_id` fixo por mensalista simulado), cada
  um com um perfil sorteado (trabalhador ou morador) que determina sua
  rotina de idas e vindas ao longo dos meses simulados.

---

## 13. Localização e influência no fluxo de Avulsos (Rua Santa Efigênia)

O estacionamento fica próximo à Rua Santa Efigênia (região comercial,
tradicionalmente forte em comércio de eletrônicos em São Paulo). Isso
influencia diretamente o padrão de fluxo do segmento **Avulso**:

- **Dentro do horário comercial das lojas da região:** fluxo de avulso é
  alto — acompanha o horário de funcionamento do comércio local, não um
  padrão genérico de "cidade".
- **Fora do horário comercial** (antes da abertura, após o fechamento,
  domingos se o comércio local não abrir): fluxo de avulso cai
  significativamente. Nesses períodos, o movimento observado é
  predominantemente de:
  - **Mensalistas moradores** (perfil descrito na seção 11) — usam a
    vaga como garagem, independente do horário comercial do entorno.
  - **Hóspedes do convênio Hotel (Passe Livre)** — padrão turístico,
    também não segue horário comercial.

**Horário comercial da região (confirmado por Fabio):**

| Dia | Abertura | Fechamento | Observação |
|---|---|---|---|
| Segunda a sexta | 8h-9h | 17h-18h | Horário comercial padrão |
| Sábado | 8h-9h | 15h-16h | Fechamento mais cedo, mas é o **dia de maior movimento** |
| Domingo | — | — | Grande maioria das lojas não abre |
| Feriado | ~8h-9h (parcial) | Varia | Estimativa: **40-50% das lojas abrem**. Movimento intermediário — menor que dia útil normal, mas maior que domingo |

**Implicações para análise e simulação:**
- Fora desse intervalo, a proporção de mensalista-morador e hotel no mix
  de tráfego deve aumentar relativamente, mesmo que o volume absoluto
  caia.
- **Sábado é um caso especial:** apesar do fechamento mais cedo (15h-16h
  vs. 17h-18h em dias úteis), é o **dia de maior movimento geral** —
  provavelmente reflete um comportamento de compra concentrado (público
  que só vai à região no fim de semana) mais do que a duração da janela
  comercial. Isso é um padrão não-trivial: não é simplesmente "mais horas
  abertas = mais movimento" — vale destacar esse contraste no relatório
  final como um achado que desafia a intuição óbvia.
- Domingo: fluxo esperado consistente com a seção anterior — quase
  exclusivamente mensalista-morador e hotel, com avulso residual muito
  baixo (comércio fechado).
- **Feriado é um caso intermediário, não deve ser tratado como "domingo":**
  com ~40-50% das lojas abrindo (estimativa de Fabio), o movimento de
  avulso fica entre o de um dia útil normal e o de domingo — nem o pico
  de dia útil, nem o vazio de domingo. Ao simular ou analisar, feriado
  merece sua própria categoria (não reaproveitar a curva de domingo nem a
  de dia útil integralmente).
- ⚠️ **A dinâmica comercial explica a maior parte do fluxo, não a
  totalidade** (confirmado por Fabio, 28/08/2026). Existe entrada e saída
  de avulso **fora do horário comercial**, com duas causas identificadas:
  - **Visitantes de moradores dos prédios do entorno** — inclusive do
    prédio MCMV interligado (seção 32). É a mesma origem que sustenta o
    subsegmento Morador dos mensalistas, aparecendo agora do lado avulso.
  - **Prestadores de serviço** que vão executar algum trabalho na região.

  → **Para a simulação:** a janela de entrada do avulso **não pode ter
  corte duro**. Precisa de uma cauda fina antes da abertura e depois do
  fechamento do comércio. No v12 ela é zero fora de 8h–20h, o que é
  assinatura de sorteio uniforme, não de comportamento.

  → **Para a análise:** avulso fora do horário comercial não é ruído nem
  erro — é um segmento pequeno com causa própria, e a proporção dele
  aumenta relativamente à noite, junto com morador e hotel.

- Esse é um bom exemplo de achado para o relatório final: "o fluxo de
  avulso é majoritariamente explicado pela dinâmica comercial do entorno,
  não por um padrão de mobilidade genérico" — reforça que decisões
  operacionais (equipe, promoções, etc.) deveriam considerar o calendário
  comercial da região.

---

## 15. Identificação de veículo — detalhes confirmados

**Ticket/cupom:** existe e é a chave de identificação principal. O ticket
impresso na cancela de entrada gera um **código de barras + numeração**,
e é por essa numeração que o sistema rastreia o veículo do início ao fim
da permanência. `ticket_id` (já usado no dataset simulado) é um campo real.

**Reconhecimento de modelo/cor do veículo por câmera:** existe, mas **não é
confiável na maioria dos casos** para veículos avulsos/convênio — a
tecnologia de reconhecimento erra com frequência. **Exceção: mensalistas**,
cujo modelo e cor ficam registrados **corretamente**, porque são
preenchidos manualmente no cadastro do cliente (não dependem da câmera).

→ Implicação: `modelo_veiculo`/`cor_veiculo`, se existirem como colunas no
dado bruto, são **confiáveis apenas para o segmento Mensalista** e não
devem ser tratados como dado de qualidade uniforme entre segmentos.

**Número da vaga:** **não é registrado no sistema** — é um processo
totalmente manual/físico:
1. Cliente recebe um **cartão físico** indicando a vaga onde o carro foi
   estacionado.
2. Na saída, o cliente entrega esse cartão no caixa.
3. O caixa comunica **por rádio** ao manobrista qual vaga buscar.

→ Confirma que o estacionamento opera **com manobrista** (não é
autoestacionamento). Isso é relevante para o projeto porque:
- Não há dado digital de ocupação por vaga — qualquer análise de
  "ocupação por vaga individual" é inviável com o sistema atual, apenas
  ocupação agregada (total de vagas ocupadas em um momento, se o sistema
  registrar isso de alguma outra forma — a confirmar).
- O tempo de permanência registrado no sistema (entrada → saída) inclui
  implicitamente o tempo de manobra (buscar/estacionar o carro), não é só
  o tempo "livre" do cliente — vale ter isso em mente ao interpretar
  `permanencia_horas` para permanências muito curtas.

---

## 17. Operação/atendimento — detalhes confirmados

**Login de operador:** existe no sistema, mas **não é usado de forma
consistente**. Só é registrado em situações específicas de gerenciamento
de caixa (ex: abertura/fechamento, sangria) — em cobranças normais do
dia a dia, **não fica registrado quem realizou a transação**.

→ Implicação: não é viável construir uma análise confiável de "taxa de
desvio da orientação do totem por atendente/turno" (ideia levantada na
seção 3) usando esse campo, pois ele não é preenchido de forma
sistemática nas transações comuns. Se quiser investigar esse ângulo, seria
necessário outro proxy (ex: horário da transação associado à escala de
turno, se houver esse controle em algum lugar).

### 17.1 Quadro e divisão de papéis — confirmado em 06/09/2026

**10 funcionários:** 1 gerente, 2 caixas e 7 manobristas (5 com jornada de
36 h/semana, 2 com 44 h).

⚠️ **Os papéis não são estanques.** As operações simples de caixa — cobrança,
desconto de selo, ativação de Passe Livre — são feitas **também pelos
manobristas quando necessário. Todos sabem fazer.**

**O papel do caixa é controle financeiro**, não atendimento: organização,
**fechamento diário** e conferência de todos os valores.

→ **Implicação direta para a seção 21.** A correção retroativa de forma de
pagamento que aquela seção descreve tem **causa estrutural, não de
treinamento pontual**: a operação de cobrança é *distribuída* entre 7 pessoas
que a fazem eventualmente, e a conferência é *centralizada* em 2 pessoas no
fechamento. Errar a forma de pagamento não é descuido — é o resultado
esperado de uma função executada de vez em quando por quem tem outra função
principal.

→ **Implicação para a aderência ao Totem (seção 3).** O manobrista que atende
uma cobrança num momento de fila tem mais motivo para resolver no caixa do
que orientar o cliente ao totem. O desvio da orientação e o erro de digitação
têm a mesma raiz.

→ **Implicação para dimensionamento.** O manobrista ocupado no caixa **não
está manobrando**. A capacidade efetiva por pessoa é menor do que a contagem
pura de manobras sugere, e o tempo gasto em caixa nunca foi medido.

→ **Não há buraco de cobertura de cobrança.** Em dia útil o caixa vai até
19:30 e no sábado até 16h, mas a garagem opera 24h — e isso não é lacuna,
porque quem está no prédio consegue cobrar.

### 17.2 Escala de trabalho — confirmada em 06/09/2026

**Segunda a sexta**

| Quem | Entra | Sai |
|---|---|---|
| Manobrista 1 | 06:00 | 12:30 |
| Manobrista 2 | 06:00 | 15:00 |
| Manobrista 3 | 08:30 | 15:00 |
| Manobrista 4 | 12:00 | 18:30 |
| Manobrista 5 | 15:00 | 21:30 |
| Manobrista 6 | 15:30 | 22:00 |
| Manobrista 7 | 22:00 | 06:00 |
| Gerente | 08:00 | 17:00 |
| Caixa 1 | 08:30 | 17:30 |
| Caixa 2 | 10:30 | 19:30 |

**Sábado**

| Quem | Entra | Sai |
|---|---|---|
| Manobrista 1 | 06:00 | 12:30 |
| Manobrista 5 | 06:30 | 13:00 |
| Manobrista 3 | 09:00 | 15:30 |
| Manobrista 6 | 11:00 | 17:30 |
| Manobrista 4 | 11:30 | 18:00 |
| Manobrista 2 | 18:00 | 06:00 (cobre a folga do M7) |
| Gerente | 10:00 | 14:00 |
| Caixa 1 | 08:00 | 12:00 |
| Caixa 2 | 12:00 | 16:00 |

**Intervalos (confirmado em 06/09/2026):**

| Quem | Presença | Intervalo | Trabalho | Jornada |
|---|---|---|---|---|
| Manobristas de turno 6h30 (M1, M3, M4, M5, M6) | 6,5 h | **30 min** | 6 h | 36 h/semana |
| Manobrista 2 (turno de 9 h) | 9 h | **1 h** | 8 h | 44 h/semana |
| **Manobrista 7 (noite)** | 8 h | **nenhum** | 8 h | 44 h/semana |
| Gerente e caixas | 9 h | 1 h | 8 h | — |

O manobrista da noite é o único sem intervalo, **por trabalhar no horário de
movimento mais baixo** (22h–6h). As três configurações fecham exatamente nas
jornadas declaradas.

⚠️ **A duração do intervalo é conhecida; o horário não.** E isso não é
detalhe: a cobertura efetiva em cada hora depende de quando cada um sai.
Modelando o melhor e o pior caso sobre a curva de demanda, **às 8h da manhã a
equipe disponível fica entre 1,5 e 3 pessoas** — numa hora de ~30 manobras. A
distância entre os dois cenários é **o que uma regra de horário de intervalo
resolveria**, e não exige dado novo nenhum para ser decidida.

→ Para qualquer conta de capacidade, usar **horas efetivas** (46 h em dia útil,
41 h no sábado), não horas de presença (49,5 h e 44,5 h).

**Domingo:** todos folgam. São **dois turnos de 8 h pagos por fora** (06:00–14:00
e 14:00–22:00), **sem escala fixa** — os manobristas decidem entre si quem vem
ganhar o extra. É o único dia em que o custo de operação é variável.

→ **Uso na análise.** A escala é o **primeiro dado operacional real** do
projeto que não depende do dataset sintético. Serve para três coisas:
1. ⚠️ **Não serve para dimensionar equipe.** Uma versão do painel tinha um
   otimizador de turnos e uma métrica de "manobristas necessários". **Foi
   removida.** Ela dependia de dois números não verificáveis: a curva horária
   de movimento (que no dataset é design do gerador) e o ritmo por manobrista
   — **que nunca foi cronometrado e que a própria operação não consegue
   estimar, porque não segue padrão fixo**. Multiplicar os dois devolvia uma
   recomendação com aparência de precisão.
   → **O que destravaria:** cronometrar algumas dezenas de manobras. É barato
   e transformaria a escala de descrição em dimensionamento.
2. **Validar a forma da curva de demanda.** Correlação entre cobertura e
   demanda de **+0,80 em dia útil**. ⚠️ Não é validação independente: o
   gerador e a escala vêm da mesma fonte de conhecimento. É teste de
   consistência.
3. **Achar desalinhamento.** No **sábado** a correlação cai para **+0,69** — a
   cobertura se concentra entre 11h e 12h enquanto a demanda pica às 8h e de
   novo às 15h–16h.

**O turno da noite existe por cobertura, não por demanda.** Das 22h às 6h o
movimento é quase nulo, mas a Cancela 1 é o único ponto de entrada e opera
24h. É restrição de serviço, e nenhuma otimização de demanda pode removê-la.

**Estrutura física de cancelas (confirmado por Fabio):** o pátio do
estacionamento é composto por **dois pisos de acesso**: subsolo e térreo.
(Não confundir com os 21 andares do sistema de elevadores — seção 23 —
que ficam acima desses dois pisos de acesso, onde os carros de fato ficam
guardados.)

O sistema Softcase identifica **3 códigos de cancela**, embora fisicamente
sejam apenas 2 estruturas (o subsolo tem uma única cancela bidirecional,
dividida em 2 códigos no sistema conforme o sentido do movimento):

| Cancela (sistema) | Local físico | Sentido | Horário de funcionamento |
|---|---|---|---|
| **Cancela 1** | Subsolo | Entrada | 24h — **único ponto de entrada** de qualquer veículo, sem exceção |
| **Cancela 2** | Subsolo | Saída | 24h, mas só concentra saída fora do horário de funcionamento do térreo |
| **Cancela 3** | Térreo | Saída (exclusiva — não permite entrada) | Seg-sex 8h30–19h, sáb 8h–16h. **Fechado inteiro aos domingos e feriados.** |

- Fora do horário de funcionamento da Cancela 3 (incluindo domingos e
  feriados por completo), toda saída de veículo passa pela Cancela 2
  (subsolo).
- **Motos e clientes de Carga e Descarga entram e saem sempre pelo
  subsolo** (Cancelas 1 e 2) — nunca usam a Cancela 3 do térreo, em
  nenhum horário.
- O sistema **não identifica qual andar ou elevador** foi usado — só a
  cancela.

→ Implicações para análise:
- Se o dado bruto tiver o campo de cancela, ele serve como sinal indireto
  de **horário/dia da semana** (já que a Cancela 3 só opera em janela
  fixa e conhecida) — não como proxy de intensidade de movimento geral,
  como uma leitura anterior desse dado poderia sugerir.
- Interessante para cruzar com os horários de pico já mapeados (Santa
  Efigênia, horário comercial, sábado — seção 13): por exemplo, checar se
  o volume de saída pela Cancela 2 fora do horário do térreo é
  consistente com o esperado para mensalistas-moradores e hóspedes de
  hotel (seção 13).

**Alocação de vaga por cartão (relevante só para carro):**
- A escolha de vaga é feita através de **cartões físicos disponíveis na
  recepção** — o cliente leva o cartão indicando andar e vaga (seção 15).
- **Problema operacional identificado:** mensalistas circulam muito
  (entram/saem repetidamente), e por isso **perdem ou esquecem o cartão**
  com frequência. Diante disso, a gestão adotou a prática de **não
  entregar mais cartão** para alguns desses mensalistas.
- Nesses casos, o manobrista escolhe a vaga livremente (sem cartão
  guiando a escolha), e **na saída, outro manobrista precisa procurar
  onde o veículo está**.
- **Solução adotada (sugestão do próprio Fabio):** carros de mensalistas
  **sem cartão** são centralizados sempre no **mesmo elevador (elevador
  2)** — reduz a busca de "3 elevadores possíveis" para "1 elevador
  certo", agilizando a saída desses clientes.
- **Consequência esperada nos dados:** o elevador 2 deve concentrar
  **volume desproporcional** de uso comparado aos elevadores 1 e 3 — não
  por ser mais movimentado organicamente, mas por essa regra
  administrativa de centralização. Importante não interpretar esse
  desbalanceamento como sinal de "gargalo" ou "elevador mais popular" sem
  considerar essa causa raiz.
- Vale medir, se o dado permitir, o **percentual de mensalistas sem
  cartão** — é um indicador indireto de um problema operacional (perda de
  cartão) que pode render uma recomendação prática no relatório (ex:
  cartões com chaveiro/fixação mais segura, ou digitalizar esse processo).

---

## 19. Financeiro — detalhes confirmados

**Tabela de valores completa:** confirmada na seção 29 (tabela antiga e
tabela atual, com data de corte em 01/06/2026 — seção 9).

**Troco:** o sistema **não registra** valor recebido em dinheiro nem
troco dado — apenas o valor final cobrado.

**Cancelamento/estorno:** **não existe** essa categoria de transação no
sistema. Não é necessário tratar esse caso na limpeza/auditoria dos dados.

**Ticket perdido:** existe uma função para esse cenário no sistema, mas
**não é utilizada por decisão da gerência** (por má conduta — ou seja, a
gerência optou por não usar essa funcionalidade por má experiência/risco
de fraude associado a ela). Na prática, quando um cliente perde o ticket:
- O funcionário pede a **placa do veículo** ao cliente.
- Busca **manualmente** no sistema qual registro de entrada corresponde
  àquela placa.
- Realiza a cobrança normalmente com base no horário de entrada
  encontrado.

→ Implicação: não há uma tarifa fixa de "ticket perdido" nem uma
categoria de cobrança especial para esse caso — o valor cobrado segue a
mesma lógica normal (permanência real), só que com um passo manual de
busca a mais. Não deve gerar distorção sistemática em `valor_cobrado` ou
`permanencia_horas` por esse motivo.

---

## 21. Status/qualidade da transação — detalhes confirmados

**Transações canceladas/anuladas:** não existe (já confirmado na seção
19, reforçado aqui).

**Correção manual de forma de pagamento:** existe um processo de ajuste
retroativo — a **líder de caixa**, ao final do dia, corrige manualmente
no sistema a forma de pagamento de transações que foram registradas
incorretamente. Isso acontece por falta de treinamento adequado: em
cobranças manuais (ex: convênio selo, passe livre, moto — que exigem
intervenção do operador), o funcionário às vezes esquece de selecionar a
forma de pagamento correta na hora, e isso é corrigido depois no fechamento
do dia.

→ Implicação para o dado: o campo `forma_pagamento` no dado bruto reflete
o valor **já corrigido** ao final do dia (pressupondo que a correção
tenha realmente sido feita) — não necessariamente o que foi digitado no
momento exato da cobrança. Isso é bom para a qualidade final do dado, mas
significa que **não é possível auditar, a partir do dado bruto, a taxa
real de erro de digitação do operador no momento da cobrança** — só se
enxerga o resultado já corrigido (quando a correção realmente ocorre).
Vale ter isso em mente ao interpretar padrões de forma de pagamento —
pequenas inconsistências residuais podem ainda existir se algum caso
escapar da correção da líder de caixa.

**Retentativas de pagamento (cartão recusado etc.):** não existe esse
registro no sistema.

---

## 23. Capacidade/ocupação — detalhes confirmados

**Snapshot de ocupação em tempo real:** não existe no sistema — como a
alocação de vaga é manual (cartão físico entregue ao cliente, sem
registro digital — ver seção 15), o sistema **não sabe quantas vagas
estão ocupadas** em um dado momento.

**Capacidade total do estacionamento:** **21 andares × 18 vagas por
andar = 378 vagas** no total (capacidade nominal máxima) — **esse número
se refere às vagas do sistema de elevadores, ou seja, apenas carros**
(ver detalhe sobre motos logo abaixo).

**Motos — operação totalmente separada dos carros:**
- Motos **não usam os elevadores** — ficam num **subsolo**, em local
  próprio indicado ao cliente.
- O **próprio cliente estaciona a moto** sozinho, sem intervenção de
  manobrista — diferente de carros, que dependem do manobrista +
  elevador (seção 15/17).
- O estacionamento fica responsável apenas pela **guarda** da moto, não
  pela movimentação dela.
- **Sem custo operacional** associado à moto (não ocupa elevador, não
  ocupa tempo de manobrista).
  ⚠️ **Precisão de 28/08/2026:** isso vale **por moto**, não em volume. O
  fluxo intenso da empresa de logística (seção 38) chegou a atrapalhar a
  operação do estacionamento. O custo da moto em escala não é de manobra —
  é de **congestionamento do acesso**, e não aparece em nenhuma métrica do
  sistema.
- Volume de moto é **relativamente baixo** comparado a carro, e é
  **raro** um cliente de moto ficar estacionado por mais de 12h.

**Capacidade de motos (subsolo):** a área do subsolo originalmente
correspondia a **9 vagas de carro**, mas atualmente é utilizada para
motos — comporta cerca de **60 motos** no total.

⚠️ **A ocupação de moto tem dois regimes distintos dentro da janela de
análise** (precisão adicionada em 28/08/2026 — ver seção 38):

| Período | Simultâneas em dia de pico | % das ~60 vagas |
|---|---|---|
| **fev–mai/2026** (com a empresa de logística) | **~50** | **~83%** |
| **jun–ago/2026** (após a saída dela) | ~20 | ~33% |

O número de **~20 motos**, informado por Fabio, é a **situação atual** — e a
**maioria delas é mensalista** (não avulso/selo/carga-e-descarga). Até maio
havia cerca de 30 motos adicionais de um único cliente corporativo.

⚠️ **A ocupação de moto do período anterior a junho é subestimada pelo
sistema por construção.** Os motoboys usavam o cartão de acesso da moto
para passar com carrinho de carga a pé, e cada uma dessas passagens é
registrada como saída de moto — subtraindo da soma cumulativa um veículo
que continua estacionado. Ver seção 38.2. **Os ~83% não são recuperáveis a
partir do dado.**

→ Implicações importantes para o projeto:
- A capacidade de **378 vagas é só de carro** (elevadores) — a
  capacidade de moto (~60 vagas no subsolo) deve ser tratada como um
  **denominador separado** ao calcular taxa de ocupação de moto, nunca
  somada ao total de carro nem misturada no mesmo percentual.
- Com pico observado de ~20 motos simultâneas para uma capacidade de 60,
  a ocupação de moto está bem abaixo do teto mesmo nos dias mais cheios —
  diferente do que se espera do lado carro, que historicamente já operou
  bem mais próximo da lotação (seção 32). Isso é outro ângulo de
  comparação interessante para o relatório: espaço para crescimento no
  segmento moto é proporcionalmente maior do que no segmento carro.
- Como a maioria das motos estacionadas é mensalista, o volume de moto
  avulsa/selo/carga-e-descarga que efetivamente usa o subsolo em um dado
  momento tende a ser pequeno — reforça que esse segmento (moto avulsa)
  é uma fatia pequena dentro de uma fatia já pequena (moto no geral).
- Para carros, `permanencia_horas` inclui tempo de manobra (elevador +
  manobrista). **Para motos, isso não se aplica** — o tempo registrado é
  mais próximo do tempo "real" de uso do cliente, sem componente
  logístico embutido. Vale ter isso em mente ao comparar diretamente a
  permanência de carro vs. moto (não é uma comparação 100% "justa" sem
  considerar essa diferença estrutural).
- Sendo raro moto ficar >12h, o teto de "diária de 12h" (seção 29) quase
  nunca deve ser acionado para o segmento moto na prática — útil para
  validar se o dado real bate com essa expectativa quando disponível.
- ⚠️ **Precisão adicionada em 28/08/2026:** o "é raro moto ficar >12h"
  refere-se a **quem paga por permanência** (avulso, selo, carga e
  descarga). **Não vale para moto de mensalista**, que fica na vaga 24/7
  por definição do contrato — a moto do perfil Morador dorme na garagem
  todos os dias. No v12, 0,0% das motos avulsas passam de 12h contra ~30%
  do conjunto, e toda a diferença é mensalista morador. Como a **maioria
  das motos é mensalista** (registrado acima), qualquer métrica de
  "permanência de moto" sem filtrar por segmento vai parecer contradizer
  esta seção sem contradizê-la de fato.

**Acesso de Mensalistas — leitura de placa vs. cartão de acesso
(confirmado por Fabio):**
- **Mensalista de carro (regra geral):** o sistema lê a placa
  automaticamente e a cancela **abre sozinha**, sem necessidade de cartão
  físico.
- **Mensalista de moto:** como o sistema **não consegue ler placa de
  moto** (câmera captura só pela frente — seção 4), todo mensalista de
  moto recebe um **cartão de acesso** com os dados do cliente, apresentado
  num leitor na cancela para liberar tanto entrada quanto saída.
- **Exceção rara (1-2 casos conhecidos):** mensalistas de **carro** com a
  placa danificada também recebem cartão de acesso, usado na entrada e na
  saída, como contingência ao mesmo problema já documentado na seção 4.

→ Implicações para o projeto — **campo confirmado como existente no
sistema, não é mais hipótese**:
- O dado bruto tem um campo de **método de entrada** (leitura automática
  de placa vs. cartão de acesso), que serve como proxy adicional (e mais
  confiável que `placa_vazia`) para identificar mensalistas de moto — já
  que, para mensalista, o cartão de acesso é praticamente sinônimo de "é
  moto", com raríssimas exceções conhecidas (carro com placa danificada).
- Diferente do avulso (onde `placa_vazia` é o único proxy disponível e
  tem ambiguidade — seção 4), para **mensalista** existe um sinal quase
  determinístico (`metodo_acesso = cartao`) que resolve a ambiguidade com
  muito mais confiança, dado o número ínfimo de exceções conhecidas.

**Funcionamento físico — garagem automática por elevadores:** o
estacionamento é uma **garagem automática operada por elevadores**, não
uma estrutura de rampas convencional. Detalhes:
- **3 elevadores** ao todo.
- O manobrista entra com o carro no elevador e sobe até o andar desejado.
- Em cada andar, cada elevador dá acesso a **6 vagas**, identificadas por
  letras de **A a F**:
  - Vagas **A, B, C**: estacionamento de **ré**.
  - Vagas **D, E, F**: estacionamento de **frente**.
- Confirma a matemática da capacidade: 3 elevadores × 6 vagas × 21
  andares = 378 vagas (bate com o total já registrado acima).
- **Fluxo operacional:** como o volume de carros não é tão grande, **só 2
  dos 3 elevadores costumam ser usados por vez** — o terceiro fica como
  reserva/reforço para horários de maior movimento.
- **Confirmado (seção 17):** o sistema Softcase não identifica qual
  andar ou elevador foi utilizado por transação — apenas qual cancela
  (subsolo entrada, subsolo saída, ou térreo saída).

→ Implicações para o projeto:
- Isso reforça ainda mais por que `permanencia_horas` inclui tempo de
  manobra (seção 15) — nesse modelo de garagem automática, o tempo de
  "buscar o carro" envolve elevador, não só caminhar até uma vaga, o que
  pode ser proporcionalmente mais demorado que numa garagem convencional.
- O uso de "2 de 3 elevadores" na maior parte do tempo não pode ser
  verificado diretamente no dado (sistema não registra elevador/andar),
  mas vale mencionar essa limitação de capacidade operacional como
  contexto qualitativo ao interpretar picos de fila ou tempo de espera,
  se esse tipo de dado existir por outra via.

→ Implicação para o projeto: como não há snapshot direto de ocupação, a
**taxa de ocupação por hora precisa ser inferida**, não lida diretamente
do sistema. Isso pode ser calculado a partir do próprio histórico de
entrada/saída: para qualquer instante `t`, ocupação estimada = número de
veículos cujo `entrada <= t` e (`saida > t` ou `saida` ainda não
ocorreu). Esse cálculo é perfeitamente viável com o dado bruto de
entrada/saída (não depende de nenhum campo adicional), mas é importante
deixar claro na metodologia do relatório que é uma **ocupação estimada**,
não uma leitura direta do sistema.

- Vale usar a capacidade de 378 vagas como denominador para expressar
  ocupação em percentual (ex: "às 14h de sábado, ocupação estimada de
  92%"), o que é mais interpretável para quem for ler o relatório do que
  só o número absoluto de veículos.
- Como a recarga elétrica ocupa 2 dessas vagas (ver seção 6), pode valer
  a pena mencionar isso como uma nota lateral (vagas de recarga são parte
  do total, não adicionais).

---

## 25. Convênios — hotéis e lojistas identificados

**Hotéis conveniados (Passe Livre):** 4 hotéis identificados —
quatro hotéis próximos, identificados no documento interno.
(**Nomes removidos da versão pública.**)

**Distribuição de uso entre hotéis:** o **hotel mais próximo** concentra
aproximadamente **90% dos hóspedes que usam o Passe Livre** — é o hotel
mais próximo fisicamente do estacionamento e foi o **primeiro a ser
conveniado**, o que provavelmente explica a concentração (proximidade +
tempo de relacionamento/divulgação do convênio). Os outros 3 hotéis
dividem os ~10% restantes.

→ Implicação: com essa concentração, análises "por hotel individual"
provavelmente não terão volume suficiente de dado para os 3 hotéis
menores serem estatisticamente relevantes de forma isolada — na prática,
a análise de Passe Livre deve se comportar, em grande parte, como uma
análise desse hotel, com os demais tratados como cauda pequena
(mencionar a existência deles e a concentração, sem necessariamente
segmentar cada um profundamente).

### 25.1 Duração da estadia do hóspede — confirmado em 28/08/2026

> **Dado novo.** A duração da estadia do hóspede nunca tinha sido
> registrada, e o gerador vinha usando um mínimo de 2 diárias — o que
> elimina justamente o caso mais comum.

**Distribuição real, segundo Fabio:**

- **Boa parte dos hóspedes fica apenas 1 diária** — é o caso mais
  frequente, não a exceção.
- Os demais variam **geralmente até 4 diárias**.
- **A grande maioria alterna entre 1 e 4 diárias.**
- Estadias mais longas existem, mas são **casos raros**.

**Distribuição sugerida para a simulação** (média ≈ 2,1 diárias):

| Diárias | Peso |
|---|---|
| 1 | 45% |
| 2 | 25% |
| 3 | 15% |
| 4 | 10% |
| 5 a 7 | 5% (cauda rara) |

→ **Implicação de peso para o projeto.** O Passe Livre é ~29% da receita
total e mais de **50% da receita transacional** — é a maior fonte de
receita por ticket da operação. O número de diárias é, portanto, **o
parâmetro isolado com maior efeito sobre a receita simulada**. Um gerador
com mínimo de 2 diárias (média 3,0) infla o ticket médio do hotel em
aproximadamente 45% em relação a esta distribuição, e infla também a
ocupação estimada, porque estadias de hotel são longas e ocupam vaga o
tempo todo.

→ Cuidado ao validar: como a maioria fica 1 diária, **o ticket médio do
hotel é bem menor do que a média de permanência sugere** — a distribuição
é assimétrica à direita, e média e mediana contam histórias diferentes.
Reportar as duas.

---

**Lojistas conveniados (Convênio Selo):** rastreabilidade **não é
viável**. Detalhes confirmados por Fabio:
- O controle de venda de cartelas de selo é **manual**, sem registro
  digital tipo "loja X comprou Y selos" — a informação pode estar
  anotada em caderno pelo financeiro, sem fácil acesso (exigiria
  conferência mês a mês).
- Os selos são **fisicamente neutros/anônimos**: não têm nenhuma marca
  de identificação da loja de origem. Na cobrança, o sistema só sabe
  **quantos** selos foram apresentados, nunca **de qual loja**.
- Selos **não têm validade** — uma loja pode comprar 50 selos e
  distribuir em ritmo próprio (ex: 1 por mês), então nem o momento da
  compra da cartela se relaciona de forma previsível com o momento de uso.
- Cada lojista tem seu próprio critério de distribuição (alguns dão o
  selo só por visita/negociação, outros exigem valor mínimo gasto) — mais
  uma camada de variabilidade que não é capturada em lugar nenhum
  digitalmente.

### 25.1 Preço de venda do selo e margem do programa

> **Seção nova em 28/08/2026.** O preço de venda ao lojista era o dado que
> faltava para saber se o convênio dá lucro. Confirmado por Fabio.

| Regime | Preço por selo | Cartela de 50 |
|---|---|---|
| Até 31/05/2026 | R$ 8,00 | R$ 400,00 |
| A partir de 01/06/2026 | **R$ 9,00** | **R$ 450,00** |

**O selo é vendido abaixo do que desconta.** Na tabela vigente ele custa
R$ 9,00 ao lojista e abate R$ 15,00 (tarifa de 1 hora, seção 29).

**Mas o custo real é limitado pelo valor da conta**, e é isso que torna a
margem contraintuitiva: quem apresenta 3 selos numa conta de R$ 23 recebe
R$ 23 de abono, não R$ 45 — o excedente transborda e evapora. Resultado:

| Permanência | Conta cheia | 1 selo | 2 selos | 3 selos |
|---|---|---|---|---|
| 30 min | R$ 10 | −R$ 1 | **+R$ 8** | **+R$ 17** |
| 1 h | R$ 15 | −R$ 6 | **+R$ 3** | **+R$ 12** |
| 2 h | R$ 23 | −R$ 6 | −R$ 5 | **+R$ 4** |
| 3 h ou mais | R$ 30 | −R$ 6 | −R$ 12 | −R$ 3 |

*(carro, tabela vigente; margem = preço de venda − abono efetivo)*

Duas leituras de negócio, ambas derivadas só das tabelas de preço — não
dependem de dado sintético nem de estimativa:

1. **Um selo apresentado sozinho dá prejuízo em 100% dos casos.** Para dar
   margem seria preciso uma conta abaixo de R$ 9, e o mínimo da tabela é
   R$ 10. Não existe permanência que salve.
2. **A margem inverte com a quantidade.** O lojista que distribui 3 selos
   de uma vez subsidia o estacionamento; o que distribui 1 é subsidiado
   por ele. É o oposto da intuição de "quanto mais desconto, pior para
   mim".

**Recomendação:** o preço do selo (R$ 9) está descolado da tarifa que ele
desconta (R$ 15). Alinhar os dois — subir o selo para a faixa de R$ 12–13,
ou criar um **selo de meia hora** (R$ 10 de abate) — leva o programa de
levemente negativo para neutro **sem mudar nada do que o lojista entrega
ao cliente final**. O reajuste de R$ 8 para R$ 9 em 01/06 já andou nessa
direção e quase zerou a diferença.

**Limite que permanece:** selos não têm validade, então a receita é
reconhecida na **venda da cartela** e o custo no **uso do selo**, meses
depois. Qualquer cálculo de margem por período é uma imputação (selos
usados × preço vigente), não faturamento observado. Só o registro digital
da venda de cartelas fecha isso — segue sendo a recomendação de maior
retorno analítico por menor esforço no projeto.

**Estimativa de lojas conveniadas:** entre 15 e 20 lojas (estimativa de
Fabio, sem contagem exata). A região tem **centenas de lojas** no total —
ou seja, a taxa de penetração do convênio é baixa, indicando **espaço de
crescimento relevante** para o programa.

**Achado de negócio interessante:** alguns clientes **Mensalistas que são
donos de loja** (perfil "Trabalhador", seção 11) **não são conveniados**
com o próprio estacionamento onde estacionam — e alguns desses lojistas
mensalistas têm **convênio de selo com um concorrente** (outro
estacionamento da região) em vez deste estacionamento. Isso é um ângulo forte
para o relatório final: o estacionamento já tem relação comercial direta
(mensalista) com lojistas que poderiam ser convertidos em parceiros de
convênio, mas não são — uma oportunidade de expansão de baixo custo
(cliente já conhecido, só falta oferecer o convênio) que pode ser citada
como recomendação de negócio, sem necessidade de dado quantitativo
adicional para sustentar esse ponto (é uma observação qualitativa válida
por si só).

**Conclusão sobre rastreabilidade:** segmentar Convênio Selo por lojista
individual **não é possível** com os dados disponíveis, nem vale o
esforço de tentar reconstruir manualmente. O segmento deve permanecer
**agregado** no projeto, mas os dois pontos de contexto acima (quantidade
estimada de lojas conveniadas e a oportunidade de conversão de
mensalistas-lojistas) são úteis para a seção de recomendações do
relatório final, mesmo sem dado granular por loja.

---

## 27. Fatores externos — clima e eventos

**Clima:** segundo observação de Fabio, **não há diferença perceptível**
no fluxo de veículos associada a variações climáticas (chuva, etc.).
Não deve ser tratado como variável prioritária de análise — não
descartar completamente, mas não vale investir esforço de coleta de
dados climáticos externos como prioridade alta para este projeto.

**Localização e eventos:** o estacionamento fica no **Centro Histórico de
São Paulo**, região com **proximidade de diversos eventos**.
(*Endereço exato removido da versão pública.*)

→ Implicação: diferente do clima, eventos na região podem ser um fator
relevante de sazonalidade para o segmento Avulso (e possivelmente
Convênio Selo, se atrelado a fluxo de comércio) — picos atípicos de
movimento em dias específicos podem ser explicados por eventos pontuais
no entorno, não apenas pelo padrão semanal já mapeado (comércio da Santa
Efigênia, seção 13). Se houver tempo/interesse, cruzar datas de picos
anômalos identificados na EDA com calendário de eventos da região central
de São Paulo pode ser uma análise adicional de valor — mas não é uma
fonte de dado que precisa ser resolvida antes de começar o projeto, pode
entrar como enriquecimento posterior.

---

## 29. Tabela de preços — valores confirmados (antiga e atual)

**Tabela ANTIGA** (vigente até 31/05/2026 — ver data de corte na seção
9), confirmada por Fabio (correção de uma foto enviada anteriormente, que
era na verdade de ~3 anos atrás e não deve ser usada):

| | Meia hora | 1 hora | Hora adicional | 12 horas | 24 horas |
|---|---|---|---|---|---|
| **Carro — Seg a Sex** | R$ 8,00 | R$ 12,00 | **R$ 6,00** | R$ 25,00 | R$ 50,00 |
| **Carro — Sáb/Dom/Feriado** | R$ 10,00 | R$ 15,00 | **R$ 6,00** | R$ 40,00 | R$ 60,00 |
| **Moto — Seg a Sex** | R$ 6,00 | R$ 12,00 | **R$ 6,00** | R$ 15,00 | R$ 30,00 |
| **Moto — Sáb/Dom/Feriado** | R$ 8,00 | R$ 15,00 | **R$ 6,00** | R$ 30,00 | R$ 30,00 |

> ⚠️ **CORRIGIDO em 28/08/2026.** Esta tabela trazia **R$ 8,00** de hora
> adicional na tabela antiga. O valor correto é **R$ 6,00** — era o
> *documento* que estava desatualizado, e o código do gerador estava certo.
>
> **Consequência:** a hora adicional **também foi reajustada** em 01/06,
> de R$ 6,00 para R$ 8,00 (**+33%**). Ela não aparecia como item do reajuste
> justamente porque o documento a registrava já com o valor novo.

> **Confirmado por Fabio:** o valor igual entre diária de 12h e 24h para
> moto no fim de semana/feriado (R$30,00 nos dois casos) **não é
> inconsistência**. O custo operacional de guardar uma moto é praticamente
> nulo (não ocupa elevador, não ocupa manobrista — seção 23), e é raro uma
> moto ficar estacionada de um dia para o outro. Por isso, o valor de
> R$30,00 na diária de 24h reflete apenas uma **taxa de guarda por período
> longo**, não um cálculo proporcional às horas adicionais. É intencional,
> não erro de tabela.

### 29.1 Mensalidade — valores e política de desconto

> **Seção nova em 28/08/2026.** Os valores de mensalidade **existiam apenas
> no código do gerador** e não estavam documentados em lugar nenhum, apesar
> de a mensalidade ser **45,4% da receita total**. Confirmados por Fabio.

⚠️ **A mensalidade NÃO muda no marco de 01/06/2026.** Estes valores vigoram
desde 2025, antes do início da janela de análise. O reajuste de 01/06
(seção 9) atinge apenas a tabela de avulso. Verificado no dado: R$ 275,55
por vaga antes do corte e R$ 276,18 depois.

**Moto — dois valores, com legado preservado:**

| Valor | Situação |
|---|---|
| R$ 180,00 / vaga | Valor **antigo**, mantido para parte dos clientes |
| R$ 200,00 / vaga | Valor **atual**, para os demais |

Não há outros valores. A base fica em torno de meio a meio entre os dois.
É o mesmo padrão de preço legado já visto no selo (R$ 8 → R$ 9) e na
tabela de avulso: **o valor novo não é aplicado retroativamente a quem já
era cliente.**

**Carro — tabela cheia com desconto discricionário:**

| | Valor |
|---|---|
| **Valor de tabela** | **R$ 310,00 / vaga** |
| Faixa praticada | R$ 250,00 a R$ 310,00 / vaga |

⚠️ **Não existe regra de desconto.** A gerência aplica abatimentos caso a
caso, sem critério formalizado. O padrão observável é que **clientes com
mais vagas recebem mais desconto por vaga** — mas isso é tendência, não
política escrita.

Desconto efetivo medido no v12:

| Vagas do cliente | R$/vaga | Desconto sobre a tabela |
|---|---|---|
| 1 | 293 | 5,5% |
| 2 | 280 | 9,7% |
| 3 | 265 | 14,5% |
| **Média** | **288** | **7,1%** |

→ **Valor do desconto concedido:** sobre 95 vagas de carro faturadas, a
receita a preço cheio seria de R$ 29,4 mil/mês contra R$ 27,4 mil
realizados — **R$ 2.081/mês, ou ~R$ 25 mil/ano** de desconto discricionário.

→ **Recomendação:** existe um desconto por volume *de fato* (5,5% / 9,7% /
14,5% conforme o número de vagas). Formalizá-lo como política escrita não
mudaria a receita, mas tornaria a decisão auditável e removeria a
arbitrariedade do caso a caso. É o mesmo raciocínio da seção 25.1 sobre o
preço do selo: o valor não está errado, está **indocumentado**.

---

**Tabela ATUAL** (vigente a partir de 01/06/2026, unificada — todos os
dias com o mesmo valor):

| | Meia hora | 1 hora | Hora adicional | 12 horas | 24 horas |
|---|---|---|---|---|---|
| **Carro** | R$ 10,00 | R$ 15,00 | R$ 8,00 | R$ 30,00 | R$ 60,00 |
| **Moto** | R$ 8,00 | R$ 12,00 | R$ 8,00 | R$ 20,00 | R$ 40,00 |

> ⚠️ **A coluna "12 horas" não é uma faixa de tarifa — é um TETO** (esclarecido por
> Fabio em 28/08/2026). Não existem tarifas de 4, 5, 6 horas: existe R$ 8,00 de hora
> adicional, com a cobrança limitada a R$ 30,00 para qualquer permanência **de até
> 12 horas**. Na prática o teto é atingido já na **3ª hora** (10 · 15 · 23 · 30), e
> da 3ª à 12ª o cliente ocupa a vaga sem custo marginal.
>
> **A faixa de 24 horas, essa sim, é pouco usada**, e tem público próprio: quem vai
> **passar a noite e não está em hotel conveniado**. Não confundir com o Passe Livre
> (seção 25), que é convênio.

**Modelo de cálculo (ambas as tabelas):** até 30min → tarifa de meia hora;
até 1h → tarifa de 1 hora; entre 1h e 12h → tarifa de 1 hora + (horas
excedentes × tarifa de hora adicional), limitado ao valor da diária de
12h (não pode custar mais que a diária); entre 12h e 24h → diária de 24h.
**Desconto de selo:** subtrai o valor de "1 hora" da tabela vigente, uma
vez por selo, do valor cheio já calculado (ver seção 12 dos scripts —
fórmula validada com exemplos reais informados por Fabio).

---

## 30. Segmento: Carga e Descarga

> **CORRIGIDO em 28/08/2026.** A versão anterior desta seção afirmava que
> o segmento foi *"criado junto com a tabela de preços atual"* e que
> *"só existe no dado a partir de 01/06/2026 — não retroage"*. **As duas
> afirmações estavam erradas** e contradiziam o próprio parágrafo seguinte,
> que dizia que os R$ 5,00 valem para as duas tabelas.
>
> **Confirmado por Fabio: o segmento existe durante todo o período
> analisado e sempre custou R$ 5,00.** O que nasceu em 01/06/2026 foi a
> tabela geral de preços, não este serviço. A tarifa de C&D **não foi
> reajustada** — é o único valor da operação que atravessa o corte
> inalterado.

Destinado a clientes que vão apenas deixar ou retirar mercadoria — **não
estacionam o carro**, giro rápido.

- **Tarifa fixa:** R$ 5,00 para até 15 minutos (valor corrigido por
  Fabio — vale tanto para a tabela antiga quanto para a atual).
- **Não é aplicada automaticamente** — o operador de caixa precisa
  **selecionar manualmente** essa tabela no sistema.
- **Se o operador esquecer de selecionar:** o sistema cobra
  automaticamente o valor de **30 minutos da tabela normal** (R$10 carro
  / R$8 moto na tabela atual) em vez do fixo de R$5 — nesse caso, o
  cliente acaba pagando **mais caro** do que deveria por um giro rápido.
- **Confirmado (seção 17):** clientes de Carga e Descarga entram e saem
  sempre pelo subsolo (cancelas 1 e 2), nunca pelo térreo.

**Conexão com achado anterior:** este é o segmento por trás das tabelas
`C E D MOTO` e `C E D CARRO` identificadas no relatório nativo do sistema
(seção 7) — mistério resolvido.

→ Implicações para análise:
- **Existe em toda a série**, sem data de corte. A métrica de aderência do
  operador tem base para o período inteiro.
- **O sistema não rotula o segmento.** Não há campo que marque C&D — na
  prática ele fica escondido dentro de `Avulso Regular`. A identificação
  precisa ser derivada: **permanência ≤ 15 min E saída pelo subsolo**.
  (Para carro existe ainda o marcador de elevador não utilizado; **para
  moto não existe**, então a regra de permanência + cancela é a única que
  serve para os dois.) Criar a categoria própria é item de prioridade alta
  para a próxima versão do dataset.
- **Taxa de aderência do operador medida no v12: ~70%**, estável antes e
  depois do corte de tabela (70,0% e 69,7%). Dos casos em que o operador
  esquece, o cliente paga entre R$ 1 e R$ 5 a mais — sempre contra ele.
- ⚠️ **O reajuste dobrou o custo do esquecimento.** Na tabela antiga o erro
  levava o carro a R$ 8 ou R$ 10 conforme o dia (prejuízo de R$ 3 a R$ 5);
  na tabela unificada, sempre a R$ 10 (prejuízo de R$ 5 fixos). A taxa de
  erro não mudou, mas o impacto por erro sim. **É a recomendação de
  treinamento mais fácil de justificar com número.**
- Permanência extremamente curta (minutos, não horas) — não confundir
  com erro de dado tipo "permanência quase zero" (seção 4); aqui é um
  padrão esperado do segmento, não problema de qualidade.

---

## 32. Contexto histórico do estabelecimento

Informação de contexto (não é regra de negócio operacional, mas é valiosa
para storytelling e para interpretar tendências de longo prazo, se dados
históricos amplos estiverem disponíveis):

- O estacionamento tem **cerca de 60 anos** de existência — uma das
  **primeiras garagens automáticas de São Paulo**, e ainda hoje uma das
  **mais altas** da cidade (reforça a estrutura de 21 andares/3 elevadores
  descrita na seção 23).
- **Há 20-30 anos**, o estacionamento operava **praticamente lotado**: de
  quase 400 vagas, cerca de **300 eram ocupadas por mensalistas**.
  Ocasionalmente havia **fila de carros na rua** esperando para
  estacionar.
- O motivo: o **prédio em frente era a sede da Justiça do Trabalho de São
  Paulo**. Os funcionários do prédio eram mensalistas do estacionamento, e
  o público que frequentava o prédio (partes de processos, advogados,
  testemunhas, etc.) alimentava o fluxo de Avulso.
- A mudança de uso do prédio em frente (a Justiça do Trabalho não está
  mais lá) provavelmente explica boa parte da diferença entre o cenário
  de altíssima ocupação de décadas atrás e a operação atual.

**Uso sugerido no projeto:** ótimo gancho narrativo para abrir o
relatório ou uma seção de contexto — contrasta a "época de ouro" (ligada
a uma âncora institucional específica) com o cenário atual, ancorado
principalmente no comércio da Rua Santa Efigênia (seção 13). Reforça a
tese de que o fluxo do estacionamento sempre foi **fortemente dependente
de quem/o que está no entorno**, não de uma demanda "genérica" de
mobilidade — primeiro a Justiça do Trabalho, hoje o comércio popular da
região. Não há necessidade de dado quantitativo desse período histórico
para usar essa narrativa — funciona bem como contexto qualitativo mesmo
sem números de décadas atrás.

**Linha do tempo completa do prédio da frente (contexto adicional):**
1. **Projeto original:** o prédio da frente seria **residencial**, com a
   garagem automática servindo como estacionamento dos moradores — os
   dois prédios são **estruturalmente interligados** até hoje por causa
   desse projeto original.
2. **Mudança de plano:** a ideia residencial foi descontinuada após as
   obras prontas; o prédio da frente foi vendido para a **União**, e o
   dono original ficou apenas com a garagem.
3. **Era Justiça do Trabalho:** o governo instalou a Justiça do Trabalho
   de SP no prédio, aproveitando a interligação física já existente com a
   garagem para circulação de clientes/funcionários (explica a "época de
   ouro" descrita acima).
4. **Início dos anos 2000:** a Justiça do Trabalho mudou de endereço; o
   prédio ficou **vazio por vários anos**.
5. **Presente:** o prédio foi reformado recentemente e hoje é **moradia
   social do programa Minha Casa Minha Vida (MCMV)**.

**Implicação direta para a segmentação de Mensalistas (seção 11):** boa
parte dos mensalistas classificados como perfil **"Morador"** vêm
justamente **desse prédio MCMV interligado** — o que explica
estruturalmente (literalmente, pela arquitetura interligada dos prédios)
por que esse subsegmento existe e tem o padrão de uso residencial
descrito (múltiplas entradas/saídas por dia, todos os dias da semana).
Esse é um detalhe forte para a narrativa do relatório: a garagem "voltou"
de certa forma à sua vocação original (moradia), só que décadas depois e
por um caminho histórico não planejado.

**Capítulo seguinte da história — leilão e retomada recente (contexto,
detalhes não 100% confirmados por Fabio):**
1. Após a saída da Justiça do Trabalho, o dono à época teria tomado um
   empréstimo bancário usando a garagem como garantia.
2. Por um conflito não detalhado, o empréstimo não foi quitado, e o
   estabelecimento acabou **penhorado e levado a leilão**.
3. Um advogado (coreano) arrematou o leilão e **operou o estacionamento
   por 17 anos**.
4. Segundo Fabio, nesse período o estabelecimento foi **degradado**, o
   que gerou **má fama do estacionamento na região**.
5. **Há 5 anos**, o dono original conseguiu **reverter a situação na
   Justiça** e retomou a posse do estacionamento.
6. Fabio foi **o primeiro contratado** dessa nova gestão, e os últimos 5
   anos têm sido de **tentativa de reerguer o estacionamento** de volta
   ao patamar de ocupação do "auge" histórico.

**Uso sugerido no projeto:** este é mais um capítulo da narrativa
histórica e ajuda a explicar o cenário atual de ocupação bem abaixo do
"auge" — não é só sobre a mudança do prédio da frente (Justiça do
Trabalho → MCMV), mas também sobre um período de 17 anos de degradação
da própria operação/reputação do estacionamento, seguido de uma fase de
reconstrução ainda em andamento. Isso é relevante para calibrar
expectativas: parte da baixa ocupação atual comparada ao "auge" histórico
provavelmente reflete tanto a mudança de uso do prédio da frente quanto
essa fase de recuperação de reputação — os dados do projeto (mesmo
cobrindo só os últimos meses) podem ser enquadrados como um retrato de
**um momento específico dessa recuperação**, não como o patamar "normal"
ou definitivo do negócio.

**Nota de cautela:** os detalhes desse período (motivo do conflito do
empréstimo, especificidades jurídicas) não são 100% confirmados por
Fabio — tratar como contexto qualitativo/narrativo no relatório, não como
fato jurídico verificado, e evitar reproduzir versões não confirmadas
como se fossem certezas.

---

## 34. Cartão Mestre — correção com base em dado real

**CORREÇÃO** (identificado ao analisar o log real de eventos de cancela,
30 dias): a explicação anterior desta seção (cortesia para familiares do
dono ou prestadores de serviço) estava **incompleta/incorreta**. O nome de
cortesia que aparece nos registros corresponde ao uso do
**cartão mestre** do estacionamento — um cartão com poder de liberar
entrada/saída de **qualquer veículo a qualquer momento**, contornando a
cobrança normal.

**Usos reais confirmados do cartão mestre:**
1. **Passagem de pedestre com carrinho/malas** — o acesso normal de
   pedestre é por escada; ocasionalmente é necessário abrir a cancela
   (destinada a veículos) para permitir a passagem de alguém com
   carrinho ou malas volumosas.
   ⚠️ **O mecanismo oficial não dava conta do volume.** Os motoboys da
   empresa de logística (seção 38) faziam a mesma coisa usando **o cartão
   de acesso da própria moto** — e esses eventos são **indistinguíveis de
   um movimento real de veículo**, ao contrário do cartão mestre, que fica
   marcado como cortesia. Ver 38.2 e 38.6.
2. **Veículos de funcionários** — tanto carro quanto moto, quando usados
   pelos próprios funcionários do estacionamento.

**Sobre o valor de R$272,00 recorrente observado no log:** **confirmado
por Fabio como não relevante para o projeto — pode ser ignorado.** Não
requer investigação adicional.

→ Implicações para o projeto (mantidas):
- Registros associados ao cartão mestre devem ser **excluídos de
  qualquer análise de receita** (não representam demanda paga real).
- Podem ser interessantes para análise de **volume/uso operacional**
  (ex: quantas vezes por dia a cancela é aberta para passagem de
  pedestre vs. para veículo de funcionário), mas não para métricas
  financeiras.
- Tratar como categoria técnica separada (`tipo_cliente = Cortesia` ou
  `Cartao Mestre`) dos segmentos de negócio pagantes.
- Vale, quando possível, diferenciar os dois usos (passagem de pedestre
  vs. veículo de funcionário) — podem ter padrões de horário e volume
  bem diferentes entre si.

---

## 35. Notas para o relatório final

- Ao reportar métricas relacionadas a moto, sempre comunicar como
  **estimativa aproximada**, nunca como número exato (por causa da
  ambiguidade com placa danificada).
- A taxa de aderência ao Totem e o indício de cobrança incorreta em moto
  são bons candidatos a **recomendações acionáveis** no relatório (ex:
  reforçar orientação ao atendente, priorizar instalação do sensor de
  classificação de veículo, avaliar habilitar Pix no Totem).
- Esse documento deve ser atualizado sempre que uma nova regra de negócio
  for identificada, antes de iniciar ou retomar qualquer fase técnica do
  projeto.

## 36. Ciclo de inadimplência do mensalista

> **Seção nova em 28/08/2026.** Esta regra operava desde sempre e **não
> estava documentada em lugar nenhum** — vivia só no código do gerador,
> com parâmetros que ninguém tinha validado. Confirmada com Fabio.

### 36.1 O ciclo, passo a passo

| # | Quando | O que acontece |
|---|---|---|
| 1 | Dia 10 | Vencimento do boleto |
| 2 | Dia 10 | **O escritório envia à operação a lista de inadimplentes** |
| 3 | A partir daí | Quando o cliente chega com o carro, **a equipe avisa** que o boleto está em aberto. Alternativamente, **alguém manda o recado por WhatsApp** |
| 4 | 3º dia útil após o vencimento | **Bloqueio no sistema** (só a partir de junho/2026 — ver 36.2) |
| 5 | Após o bloqueio | O cliente **não é impedido de entrar**: abre-se um ticket temporário e ele passa a pagar como avulso até regularizar |

**O objetivo declarado do passo 3 é evitar o desconforto de o cliente ser
bloqueado.** A equipe trabalha ativamente para que o passo 4 não aconteça
— o bloqueio é a falha do processo, não o processo.

**Volume real (confirmado por Fabio):** **2 a 3 clientes atrasam por mês**,
e **geralmente são os mesmos** — a inadimplência tem forte reincidência,
não é uma amostra nova de clientes a cada mês.

### 36.2 ⚠️ Marco: o bloqueio automático só existe a partir de junho/2026

**Este é o ponto mais importante da seção.**

| Período | Como o atraso era tratado |
|---|---|
| Até maio/2026 | **Sem bloqueio.** Mesmo com a cancela instalada, o estacionamento **não barrava a entrada** do inadimplente. Mantinha os avisos e deixava o boleto correr com **juros (percentual baixo, não quantificado)** |
| A partir de junho/2026 | O **ERP identifica a falta de pagamento e executa o bloqueio** no sistema. É um dos três efeitos do marco de 01/06 — ver seção 9 |

→ **Implicação para qualquer análise histórica:** registros de bloqueio
anteriores a junho/2026 **não podem existir**. E, mais importante, a série
de bloqueios saindo de zero em junho é um **artefato de início de coleta**,
não uma mudança de comportamento dos clientes. Declarar isso na metodologia
com a mesma força que o corte da tabela de preços.

### 36.6 ⚠️ Como o inadimplente entra e paga — corrigido em 13/09/2026

> A versão anterior desta seção tratava o inadimplente como **fluxo de exceção**
> e o excluía do denominador da aderência ao totem. **Estava errado.**

**O fluxo real, passo a passo:**

1. Com a mensalidade vencida, a **cancela não abre automaticamente** e o sistema
   exibe aviso de vencimento.
2. Se o cliente quiser entrar assim mesmo, ele **aperta o botão e retira ticket**,
   como qualquer avulso.
3. O registro fica como **`mensalista (nome) — entrada como avulso`**.
4. Na saída, ele **pode pagar no totem normalmente**, e o sistema cobra a estadia
   pela tabela de avulso.

→ **Consequência para a seção 3.1:** o inadimplente **é elegível ao totem** e
pertence ao denominador da aderência. Não é exceção — é um avulso com nome.

→ **O gerador já estava certo.** Ele sempre sorteou o canal de pagamento do
inadimplente entre totem e caixa (exceto moto, por causa da regra 4). O erro
estava só na **regra escrita** — mesma classe do achado "documentei errado" da
recarga elétrica: o código refletia a operação e o documento não.

→ **Impacto numérico:** a aderência sai de 89,3% para **89,2%**. Praticamente
nada — e é justamente por isso que o erro sobreviveu tanto tempo.

### 36.3 O que o sistema não registra

**O aviso não deixa rastro.** É verbal na chegada ou por WhatsApp — nada
disso entra no Softcase. O sistema guarda o **bloqueio** (a exceção) e
perde o **aviso** (a rotina que funciona).

→ Não é possível medir: tempo entre aviso e pagamento · quantos avisos
evitaram um bloqueio · se o WhatsApp funciona melhor que o aviso presencial.

→ **Recomendação:** registrar o aviso no cadastro do cliente, com data e
canal, transformaria uma rotina invisível num indicador de recuperação.

> **Padrão que se repete no projeto.** Este é o terceiro processo manual
> que funciona bem e não deixa rastro, ao lado da **venda de cartelas de
> selo** (seção 25) e do **login de operador** (seção 17). Os três maiores
> buracos analíticos do projeto têm a mesma causa, e a mesma recomendação:
> o sistema registra a falha e perde o processo.

### 36.4 Como isso aparece na receita — e por que engana

A inadimplência do mensalista **nunca aparece como perda de receita**:

- **Até maio:** virava **juros** somados ao boleto.
- **De junho em diante:** vira **ticket de avulso** pago na saída.

Nos dois regimes, o cliente que não pagou gera uma linha **positiva** no
caixa. Um painel que olhe só o faturamento diário não enxerga o problema —
é preciso cruzar com o ERP. É um bom exemplo, para o relatório, de métrica
que engana pelo sinal.

### 36.5 Parâmetros para a simulação

| Parâmetro | Valor |
|---|---|
| Vencimento | Dia 10 de cada mês |
| Bloqueio | 3º dia útil após o vencimento, **apenas de junho/2026 em diante** |
| Clientes em atraso por mês | 2 a 3 (sobre base de ~80) |
| Reincidência | **Alta** — modelar com memória, não com sorteio independente mês a mês |
| Dias até regularizar após o bloqueio | 1 a 3 (o cliente já foi avisado duas vezes antes) |
| Juros no regime antigo | Existe, percentual baixo — **não modelar** |

**Erro conhecido a evitar:** sortear o atraso de forma independente a cada
mês produz a taxa mensal certa e um acumulado absurdo — no v12, 25% da base
passou por bloqueio no semestre, **com zero reincidentes**, exatamente o
oposto do comportamento real. Uma cadeia de dois estados
(`P(atrasa | em dia) ≈ 0,015`, `P(atrasa | atrasou) ≈ 0,70`) reproduz os
2–3 por mês com maioria reincidente e ~9% da base afetada no semestre.

---

## 37. O boleto antes e depois do ERP — o que mudou foi a entrega

> **RESOLVIDO em 28/08/2026.** Esta seção registrava uma limitação
> ("não sabemos como o boleto era registrado antes do ERP"). Fabio
> esclareceu, e **não há limitação**: o boleto nunca mudou.

**O boleto sempre foi gerado diretamente com o banco**, e sempre foi
exatamente igual. O ERP **não mudou a geração — mudou a distribuição**:

| | Antes de 06/2026 | A partir de 06/2026 |
|---|---|---|
| Geração | Direto com o banco | Direto com o banco (igual) |
| Valor e periodicidade | Iguais | Iguais |
| **Entrega** | O financeiro **imprimia cada boleto** e enviava ao estacionamento, que entregava ao cliente em mãos. Clientes que já tinham fornecido e-mail recebiam por e-mail | **Cadastro de todos os clientes atualizado com e-mail.** Entrega 100% digital, sem impressão |

→ **Implicação para o dado:** os registros de mensalidade anteriores a
junho são **legítimos e comparáveis** aos posteriores. Não há quebra de
série na receita de mensalidade — o que muda em 01/06 é só a tabela de
avulso (seção 9) e o bloqueio automático (seção 36).

→ **Implicação para o relatório:** é uma melhoria operacional concreta e
citável do marco de modernização, ao lado das outras três. Eliminou
impressão de boleto, transporte físico até o estacionamento e entrega em
mãos pela equipe — trabalho recorrente todo mês que simplesmente deixou de
existir. **É o único dos quatro efeitos do marco que não tem contrapartida
negativa nenhuma.**

---

## 38. O cliente de locação de espaço — empresa de logística (até 31/05/2026)

> **Seção nova em 28/08/2026.** Este cliente **não estava documentado em
> lugar nenhum** e é o item que mais contradiz regras já escritas neste
> documento. Esteve presente durante **108 dos 180 dias** da janela de
> análise e saiu no marco de 01/06. Ler antes de qualquer análise que
> atravesse essa data.

### 38.1 O que era

Uma empresa de logística de entregas, mensalista da garagem desde antes da
gestão atual. Recolhia pacotes nas lojas da região (seção 13), separava no
subsolo e distribuía pela cidade de moto.

**Evolução do contrato:**

| Fase | Como era cobrado | Uso |
|---|---|---|
| Início | **3 vagas de carro** | ~10 motos + o espaço restante para separar mercadoria |
| Depois do crescimento | **Locação de espaço** — valor único, sem número fixo de vagas | ~1/3 do subsolo, ~30 motos |

A cobrança era por boleto, como qualquer mensalista. **Mas a unidade
contratada deixou de ser a vaga.**

**Frota e credenciais no fim do período:**

- **~30 motos**, com **~30 cartões de acesso fixos, um por motoboy**. A
  gerência optou por **não vincular cada cartão aos dados do motoboy** —
  todos foram cadastrados apenas com os dados da empresa.
- **1 Renault Kangoo**, para coletas de grande volume. Usava **vaga de
  carro normal, com elevador e manobrista**.
- **5 carrinhos de carga**, sem dono fixo — os motoboys se alternavam no
  uso durante a tarde.

**Operação:** segunda a sábado, com o núcleo entre **12h e 16h**; poucos
chegavam mais cedo. A Kangoo saía para coleta **1 a 2 vezes por dia**.

**Saída:** com o crescimento, o fluxo de pessoas e motos passou a atrapalhar
a operação do próprio estacionamento. Foi proposto um reajuste, **a empresa
recusou e saiu em 01/06/2026**, indo operar em outro estacionamento.

### 38.2 ⚠️ O ponto mais importante: movimento de veículo que não é veículo

**O acesso de pedestres da garagem é por escada; a rampa é só para
veículos.** Mas parte dos motoboys precisava passar com **carrinho de
carga**, e para conseguir abrir a cancela **usava o cartão de acesso da
própria moto**.

Resultado, e é aqui que o dado mente:

| Momento | O que o sistema registra | O que existe no subsolo |
|---|---|---|
| Motoboy chega com a moto | Entrada de moto | 1 moto ✓ |
| Sai a pé, com o carrinho | **Saída de moto** | **1 moto** ✗ |
| Volta com a mercadoria | **Entrada de moto** | 1 moto ✓ |
| Vai embora no fim do dia | Saída de moto | 0 ✓ |

**Para o sistema, quem circula é a moto. Na realidade é o motoboy, a pé.**

→ **Consequência direta sobre o método da seção 23.** A ocupação é
reconstruída por soma cumulativa de entradas e saídas — é o único caminho,
porque não existe snapshot. Mas **cada saída de pedestre subtrai uma moto
que continua estacionada.** A ocupação de moto do período fica
**subestimada por construção**, e o erro é máximo justamente **entre 12h e
16h**, que é quando mais motoboys estão fora a pé.

→ **A ocupação real de fevereiro a maio (~83% da área de moto, ver 38.3) é
inobservável no dado.** Ela existe na observação de Fabio e não existe no
sistema. Nenhuma reconstrução recupera esse número. **Declarar isso na
metodologia** — é uma limitação do sistema real, não do método de análise.

→ **Como os carrinhos eram alternados entre os motoboys**, os eventos
fantasma se espalham por todos os ~30 cartões em vez de se concentrarem em
alguns. Isso **piora a detectabilidade**: nenhum cartão isolado fica
anômalo o bastante para ser sinalizado. O padrão só é visível no agregado
do cliente.

### 38.3 O que isso reverte na capacidade de moto (seção 23)

Os números de moto informados por Fabio — **~20 simultâneas para ~60 vagas**
— são a **situação atual, posterior à saída da empresa**.

| Período | Motos simultâneas | % das ~60 vagas |
|---|---|---|
| **fev–mai/2026** (com a empresa) | ~20 + ~30 = **~50** | **~83%** |
| **jun–ago/2026** (após a saída) | ~20 | ~33% |

⚠️ **A conclusão da seção 23 de que "o espaço para crescimento no segmento
moto é proporcionalmente maior do que no carro" vale para hoje e era falsa
em maio.** A área de moto estava perto da lotação três meses atrás. A folga
atual **não é estrutural — é o buraco deixado por um cliente que saiu.**
Qualquer recomendação sobre expansão de moto precisa datar o número.

*(O total de ~50 também valida a capacidade de ~60 vagas por outro
caminho: os dois regimes somados cabem no espaço, com folga pequena.)*

### 38.4 A inversão do calendário semanal

A empresa funcionava **de segunda a sábado, com mais movimento nos dias
úteis e menos no sábado** — inclusive com **menos motoboys ativos** no
sábado.

**Isso é o oposto do resto da garagem.** A seção 13 estabelece que o sábado
é o dia de maior movimento, puxado pelo comércio da região. Havia, portanto,
**dois calendários semanais opostos convivendo no mesmo prédio**:

| Movimentos/dia | Sem a empresa | Com a empresa (fev–mai) |
|---|---|---|
| Dia útil | 319 | ~449 |
| Sábado | 368 | ~440 |
| **Razão sábado / dia útil** | **1,15×** | **~0,98×** |

→ **A sazonalidade semanal agregada da garagem mudou de forma estrutural em
junho** — não porque o comportamento dos clientes mudou, mas porque saiu um
inquilino com calendário invertido. Antes de junho o pico de sábado
praticamente desaparecia no total; depois ele aparece limpo.

→ **Implicação para a modelagem de ocupação (Etapa 4):** um modelo de
sazonalidade ajustado sobre a janela inteira está ajustando **uma mistura de
dois regimes**. A estrutura semanal (lag-7) não é a mesma antes e depois de
01/06. Ou segmentar por regime, ou declarar a limitação.

*(O sábado do **Avulso**, medido isoladamente, não é afetado — segue 1,96×
o dia útil. O que se contamina é o movimento total.)*

### 38.5 As regras que este cliente contradiz

Lista para conferência antes de qualquer análise:

| Seção | O que a regra diz | Por que não vale aqui |
|---|---|---|
| **1** | Seis segmentos de cliente | Nenhum cobre "locação de espaço operacional" — é um sétimo |
| **23** | Capacidade contratada se mede em vagas | O contrato não tinha número de vagas |
| **23** | ~20 motos simultâneas, muito abaixo do teto | Era ~50 (83%) até maio — ver 38.3 |
| **23** | Moto **não tem custo operacional** (não usa elevador nem manobrista) | Verdade para uma moto, falso para cinquenta: o fluxo atrapalhava a operação. O custo é de **congestionamento de acesso**, não de manobra |
| **23** | O cartão de acesso identifica o veículo do cliente | Aqui identifica **um motoboy**, cadastrado só com os dados da empresa. `Veiculo_ID` segue estável (cartão fixo por pessoa), mas **deixa de significar "veículo"** |
| **11** | Mensalista é Trabalhador ou Morador | Não é nenhum dos dois, nem dormente |
| **11.1** | entradas/dia por cliente separa perfis | Este cliente é outlier de uma ordem de grandeza: ~31 credenciais, dezenas de entradas/dia |
| **13** | Sábado é o dia de maior movimento | Invertido para eles — ver 38.4 |
| **30** | "Carga e descarga" é o avulso de giro rápido | Eles fazem carga e descarga como **mensalista**. Mesmo nome, coisas diferentes |
| **34** | O cartão mestre serve à passagem de pedestre com carrinho | Existe o mecanismo oficial; eles usavam o cartão da moto — ver 38.6 |
| — | O estacionamento guarda veículos | Guardava também **mercadoria**, que não é veículo e não está em nenhuma regra |

### 38.6 O elo com a seção 34 (cartão mestre)

A seção 34 já documenta a necessidade: *"o acesso normal de pedestre é por
escada; ocasionalmente é necessário abrir a cancela para permitir a
passagem de alguém com carrinho ou malas volumosas"* — e para isso existe o
**cartão mestre**.

O documento tinha metade da história. A outra metade é que **o mecanismo
oficial não dava conta do volume**, e a operação encontrou um atalho.

| Mecanismo | Como fica no dado |
|---|---|
| Cartão mestre (oficial) | Marcado como cortesia, **identificável**, e a seção 34 já manda excluir de análises de receita |
| Cartão da moto (atalho) | **Indistinguível de um movimento real de veículo.** Nenhum campo o revela |

→ Vale como recomendação operacional: **passagem de pedestre com carga
precisa de uma credencial própria.** Enquanto ela não existir, todo volume
de carrinho vira movimento fantasma de veículo no histórico.

### 38.7 Parâmetros para a simulação

| Parâmetro | Valor | Origem |
|---|---|---|
| Presença | 13/02 a 31/05/2026 (108 dias); ausente a partir de 01/06 | fabio |
| Dias de operação | Segunda a sábado; **domingo não opera** | fabio |
| Janela principal | 12h–16h (poucos mais cedo) | fabio |
| Motos / cartões | ~30, cartão fixo por motoboy | fabio |
| Carro | 1 Kangoo, vaga normal, 1–2 coletas/dia | fabio |
| Carrinhos de carga | 5, alternados entre os motoboys | fabio |
| Motos com voltas reais no dia | poucas, 2 a 3 voltas | fabio |
| Voltas por carrinho por dia | **4** | **arbitrado** — ordem de grandeza não confirmada |
| Atividade no sábado | ~55% do dia útil, com menos motoboys | arbitrado (Fabio: "menos movimento") |
| Valor do boleto | **~R$ 3.000/mês** | fabio (ordem de grandeza) |
| Reajuste proposto e recusado | **~R$ 5.000/mês** (+67%) | fabio |

**Volume estimado:** ~130 eventos/dia útil, dos quais **~31% são movimento
fantasma** (pedestre com carrinho). Sobre um dataset de ~309 eventos/dia,
isso é **+40% no período de fevereiro a maio**.

### 38.8 O peso financeiro, e a economia da decisão

**Este era, de longe, o maior cliente da garagem.**

| Indicador | Valor |
|---|---|
| Mensalidade | **~R$ 3.000/mês** |
| Múltiplo do mensalista médio (R$ 372) | **8,1×** |
| Fatia da receita mensal de mensalidade (~R$ 29,3 mil) | **~10%** |
| Perda anualizada com a saída | **~R$ 36.000** |

**A economia por unidade explica o reajuste.** Como o contrato era por área
e não por vaga, ninguém calculava o valor por veículo — mas ele é
calculável e é revelador:

| | R$/mês por moto | % da tarifa padrão (seção 29.1) |
|---|---|---|
| Empresa de logística (R$ 3.000 ÷ ~30 motos) | **R$ 100** | **50% a 56%** |
| Proposta recusada (R$ 5.000 ÷ ~30 motos) | R$ 167 | **83% a 93%** |
| Mensalista de moto comum | R$ 180 (legado) ou R$ 200 (atual) | 100% |

**A empresa pagava cerca de metade da tarifa por moto praticada com os
demais clientes.** E o reajuste proposto **não era um aumento — era a
remoção do desconto**: a R$ 5.000 ela chegaria a 83–93% do valor padrão,
ainda ligeiramente abaixo.

Esse é o mesmo formato de outros dois achados do projeto: a tabela
unificada de 01/06 não reajustou o fim de semana, fez o dia útil alcançá-lo
(seção 9); e o selo passou de R$ 8 para R$ 9 aproximando-se do que
desconta (seção 25.1). **Três "aumentos" que eram, na verdade, correções de
descontos herdados.**

**Mas o resultado foi ruim, e o dado mostra por quê.** A área liberada não
foi recolocada: a ocupação de moto caiu de ~83% para ~33% e permanece lá.
Para repor os R$ 3.000/mês com mensalistas de moto na tarifa padrão seriam
necessários **~11 novos clientes** — contra uma base atual de **14 veículos
de moto mensalista no total**. Repor esse contrato exige praticamente
dobrar o segmento de moto da casa.

### 38.9 O custo de servir — por que o reajuste não era sobre vagas

> **Informação de Fabio, 28/08/2026.** O reajuste não foi calculado sobre
> espaço ocupado. Foi uma tentativa de precificar um custo que **nenhuma
> métrica do estacionamento captura**.

**A empresa não ocupava vagas — ela trazia gente.** Cerca de **30
motoboys**, mais funcionários que chegavam **a pé** para ajudar na
operação. Isso gerava consumo real e contínuo:

| Item | Natureza |
|---|---|
| Uso do banheiro, várias vezes ao dia por ~35 pessoas | Consumo de água, limpeza, manutenção |
| **Iluminação adicional instalada** na área que ocupavam | Investimento + energia recorrente |
| **Micro-ondas** no espaço deles | Energia |
| **Wi-Fi instalado** | Serviço recorrente |
| Motos, carrinhos e pessoas circulando pelo pátio | **Conflito operacional com os manobristas** |

⚠️ **O modelo de custo do estacionamento é por veículo; o custo deste
cliente era por pessoa.** Toda a estrutura de custo descrita nas seções 15
e 23 é manobra e elevador — e a seção 23 chega a afirmar que **moto não
tem custo operacional**. Nada nesse modelo tem lugar para "gente".

E há uma razão estrutural para essa cegueira: **pedestres não passam pela
cancela** — o acesso é por escada (seção 34). O sistema **não registra
presença humana**, só passagem de veículo. Um cliente cujo principal
insumo é presença de pessoas é, por construção, invisível para todas as
métricas da casa.

*(É também o que explica 38.2: quando essas pessoas precisavam passar com
carrinho, o único jeito de abrir a cancela era usar o cartão da moto. A
cegueira do sistema a pedestres é a causa do movimento fantasma.)*

**O conflito de horário agrava.** A operação deles era das 12h às 16h.
Nessa janela o estacionamento faz cerca de **81 manobras de carro**, 29%
das ~276 do dia útil — e é a rampa de subida para o pico da tarde. Motos,
carrinhos e pedestres circulando pelo pátio nesse intervalo competem
diretamente com o trabalho dos manobristas.

### 38.10 O resultado da decisão

**Pelo financeiro isolado, foi uma perda grande:** −R$ 3.000/mês, ~R$ 36
mil/ano, ~10% da receita de mensalidade, com a área liberada sem
recolocação até agora (ocupação de moto caiu de ~83% para ~33%).

**Pela operação, a avaliação de Fabio é clara: o estacionamento ficou
muito mais fluido depois da saída.**

⚠️ **Este é o ponto a levar para o relatório final, e vale mais que o
número.** Todos os indicadores disponíveis apontam para "perdemos R$ 36
mil por ano". O benefício — fluidez de pátio, custo de servir, ausência de
conflito no horário de pico — **não aparece em nenhuma métrica, porque
nenhuma métrica existe para ele.**

> A decisão mais importante do período foi correta, e **os dados jamais
> diriam isso**. Não por falta de análise: por falta de instrumentação.

→ **Recomendação, e ela não é sobre esse cliente — é sobre o próximo.**
Contratos de locação de espaço precisam de três números que hoje não
existem:
> 1. **valor por unidade ocupada**, comparável à tarifa padrão de vaga
>    (seção 29.1);
> 2. **estimativa de pessoas** que o contrato traz para dentro do prédio,
>    já que é esse o verdadeiro gerador de custo;
> 3. **sobreposição com os horários de pico** da operação de manobra.
>
> Sem os três, a decisão de reajustar ou liberar é tomada no escuro — como
> foi aqui, ainda que o instinto tenha acertado.

---



## 39. Energia — elevadores, placas solares e recarga elétrica

> **Seção nova em 28/08/2026.** A geração solar não estava documentada em
> lugar nenhum, e muda a leitura do custo de operação e da margem da
> recarga elétrica.

### 39.1 O investimento

O estacionamento é uma **garagem automática movida a elevadores** (seção
23): todo carro que entra ou sai consome energia de elevador. Isso torna o
**custo energético da operação alto** e estruturalmente ligado ao volume de
movimento — diferente de um estacionamento de rampa.

Diante disso, o dono investiu em um **grande número de placas solares**.

**O que se sabe (Fabio, 28/08/2026):**
- A instalação é grande.
- **Não zera o gasto de energia** — reduz significativamente.

**O que não se sabe:** potência instalada, geração mensal, fração da conta
coberta, existência de baterias, modalidade de compensação. **Nada disso
está disponível para o projeto**, nem a conta de energia.

### 39.2 Geração e consumo coincidem — e a geração nunca cobre

> ⚠️ **CORREÇÃO de 28/08/2026.** A primeira versão desta seção afirmava que
> as curvas de geração solar e consumo de elevador eram **descasadas**, com
> o elevador tendo dois picos (manhã e fim de tarde) e o sol um só, ao
> meio-dia. **Estava errado.** Aquela curva horária foi extraída do dataset
> **sintético**, cujas janelas de chegada e saída do mensalista trabalhador
> são constantes fixas no gerador — `(7.0, 9.5)` e `(17.0, 19.5)`. Era o
> gerador sendo citado como se fosse observação do mundo real.

**O que Fabio observa (28/08/2026):**

> O momento de maior número de recargas é também o momento em que **o
> elevador mais é utilizado**. E o elevador consome **muita** energia.

E o propósito declarado do investimento em placas era **reduzir custo, não
zerar**: a geração **nunca cobre o consumo**.

**A consequência econômica é a que importa, e ela simplifica tudo:**

> **A geração solar reduz o custo MÉDIO da energia do prédio. Ela não
> reduz o custo MARGINAL do próximo kWh consumido**, porque o
> estacionamento é importador líquido em todos os momentos — inclusive no
> pico solar, quando o elevador está no auge.

→ Toda recarga elétrica, **em qualquer horário**, é consumo adicional que
vem da rede. O custo marginal é a tarifa cheia (~R$ 1,00/kWh, seção 6.4c),
e não há um cenário de "energia própria a custo zero".

→ **Não existe descasamento de curvas a reportar.** Aquilo era artefato do
dado sintético.

### 39.3 A recarga não muda de margem conforme o horário

Como a geração nunca cobre o consumo (39.2), a distinção entre carregar de
dia e de noite **não gera diferença de custo marginal**. A margem da
recarga é aproximadamente **constante ao longo do dia**, em torno de 60%
(seção 6.4c).

**Isso invalida três coisas que chegaram a ser escritas neste documento** e
que ficam registradas para não voltarem:

| Afirmação retirada | Por quê |
|---|---|
| "A recarga no pico solar tem margem próxima de 100%" | Não há excedente solar; o consumo base já absorve tudo |
| "Orientar o manobrista a priorizar recarga entre 10h e 15h" | Não muda o custo marginal. **Não recomendar** |
| "O crescimento da recarga noturna erode a margem" | O mix diurno/noturno não afeta o custo por kWh |

**A observação de Fabio de que a maioria das recargas já ocorre no horário
de maior movimento continua válida e é útil por outro motivo** — ela diz
que a demanda de recarga se soma ao pico operacional, não que ela é mais
barata. Isso é uma questão de **capacidade e de manobra** (seção 6.4), não
de energia.

⚠️ **Uma ressalva que permanece aberta.** Se o estacionamento estiver em
modalidade tarifária **horo-sazonal** (comum no Grupo A), existe um período
de *ponta* — tipicamente 17h–20h em dias úteis — com tarifa
significativamente mais cara. Nesse caso a recarga do morador que chega no
fim da tarde **seria** mais cara que a do meio-dia, por um motivo diferente
do solar. **Isso não é sabido** e depende da conta de energia (39.4). Não
afirmar em nenhuma direção.

### 39.3.1 O crescimento vem dos mensalistas — e o efeito é de capacidade, não de margem

A seção 6.3 estabelece que os três saltos de volume da recarga têm a mesma
causa: **entrada de veículo elétrico novo na base de mensalistas**. O peso
do segmento Morador na recarga saltou de **~15% para ~45% das sessões**
entre maio e junho de 2026, com a entrada dos dois moradores EV-dependentes.

⚠️ **Isso NÃO tem efeito sobre a margem** — ver 39.3. Uma versão anterior
desta seção calculava uma erosão de margem pela mudança de mix
diurno/noturno; a conta partia da premissa errada de excedente solar e foi
retirada.

**O efeito real é de capacidade e de operação:**

- A demanda cresce ~8× ao ano (seção 6.3) e **se concentra no horário de
  maior movimento** do estacionamento (39.2). São duas tomadas, três em
  breve, e o dimensionamento por Erlang B da seção 6.4 já mostra saturação
  em ~5,4 recargas/dia com três tomadas.
- Cada recarga gera **uma manobra a mais** (seção 6.4), e ela cai
  justamente quando o manobrista está mais ocupado.
- O mensalista morador tem **expectativa de disponibilidade** diferente de
  um avulso: paga vaga fixa e conta com a tomada.

→ **A pergunta certa para o roadmap das tomadas não é de margem, é de
serviço:** quando o crescimento da base de elétricos vai começar a produzir
motorista que chega e não encontra tomada livre no horário em que mais
precisa. A seção 6.4 já tem os números de bloqueio; o que esta subseção
acrescenta é que a demanda **não está distribuída ao longo do dia — está
empilhada no pico**, o que torna os números da 6.4 otimistas.

### 39.4 Nota sobre o custo do kWh

O custo de aquisição do kWh **permanece desconhecido** — Fabio não tem
acesso à conta de energia. A estimativa de ~R$ 0,80/kWh mencionada na seção
6.4b é referência de mercado, **não um dado da operação**, e com a geração
solar no meio o custo efetivo é provavelmente **menor e variável ao longo
do dia**.

→ Ao reportar a recarga elétrica, tratar como **receita conhecida e margem
desconhecida**. É honesto e não compromete o resto da análise.

### 39.5 Efeito colateral sobre o modelo de custo por veículo

A seção 23 afirma que **moto não tem custo operacional** por não usar
elevador nem manobrista. Com o peso energético do elevador confirmado como
motivo de um investimento em geração própria, essa afirmação fica **mais
forte, não mais fraca**: a moto evita justamente o insumo mais caro da
operação.

Isso muda a leitura econômica do segmento moto — ele é de **margem
estruturalmente superior** por vaga ocupada, ainda que a tarifa seja menor
(R$ 180–200 contra R$ 250–310, seção 29.1). Vale considerar na avaliação de
expandir a área de moto, especialmente com ~30 vagas ociosas desde a saída
da empresa de logística (seção 38.3).

*(A ressalva de 38.9 continua valendo: moto em **volume** tem custo de
congestionamento de acesso, que é outro eixo e também não é medido.)*

---

---

**Histórico de revisões**

| Data | O que mudou |
|---|---|
| 26/08/2026 | Seção 6 reescrita com a série real de 12 meses do Clamper Mobi Manager. A estimativa de "~60 recargas/mês" foi corrigida: o volume é uma curva de adoção crescente, não um patamar. Acrescentadas as médias de referência (10,71 kWh e 1,82h por sessão, 5,90 kW) e o alerta de que fev/2026 é outlier. |
| 26/08/2026 | Seção 6.4 nova: dimensionamento das tomadas por Erlang B com a duração real. Registrado que a 3ª tomada já está em obra e satura em ~5,4 recargas/dia. Confirmado que a vaga é rotativa (o manobrista retira o carro ao fim da carga), o que valida o modelo. Acrescentada a análise do tempo de retirada como gargalo do carregamento rápido, e a comparação potência vs. número de vagas. |
| 26/08/2026 | Seção 6: causa dos três saltos da série confirmada (entrada de elétricos na base de mensalistas — eletrificação da frota em SP, não eventos pontuais). Registrada a leitura de 25/08 (~120 recargas em agosto) e o alerta de que a foto de agosto é do início do mês. Acrescentada a recomendação de avaliar uma 3ª tomada. |
| **28/08/2026** | **Revisão a partir da EDA do v12 (`eda_v12_achados.md`) e de três rodadas de confirmação com Fabio.** Nove alterações, listadas abaixo. |
| 28/08/2026 | **Seção 3** — nova subseção 3.1 com o **denominador canônico** da aderência ao Totem (Avulso Regular, carro, sem selo, sem recarga EV, cartão). A EDA mostrou que a métrica varia 29 pontos conforme a definição, e que a maior parte da variação são pagamentos que a seção 2 obriga a ir ao Caixa. Acrescentados o limite de atribuição por turno (3.2) e o teto estrutural do Totem (3.3). |
| 28/08/2026 | **Seção 5** — a fórmula de `seguiu_orientacao_totem` **contradizia a seção 2** e foi corrigida; criado o campo `elegivel_totem`. Novo campo derivado `entrada_efetiva` (exclui tentativas bloqueadas, que são logadas como Entrada sem que o veículo entre). |
| 28/08/2026 | **Seção 9** — reescrita como **marco único de modernização**: 01/06/2026 traz três mudanças simultâneas (tabela unificada, faturamento no ERP, bloqueio automático de inadimplente), e não apenas o reajuste. Confirmado por Fabio que tabela e ERP foram idealizados para sair juntos. Acrescentado o alerta de artefato de início de coleta. |
| 28/08/2026 | **Seção 11** — a feature recomendada estava errada. "Entradas/dia por **cliente**" tem correlação **0,81 com o número de vagas contratadas**: mede o contrato, não o comportamento. Substituída por entradas/dia **por veículo**, com a ordem de utilidade das features medida no v12 e a ressalva para a etapa de clustering. Registrado que **90% dos trabalhadores abrem no sábado** (antes: "parcela"). |
| 28/08/2026 | **Seção 23** — precisão sobre o "é raro moto ficar >12h": vale para quem paga por permanência, **não para moto de mensalista**, que fica na vaga 24/7 por contrato. |
| 28/08/2026 | **Seção 25** — duas subseções novas. **25.1**: distribuição real de diárias do hotel (boa parte fica 1 diária, maioria entre 1 e 4, cauda rara) — parâmetro com maior efeito isolado sobre a receita simulada. **Preço de venda do selo**: R$ 8,00 até 31/05 (R$ 400 a cartela) e R$ 9,00 depois (R$ 450). Com o abono de R$ 15, o selo é vendido abaixo do que desconta; incluída a tabela de margem, que **inverte de sinal conforme a quantidade apresentada**, e a recomendação de alinhar o preço. |
| 28/08/2026 | **Seção 30** — **corrigida.** O segmento Carga e Descarga **existe durante todo o período e sempre custou R$ 5,00** (confirmado por Fabio); as afirmações de que foi "criado junto com a tabela atual" e de que "não retroage" estavam erradas e se contradiziam com o parágrafo seguinte. Acrescentado que o sistema **não rotula o segmento** (identificação por permanência ≤ 15 min + saída pelo subsolo), a aderência medida do operador (~70%) e o fato de que **o reajuste dobrou o custo do esquecimento** para o cliente. |
| 28/08/2026 | **Seção 36 nova** — ciclo de inadimplência do mensalista, que não estava documentado em lugar nenhum. Vencimento no dia 10, lista enviada pelo escritório, aviso presencial ou por WhatsApp para evitar o bloqueio, 2 a 3 clientes por mês com **alta reincidência**. **Marco: o bloqueio automático só existe a partir de junho/2026** — antes o boleto corria com juros baixos e o cliente entrava normalmente. Registrado que o aviso não deixa rastro no sistema, e os parâmetros para simulação. |
| 28/08/2026 | **Seção 11.2 nova** — os perfis não são estanques. Dois ou três **lojistas com mais de um carro** deixam um veículo parado permanentemente, como garagem, e circulam com o outro; dois ou três **moradores viajam**, uns levando o carro (vaga vazia) e outros deixando-o guardado (vaga ocupada) — assinaturas opostas na ocupação, idênticas na contagem de eventos. Registrado o alerta de que "permanência longa de lojista" deixa de ser sinal automático de erro de pareamento. |
| 28/08/2026 | **Seções 11.3, 11.4 e 11.5 novas** — o **mensalista dormente**: 3 clientes (2 carros com defeito sem verba para conserto, 1 moto abandonada) que **pagam o boleto e não movimentam o veículo**. Não têm nenhum evento de cancela, só a Renovação Mensal: existem na receita e não no log de movimento, o que faz a base contratada divergir da base observada. **11.4 — ponto cego crítico:** um deles atrasa sempre, mas como o veículo nunca passa pela cancela **o bloqueio nunca é acionado** — a inadimplência medida por `Status=Bloqueado` subestima sistematicamente o caso crônico. **11.5** — leitura de negócio: melhor margem operacional da base e maior risco de churn ao mesmo tempo. |
| 28/08/2026 | **Seção 38 nova, e é a maior adição da revisão** — a **empresa de logística** mensalista até 31/05/2026, presente em 108 dos 180 dias e não documentada em lugar nenhum. Contrato por **locação de espaço** (~1/3 do subsolo), ~30 motos com cartão fixo por motoboy, 1 Kangoo, 5 carrinhos de carga, operação de segunda a sábado concentrada entre 12h e 16h. Saiu em 01/06 após recusar reajuste. **38.2 — achado central:** os motoboys usavam o cartão da moto para passar com carrinho a pé, então **o log registra movimento de veículos que não se moveram**, e a ocupação de moto do período fica subestimada por construção. **38.3:** os "~20 motos simultâneas" da seção 23 são a situação ATUAL — até maio eram ~50 (83% da área), o que **inverte a conclusão de que há folga no segmento moto**. **38.4:** calendário semanal oposto ao do resto da garagem, achatando o pico de sábado até junho. **38.5** lista as 11 regras que este cliente contradiz. |
| 28/08/2026 | **Seções 1, 9, 11.3b, 23 e 34 ajustadas** em função da seção 38: sétimo segmento ("locação de espaço"); quarto efeito do marco de 01/06, o único que muda volume; alerta de clustering; capacidade de moto separada por regime e a precisão de que "moto sem custo operacional" vale por moto e não em escala; e o elo entre o cartão mestre e o atalho do cartão de moto. |
| **06/09/2026** | **Seções 17.1 e 17.2 novas — quadro e escala.** Registrado o quadro (1 gerente, 2 caixas, 7 manobristas) e a **escala completa** de segunda a sexta, sábado e domingo. ⚠️ **Os papéis não são estanques:** as operações simples de caixa são feitas também pelos manobristas, e **todos sabem cobrar, aplicar selo e ativar Passe Livre**. O papel do caixa é **controle financeiro** — organização, fechamento diário e conferência de valores. Isso dá **causa estrutural** à correção retroativa de forma de pagamento da seção 21: cobrança distribuída entre 7 pessoas, conferência centralizada em 2. A escala é o primeiro dado operacional real do projeto e calibra o ritmo por manobrista, com dia útil e sábado convergindo no mesmo valor. Registrados também os **intervalos**: 30 min nos turnos de 6h30, 1 h nos de 9 h, e **nenhum no turno da noite** — as três configurações fecham nas jornadas de 36 h e 44 h declaradas. ⚠️ A **duração** do intervalo é conhecida, o **horário** não, e às 8h isso faz a equipe disponível variar entre 1,5 e 3 pessoas. |
| 28/08/2026 | **Seção 39 nova — energia.** Registrada a instalação de **placas solares**, motivada pelo alto custo energético dos elevadores; a geração é grande mas **não zera** a conta. **39.5:** o peso energético do elevador reforça que a moto tem margem estruturalmente superior por vaga. |
| 28/08/2026 | ⚠️ **Seções 39.2, 39.3, 39.3.1 e 6.4c CORRIGIDAS no mesmo dia.** A primeira versão afirmava que as curvas de geração solar e consumo de elevador eram descasadas, e daí derivava margem de ~100% para recarga diurna, recomendação de concentrar recarga entre 10h e 15h, e erosão de margem pelo crescimento da recarga noturna. **Tudo errado.** A curva horária usada como prova foi extraída do **dataset sintético**, cujas janelas do mensalista trabalhador são constantes fixas no gerador (`(7.0, 9.5)` e `(17.0, 19.5)`). Fabio observa o oposto: **o pico de recarga coincide com o pico de elevador**, e a geração **nunca cobre o consumo**. Consequência correta: a solar reduz o custo **médio** da energia, não o **marginal** — o estacionamento é importador líquido o tempo todo, então toda recarga custa a tarifa cheia e **a margem é ~60% em qualquer horário**. O crescimento da recarga é problema de **capacidade e manobra**, não de margem. |
| 28/08/2026 | **Seções 6.4b, 11.1b, 11.5b e 13 ajustadas — fechamento das pendências.** **6.4b:** tarifa de recarga documentada, com reajuste trimestral desde a instalação (1,99 → 2,20 → 2,40 → 2,50, +25,6% em 9 meses); custo do kWh segue desconhecido e a margem estimada de ~68% é hipótese, não fato. **11.1b:** no fim de semana a maioria dos moradores reduz as saídas, mas os de maior volume mantêm — a redução é inversamente relacionada à frequência de base, o que cria subestrutura dentro do perfil. **11.5b:** a operação **não consegue perceber** um cliente que está há dias sem movimentar o veículo; a ausência não gera evento e some no ruído de ~300 movimentos/dia. **13:** a janela do avulso tem cauda fora do horário comercial, com duas causas — visitantes de moradores do entorno e prestadores de serviço. |
| 28/08/2026 | **Seção 37 reescrita — a limitação deixou de existir.** O boleto **sempre foi gerado diretamente com o banco** e nunca mudou; o ERP alterou apenas a **entrega**, que antes exigia o financeiro imprimir cada boleto e enviar ao estacionamento para entrega em mãos, e passou a ser 100% por e-mail. Não há quebra de série na receita de mensalidade, e a digitalização da entrega é o único dos quatro efeitos do marco de 01/06 sem contrapartida negativa. |
