# Etapa 3 — as 8 perguntas do EDA

Documento de aprovação. Escolher as perguntas **antes** de abrir o notebook, senão
saem trinta gráficos e oito são escolhidos por serem bonitos.

**Base:** `logs_estacionamento_v13.csv` (66.970 registros, 180 dias).
**Filtro aplicado a cada candidata:** a resposta pode ser um parâmetro que eu mesmo
escrevi? Se sim, ela valida o gerador — não descobre nada. Ver a auditoria de origem
(seção 3.10 do `eda_v12_achados.md`), onde 8 de 15 achados caíram nesse teste.

| Classe | Significado |
|---|---|
| **VALIDAÇÃO** | Confrontado com fonte externa independente |
| **DERIVADO** | Sai das regras de negócio, não do dataset |
| **REGRA** | Confronto do dado com uma regra documentada |
| **MÉTODO** | Propriedade do dado enquanto dado |

---

## As 8 selecionadas

### 1. Onde está o dinheiro? · DERIVADO
**Pergunta:** qual segmento sustenta a receita, e quanto vale cada transação?

Gráfico: ticket médio por segmento, com o volume de transações ao lado.

O achado é a **desproporção**: o hóspede de hotel entrega mais que o avulso inteiro
com uma fração das transações. Isso sai da tabela de preços e da duração das
estadias — não do volume simulado.

⚠️ **Reportar ticket médio, não fatia da receita.** A fatia depende de quantos
clientes de cada tipo eu inventei; o ticket depende só da tabela de preços.

---

### 2. O convênio de selos custa mais do que rende · DERIVADO ⭐
**Pergunta:** o programa de cupons dá lucro?

Gráfico: margem por estadia, cruzando permanência × quantidade de selos.

**Não dá.** O selo é vendido a R$ 9 e desconta R$ 15. E a virada: **a margem inverte
com a quantidade** — quem apresenta 3 selos gera lucro, porque o desconto transborda
a conta e evapora.

Sai inteiramente das duas tabelas de preço. Não depende de nada que eu simulei.
Recomendação com número: alinhar o preço à tarifa, ou criar um selo de meia hora.

---

### 3. Vaga vendida não é vaga ocupada · MÉTODO + REGRA
**Pergunta:** quanto da garagem está realmente em uso?

Gráfico: curva de ocupação ao longo do dia, com duas linhas de referência —
capacidade total e vagas contratadas.

Três leituras: a ocupação **física** é bem menor que a **contratada**; o piso noturno
é composto pelos moradores; e o sistema **não mede nenhuma das duas** — a ocupação
precisa ser reconstruída somando entradas e saídas.

⚠️ Os níveis dependem do tamanho da base, que é escolha minha. **O que se reporta é
a distância entre as duas métricas**, não o percentual absoluto.

---

### 4. O sábado é mais pesado do que o volume sugere · DERIVADO ⭐
**Pergunta:** qual é o dia mais difícil de operar?

Dois painéis:
- manobras de carro **por hora de comércio aberto**, por tipo de dia
- ticket médio do avulso por tipo de dia, antes e depois do reajuste

**O sábado move só 4% mais carros que um dia útil — mas concentra tudo numa janela
2 horas mais curta.**

| | Manobras/dia | Janela comercial | **Manobras por hora** |
|---|---|---|---|
| Dia útil | 298 | 9,5 h | 21,7 |
| **Sábado** | 310 | **7,5 h** | **30,8** |

**42% mais intenso por hora.** E cada manobra de carro custa manobrista + elevador —
moto não entra na conta, porque o cliente estaciona sozinho. É o dia que dimensiona a
equipe, e ninguém olhando só o total diário perceberia.

**Segundo painel — o reajuste apagou o prêmio do sábado:**

| Ticket médio do avulso | Dia útil | Sábado | Prêmio |
|---|---|---|---|
| Tabela antiga | R$ 16,07 | R$ 20,93 | **+30%** |
| Tabela unificada | R$ 20,28 | R$ 21,06 | **+4%** |

O sábado era o dia **cheio e caro**. Virou só o dia cheio. Ele ainda carrega ~27% da
receita de avulso da semana inteira em um único dia — e agora sem nenhum prêmio de
preço.

⚠️ **Enquadramento honesto:** que o sábado é o dia de maior movimento **não é
descoberta** — é o que o informante descreveu e o gerador reproduz. O que a análise
acrescenta é a *consequência*: a intensidade por hora e a perda do prêmio de preço.
Nenhuma das duas é entrada de ninguém. Escrever como "quantificando o que o operador
já sabia", nunca como "descobri que sábado é cheio".

---

### 5. A recarga elétrica contra o mundo real · VALIDAÇÃO ⭐
**Pergunta:** o simulado descreve a operação de verdade?

Gráfico: recargas por dia, mês a mês, simulado sobre a série real do app.

**1,01× em volume e 0,99× em energia.** É a única validação externa do projeto, e
mede uma curva de adoção que octuplicou em 11 meses.

Reaproveita o gráfico da Etapa 1 com os dados do v13.

---

### 6. Quantas tomadas o crescimento exige · DERIVADO ⭐
**Pergunta:** a 3ª tomada em obra resolve por quanto tempo?

Gráfico: probabilidade de o motorista chegar e não achar tomada livre, por número de
tomadas e por volume de demanda.

**Satura em ~5,4 recargas/dia** — poucos meses no ritmo atual. E o achado não óbvio:
**potência rende mais que número de vagas.** Trocar 3 tomadas comuns por trifásicas
triplica a capacidade sem abrir vaga nova.

Modelo de filas sobre a duração medida no app. Não é o dataset falando.

---

### 7. Depois da 3ª hora, a vaga é de graça · DERIVADO ⭐
**Pergunta:** a partir de quando a permanência deixa de gerar receita?

Gráfico: valor cobrado em função da permanência, com a distribuição real das estadias
por baixo.

**A tarifa para de subir na 3ª hora.** O que a tabela chama de "12 horas" não é uma
faixa — é o **teto** da soma de horas adicionais:

| Permanência | Valor | Δ |
|---|---|---|
| 30 min | R$ 10 | — |
| 1 h | R$ 15 | +5 |
| 2 h | R$ 23 | +8 |
| **3 h** | **R$ 30** | +7 · **teto** |
| 4 h … 12 h | R$ 30 | **+0** |

Da 3ª à 12ª hora o cliente ocupa a vaga **sem custo marginal nenhum**. E não é caso
raro: **24,5% das estadias de avulso passam das 3 horas.**

No período, isso são ~998 horas de vaga entregues acima do teto. Cobrando os R$ 8/hora
até a 12ª, seriam ~R$ 13 mil a mais — **16% da receita de avulso**.

Não é recomendação de subir preço: o teto pode ser exatamente o que atrai o cliente
de meio-período. É a quantificação do que ele custa, que ninguém tinha.

⚠️ **A faixa de 24 horas, essa sim, é pouco usada** — e tem um público específico
identificado pelo informante: quem vai passar a noite e não está em hotel conveniado.
No dataset ela nunca é acionada (permanência máxima de avulso: 7,9h), o que é uma
**limitação a declarar**: o v13 não gera pernoite de avulso.

---

### 8. A inadimplência aparece como receita · DERIVADO ⭐
**Pergunta:** quanto custa um mensalista que não paga?

Gráfico: comparação entre a mensalidade devida e o que o cliente efetivamente gera
enquanto está bloqueado.

**Não aparece como perda em lugar nenhum.** O cliente bloqueado continua entrando e
passa a pagar ticket; antes de junho, o boleto corria com juros. Nos dois regimes,
quem não pagou gera uma linha **positiva** no caixa.

Um painel de faturamento diário não enxerga o problema. É preciso cruzar com o ERP.
Métrica que engana pelo sinal — e é a mais "consultoria" da lista.

---

## Fora da lista, e por quê

Todas interessantes. Todas caem no teste da auditoria.

| Candidata | Por que fica de fora |
|---|---|
| "Sábado tem o dobro do avulso" como manchete | **PARÂMETRO** — a taxa por tipo de dia é sorteada direto do que o informante descreveu. Entrou na pergunta 4, mas só como contexto: o que se reporta é a intensidade por hora e o prêmio de preço perdido |
| A área de moto teve dois regimes (~50 até maio, ~20 depois) | Saiu da lista a pedido, e o destino é coerente: é a mesma história das **trinta motos que não saíram do lugar**, que já estava na trilha de curiosidades |
| Mix de segmentos e volume por dia | **PARÂMETRO** — o tamanho da base é escolha de modelagem |
| Domingo rende igual ao dia útil | **ARTEFATO** — depende de o fluxo de hotel ser plano entre os dias, que é suposição minha, não dado |
| Aderência ao totem em 90% | **PARÂMETRO** — o valor é a constante do gerador. A *lição do denominador* é ótima, mas é método: vai para o post de fechamento |
| Curva horária de qualquer coisa | **PARÂMETRO** — as janelas de chegada são constantes fixas. Já me enganou uma vez |
| Aderência do operador em carga e descarga | **PARÂMETRO** no valor. Mas o **custo do erro** é derivado, e cabe como nota dentro da pergunta 1 |

---

## O que sobra para os outros posts

- **Post de fechamento:** a auditoria de origem, a métrica que muda 36 pontos, o
  "usei meu próprio dado como prova". São achados de método e pesam demais no
  semanal.
- **Curiosidades (trilha paralela):** as trinta motos que não saíram do lugar, o
  cliente que atrasa e nunca é bloqueado, perder o maior cliente e a operação
  melhorar, o prédio da Justiça do Trabalho.

---

## Balanço da lista

| Classe | Quantas |
|---|---|
| DERIVADO | 6 |
| VALIDAÇÃO | 1 |
| MÉTODO + REGRA | 1 |

**Nenhuma PARÂMETRO.** A lista responde sobre **dinheiro** (1, 2, 4, 7, 8),
**capacidade** (3, 6) e traz **uma validação externa** (5) — que são as perguntas que
um dono de estacionamento faz de verdade.

⚠️ **A troca custou o único item de classe REGRA.** A pergunta antiga (dois regimes na
área de moto) era o exemplo mais claro do projeto de uma conclusão que se inverte
conforme a data de corte. Ela continua viva como curiosidade, mas a lista perdeu o
tipo de achado que nasce do **confronto entre dado e regra documentada** — vale ter
isso em mente ao escrever o post de fechamento, onde essa classe é a mais forte.

---

## Antes de rodar

- [ ] Aprovar ou trocar perguntas desta lista
- [ ] Confirmar que a base é o **v13** (o v12 tem hotel e moto errados)
- [ ] Decidir se as 8 viram 8 gráficos ou se alguma pede dois painéis
- [ ] Definir se o post da Etapa 3 mostra as 8 ou seleciona as 4 mais visuais
