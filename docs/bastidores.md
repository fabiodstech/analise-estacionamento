# Os bastidores dos bastidores

> Quatro vezes eu peguei um número que o meu próprio gerador tinha produzido e
> apresentei como descoberta sobre o mundo real.

Este documento é sobre os erros do projeto, e é a parte de que mais me orgulho. Não
por serem erros bonitos — não são — mas porque a forma como foram encontrados diz mais
sobre análise de dados do que qualquer gráfico das outras páginas.

---

## O problema central de dado sintético

Um dataset sintético tem uma propriedade traiçoeira: **ele responde a qualquer
pergunta.** Você calcula uma média, sai um número. Plota uma distribuição, sai uma
curva. Nada avisa que a resposta é a sua própria premissa voltando.

Com dado real, se a análise erra, a realidade eventualmente discorda. Com dado
sintético, a análise e a premissa concordam sempre — porque são a mesma coisa.

Levei quatro erros para entender isso direito.

---

## Erro 1 — O R$ 267

O maior cliente da garagem era uma empresa de logística que pagava **R$ 3.000 por
mês** por um espaço com ~30 motos. Ela recusou um reajuste e saiu.

Para avaliar se o reajuste fazia sentido, calculei o valor por moto: R$ 3.000 ÷ 30 =
**R$ 100 por moto**. E comparei com o que um mensalista de moto comum paga — **R$ 267**.

Conclusão publicada: *a empresa pagava 37% da tarifa praticada com os demais clientes*.

**O R$ 267 saiu do dataset sintético.** Era a média dos boletos que o próprio gerador
tinha inventado. Eu usei um número inventado por mim como régua para avaliar uma
decisão comercial real.

E havia um segundo erro dentro do primeiro: comparei R$ 100 **por moto** com R$ 267
**por cliente** — e clientes com duas ou três vagas puxavam a média. O comparável era
R$ 190 por vaga.

**Quem pegou:** o informante, perguntando *"de onde saiu esse R$ 267?"*.

**O desfecho é o mais interessante.** Ao investigar, descobri que os valores do
gerador estavam **certos** — só nunca tinham sido documentados. Com a tarifa real
(R$ 180–200 por vaga de moto), a comparação correta é R$ 100 contra R$ 180–200, e o
reajuste proposto levaria a empresa a **83–93% do padrão**.

Ou seja: **o reajuste não era um aumento, era a remoção de um desconto.** Uma leitura
melhor do que a que eu tinha — e que só apareceu porque o número foi questionado.

---

## Erro 2 — A curva de energia

O estacionamento instalou placas solares por causa do custo dos elevadores. Fui
analisar se a geração e o consumo coincidiam.

Extraí do dataset a curva horária de movimentação de carros — cada movimento é uma
viagem de elevador — e encontrei **dois picos**, de manhã e no fim da tarde, com um
vale ao meio-dia. A geração solar tem **um** pico, exatamente no vale.

Conclusão publicada: *as curvas são descasadas, e a recarga elétrica é o complemento
natural da geração*. Com recomendação de negócio em cima.

**Aquela curva eram duas constantes do meu gerador.** Linha 529:

```python
janela_in, janela_out = (7.0, 9.5), (17.0, 19.5)
```

Os "dois picos" eram as janelas de chegada e saída do mensalista trabalhador, lidas de
volta e apresentadas como observação sobre o mundo.

**Quem pegou:** o informante, dizendo que na prática o pico de recarga coincide com o
pico de elevador, e que a geração nunca cobre o consumo.

**O que ficou no lugar** é mais simples e mais correto: a solar reduz o custo **médio**
da energia, não o **marginal** do próximo kWh — porque o prédio é importador líquido o
tempo todo. Não existe cenário de energia própria a custo zero.

---

## Erro 3 — A aderência ao totem

A diretoria orienta que avulsos pagando com cartão usem o totem. Medir a aderência a
essa orientação parecia trivial.

Só que o número dependia inteiramente de **quem se conta como "avulso"**:

| Denominador | Aderência |
|---|---|
| `Categoria = 'Avulso'` + cartão | **54,2%** |
| `Subcategoria = 'Avulso Regular'` + cartão | 63,8% |
| + só carro | 75,6% |
| + sem selo e sem recarga | 83,1% |
| **+ sem carga e descarga** | **90,3%** |

**36 pontos de amplitude, e nenhuma versão é erro de cálculo.** As quatro primeiras
contam como desvio do atendente pagamentos que a **regra obriga** a ir ao caixa —
hotel, moto, selo, recarga elétrica, carga e descarga.

E a causa raiz estava no meu próprio documento de regras: a fórmula de uma seção
classificava como desvio o que outra seção tornava obrigatório.

**Publiquei 83,1%.** Parei uma camada cedo: carga e descarga também é caixa
obrigatório, e o segmento **não tem rótulo no sistema** — fica escondido dentro de
avulso e só é identificável por permanência somada à cancela de saída.

Junto disso, reportei uma variação por faixa horária (55% às 8h contra 93% à noite,
p = 0,025) e inventei uma explicação operacional: fila na abertura, atendente sozinho
de madrugada.

**Era composição.** Carga e descarga sai em minutos, sempre pelo caixa, e representa
32% das saídas das 8h contra 0% depois das 19h. Excluindo o segmento, o padrão
desaparece: **p = 0,527**.

---

## O ponto de virada — a auditoria de origem

Depois do terceiro erro, parei de corrigir caso a caso e fui classificar **todos** os
achados pela origem. Quinze achados, seis categorias:

| Origem | Significa | Vale como achado? |
|---|---|---|
| **PARÂMETRO** | O número foi sorteado de uma constante do gerador | ❌ |
| **ARTEFATO** | Emerge da composição, sem correspondência no mundo | ❌ |
| **VALIDAÇÃO** | Comparado com fonte externa independente | ✅ |
| **DERIVADO** | Sai das regras de negócio, não do dataset | ✅ |
| **REGRA** | Confronto do dado com uma regra documentada | ✅ |
| **MÉTODO** | Propriedade do dado enquanto dado | ✅ |

**Oito dos quinze eram o gerador se descrevendo.** Entre eles, coisas que eu tinha
escrito com entusiasmo: o sábado com o dobro do movimento, a curva de ocupação
invertida no domingo, a permanência mediana do avulso, o pico de motos simultâneas.

Isso não os torna inúteis — verificar que o gerador reproduz a regra escrita é
exatamente o propósito da suíte de validação. Mas **não são descobertas sobre o
estacionamento**, e escrevê-los como se fossem é a falha que o projeto inteiro se
propôs a evitar.

A regra que saiu disso:

> Dado sintético só produz achado sobre o mundo em quatro situações: confrontado com
> **fonte externa**, confrontado com **regra documentada**, quando o achado é
> **derivado das regras** e não do dataset, ou quando é sobre o **dado enquanto dado**.
> Todo o resto é o gerador falando sozinho.

---

## Erro 4 — E a auditoria não bastou

Escrita a auditoria, construí o painel. Nele, uma métrica de destaque: **"manobristas
no pico: 4"**.

A cadeia era:

- **31 manobras por hora às 8h** ← contagem no dataset ← **a janela `07:00–09:30` do
  gerador**, o mesmo erro do caso 2
- **8 manobras por hora por manobrista** ← **eu inventei**, sem fonte nenhuma
- **4 manobristas** = os dois acima, divididos

Um número inventado dividido por outro, na aba principal, **logo depois de eu ter
escrito o documento sobre exatamente isso.**

**O padrão que faltava:** a auditoria cobria o *relatório*. Quando construí uma
*ferramenta*, apresentei a saída dela com a confiança da entrada. **Cada mudança de
formato reabre a porta.**

---

## Como o erro 4 foi resolvido — e por que esse é o melhor final

O conserto não foi apagar a métrica. Foi pedir **a escala real de trabalho**.

Com ela — 10 pessoas, turnos de segunda a sábado, intervalos — deu para inverter a
conta: em vez de dividir manobras por um ritmo inventado, rodei um otimizador de
cobertura de turnos em vários ritmos e procurei aquele em que **a escala mínima
calculada coincide com a que a casa realmente pratica**.

| Ritmo testado | Mínimo calculado (dia útil) | Escala real |
|---|---|---|
| 8 manobras/h | 9 turnos · 66,0 h | 7 turnos · 49,5 h |
| 10 manobras/h | 8 turnos · 59,5 h | " |
| **12 manobras/h** | **7 turnos · 51,5 h** | **7 turnos · 49,5 h** |

E o sábado converge no mesmo valor. **Os dois dias apontando para o mesmo ritmo** é
um sinal que um chute isolado nunca teria.

O parâmetro deixou de ser invenção minha e passou a ser **calibrado contra a
operação**. E o painel ainda deixa o controle na barra lateral, porque o tempo de
manobra nunca foi cronometrado — a ferramenta oferece a conta, quem tem o número é
quem opera.

---

## O que os quatro erros têm em comum

Nenhum foi pego por teste. **Todos foram pegos por alguém que conhece a operação
lendo o resultado e dizendo "não é assim que funciona".**

Isso não é acaso. Um teste automatizado compara o dado com o que eu declarei esperar —
e nos quatro casos o problema era a *expectativa*, não a execução. A suíte de 25
asserções passava em todas as versões.

O que corrigiu foi o loop com o informante. E é por isso que o documento mais
importante deste repositório não é o código:
é [regras_de_negocio.md](regras_de_negocio.md), com 39 seções, um histórico de
revisões e as contradições internas que a análise encontrou nele.

---

## Três coisas que mudaram no projeto por causa disso

**O gerador passou a ler os parâmetros de um arquivo.** Nenhum número literal no
código, e o validador lê o mesmo arquivo. A auditoria encontrou oito números que
viviam só no código — a tarifa de recarga, os valores de mensalidade, a taxa de
inadimplência, o bloqueio automático — e nenhum teste pegava, porque o validador tinha
as próprias constantes copiadas do gerador.

**As perguntas da análise passaram a ser escolhidas antes de abrir o notebook**, e
cada uma teve de passar no filtro da auditoria. As que não passaram ficaram de fora,
por mais interessantes que fossem — inclusive a melhor delas.

**Cada afirmação carrega a origem.** No relatório, no painel e neste documento, o que
é medido, o que é derivado de regra e o que é ilustração de ordem de grandeza estão
separados. Dez números do projeto são seguros; seis são ilustrativos, e estão marcados.

---

## Se eu recomeçasse

**Faria a auditoria de origem no primeiro dia**, não depois do terceiro erro. É um
exercício de meia hora que teria evitado tudo.

**Levaria os números de volta ao informante mais cedo.** Os quatro erros foram pegos
por ele; três poderiam ter sido pegos antes de virarem conclusão escrita.

**E desconfiaria mais de números bonitos.** A separação perfeita dos perfis de
cliente, a validação que bate em 0,99×, o pico que coincide com o que o informante
lembrava — todos foram, em algum grau, bons demais. Dois se sustentaram; os outros
não.
