# Relatório de Auditoria e Melhorias — TradingAgents-NEXUS
**Data:** 03-11-2026  
**Repositório:** https://github.com/BUDA1999/TradingAgents-NEXUS  
**Escopo:** revisão estática da estrutura pública, documentação e ficheiros NEXUS identificáveis. Não foi executado no Realme C33 nem foram executados os testes do repositório.

## 1. Resumo executivo

O repositório combina o framework original TradingAgents (Tauric Research) com uma camada NEXUS em desenvolvimento. A camada de simulação manual é útil como protótipo offline, mas não deve ser confundida com um sistema de trading automático ou com uma integração funcional dos agentes de IA.

A própria documentação informa que:
- o painel paper funciona sem API e sem corretora;
- os preços são introduzidos manualmente;
- não existe monitorização contínua quando o programa está parado;
- o motor TradingAgents não está integrado no painel NEXUS;
- a compatibilidade do motor completo com Termux/Android não foi validada;
- a experiência Forex ainda não é uma plataforma Forex pronta.

**Conclusão:** manter a execução exclusivamente simulada e corrigir primeiro a integridade dos dados, os limites de risco, os testes e a integração modular.

## 2. Constatações, riscos e soluções

| Prioridade | Constatação | Risco/efeito | Solução recomendada |
|---|---|---|---|
| P0 | Preços são introduzidos manualmente | Cotação pode estar desatualizada ou digitada incorretamente | Criar interface de cotação com origem, timestamp, validação Bid/Ask e bloqueio de dados antigos |
| P0 | Não há monitorização contínua | Stops/targets não são observados enquanto a aplicação está fechada | Não prometer execução automática; numa fase futura, usar serviço de polling controlado e alertas, com tratamento de falhas |
| P0 | P&L apresentado é saldo realizado, não equity | O utilizador pode subestimar risco aberto | Mostrar saldo, P&L não realizado, equity estimada e exposição separadamente |
| P0 | Limite diário usa P&L fechado desde 00:00 UTC e capital inicial | Não representa necessariamente drawdown total nem o dia local da corretora | Definir timezone da sessão, incluir P&L realizado + não realizado e persistir o bloqueio diário |
| P0 | Dimensionamento Forex depende de especificações que variam por instrumento/corretora | Risco monetário e tamanho de lote podem estar errados | Criar especificações por símbolo: tamanho do contrato, pip/tick, moeda de lucro, conversão, margem, comissão e swap |
| P1 | NEXUS e TradingAgents não estão integrados | Painel e agentes funcionam como componentes separados | Criar uma camada de serviço/adaptador, sem acoplar a interface diretamente ao grafo |
| P1 | `main.py` contém ticker e data fixos (`NVDA`, `2026-09-01`) | Execução repetida analisa sempre o mesmo ativo/data | Substituir valores fixos por argumentos CLI e validar ticker/data |
| P1 | Documentação declara Python 3.10+ para Paper, enquanto o framework principal exige Python 3.11+ | Confusão sobre compatibilidade e instalação | Documentar requisitos separados para Paper NEXUS e motor TradingAgents |
| P1 | Não há validação Android demonstrada | Dependências nativas podem falhar no Termux | CI em Linux + teste manual documentado em Android; instalar em etapas e não exigir Docker no telefone |
| P1 | Dois módulos de simulação (`nexus_termux.py`, `nexus_paper.py`) | Regras podem divergir com o tempo | Definir um único núcleo de validação/risco partilhado e manter interfaces finas |
| P1 | Dados Yahoo podem não ser executáveis nem em tempo real para Forex | Sinais baseados em preço inadequado | Exigir fornecedor identificado, timestamp, atraso e spread; bloquear sinal quando a fonte não cumprir critérios |
| P2 | Falta dashboard unificado e telemetria | Difícil auditar decisões e erros | Painel textual com estado do sistema, fonte/idade dos dados, posições, equity e logs |
| P2 | Falta backtesting específico Forex validado | Estratégia pode parecer boa sem custos realistas | Backtest com spread variável, comissão, swap, slippage, timezone e prevenção de look-ahead |

## 3. Pontos de código identificados

### `main.py`
O ficheiro inicializa `TradingAgentsGraph` e chama `propagate("NVDA", "2026-09-01")`. É uma demonstração fixa, não uma interface de operação NEXUS.  
**Solução:** criar uma CLI própria com `--ticker` e `--date`, manter as variáveis de ambiente do projeto e tratar exceções com mensagens claras.

### `nexus-start.sh`
O script identifica a pasta pelo caminho do próprio ficheiro, verifica Python, mostra o banner e executa `nexus_termux.py`. É uma boa abordagem para não depender de um caminho fixo. Contudo, o comentário deixa claro que não instala nem inicia o motor de IA.  
**Solução:** manter essa honestidade na mensagem do menu e separar comandos `paper` e `ai`.

### `NEXUS-PAPER-TERMUX.md`
A documentação já descreve limitações importantes: preços manuais, ausência de vigilância contínua, custos de mercado omitidos e falta de integração.  
**Solução:** manter estas limitações visíveis no ecrã principal, não apenas no documento.

### `NEXUS-TERMUX.md`
A documentação corretamente alerta que o TradingAgents original é orientado a ações e que os fundamentos de ações não se aplicam diretamente a Forex.  
**Solução:** não reutilizar os agentes de fundamentos de ações para produzir decisões Forex. Criar analistas próprios de macroeconomia, calendário económico, taxas, notícias e estrutura de mercado.

## 4. Código de melhoria incluído neste pacote

Foi preparado um módulo **aditivo** `codigo/nexus_safety.py`, sem substituir os ficheiros existentes. Ele implementa:
1. validação de Bid/Ask e spread;
2. validação de idade da cotação;
3. bloqueio de cotação inválida ou antiga;
4. cálculo genérico do risco monetário de uma posição linear;
5. rejeição quando o risco excede o limite configurado.

**Limite importante:** este cálculo é genérico e não calcula lotes Forex/XAUUSD. Antes de usar tamanho de posição real, é obrigatório implementar especificações do contrato, moeda de conversão, tick value, margem e custos da corretora.

Testes incluídos em `testes/test_nexus_safety.py`. O código é uma base para integração; não foi aplicado ao repositório remoto nem validado em Android.

## 5. Plano de execução recomendado

### Fase 1 — Estabilização (primeiro)
- Fazer cópia/branch de segurança.
- Executar os testes atuais.
- Adicionar os testes de validação de cotação e risco deste pacote.
- Corrigir erros de importação, caminhos e persistência.
- Não ligar corretora nem conta real.

### Fase 2 — Dados fiáveis
- Escolher fornecedor de dados com documentação e limites conhecidos.
- Guardar `source`, `timestamp`, `bid`, `ask` e `symbol`.
- Definir limite de idade por timeframe.
- Bloquear entradas quando os dados estiverem antigos, incompletos ou incoerentes.

### Fase 3 — Risco e contabilidade
- Separar saldo, equity, margem usada, margem livre e P&L aberto/fechado.
- Implementar especificações corretas por instrumento.
- Aplicar limites diários com timezone configurável e P&L total.
- Persistir bloqueios e eventos de risco.

### Fase 4 — Integração dos agentes
- Criar um adaptador que recebe símbolo, data e contexto de mercado.
- Validar a resposta do agente num schema estruturado.
- Fazer o motor de risco aprovar/rejeitar a proposta.
- Registar prompt/modelo, fonte dos dados, decisão, confiança, timestamp e motivo da rejeição.
- Não permitir que o LLM envie ordens diretamente.

### Fase 5 — Android/Termux
- Testar primeiro o Paper offline.
- Medir memória, CPU, bateria e armazenamento.
- Instalar dependências do motor original uma a uma.
- Documentar o que funciona no Realme C33 e o que deve correr num servidor externo.

## 6. Critérios mínimos de aceitação

- Cotação antiga nunca gera nova entrada.
- `bid <= 0`, `ask <= 0` ou `ask < bid` são rejeitados.
- Risco acima do limite é rejeitado.
- Falha de rede não cria posição.
- Reiniciar o Termux não perde posições nem bloqueios.
- Cada decisão tem fonte e timestamp.
- Nenhum módulo executa ordens reais nesta fase.
- Testes automatizados passam antes de cada atualização.

## 7. Veredito

O projeto tem uma base interessante e uma separação inicial entre motor original e protótipo NEXUS. O principal trabalho agora não é adicionar mais efeitos visuais ou mais fornecedores de IA. É transformar dados, risco e decisões em componentes auditáveis.

**Prioridade estratégica:** primeiro segurança e fiabilidade; depois integração IA; por último automação. Não usar dinheiro real com o estado atual.

## 8. Fontes consultadas
- Repositório: https://github.com/BUDA1999/TradingAgents-NEXUS
- `NEXUS-PAPER-TERMUX.md`
- `NEXUS-TERMUX.md`
- `nexus-start.sh`
- `nexus_termux.py`
- `nexus_paper.py`
- `main.py`
