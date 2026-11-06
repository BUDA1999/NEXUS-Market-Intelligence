# JD NEXUS — auditoria inicial e prioridades (2026-11-06)

## Escopo e método

Repositório efetivo: https://github.com/BUDA1999/NEXUS-Market-Intelligence (o endereço TradingAgents-NEXUS é o nome anterior). Revisão estrutural da árvore e inspeção focal do painel, backup, validação, instalador, engine, fornecedores, dados, testes e documentação. Isto **não é uma auditoria exaustiva de segurança ou validação de produção**. Não foi feito teste no Termux nesta sessão nem ligações autenticadas a APIs.

## Constatações

1. `tradingagents/graph`, `agents` e `llm_clients` são o motor original TauricResearch. Existe orquestração e suporte a múltiplos fornecedores no upstream, mas o painel `nexus_termux.py` não está ligado ao grafo. O motor usa níveis quick/deep; seleção por agente ainda não foi comprovada.
2. `nexus_termux.py` implementa menu, SQLite, preços manuais e posições simuladas, resumo, limites configuráveis, exportação, backup/restauro. A cotação não é feed ao vivo; os stops só são observados ao atualizar manualmente. Valor mostrado como saldo e P&L estimado não equivale a margem/equity de corretora.
3. `nexus_paper.py` e validações de risco no painel sobrepõem-se; `nexus_safety.py` é separado e não está ligado ao fluxo. Risco divergente é possível. Consolidar com testes de regressão antes de automatizar.
4. `nexus_api.py` faz um teste HTTP opcional para alguns fornecedores; não executa agentes nem comprova que um modelo ou saldo de API funciona. Não foram usadas chaves reais.
5. Adaptador NEXUS para feed Forex bid/ask com origem, hora, latência e preços executáveis não existe. O mapa upstream para XAU usa futuro `GC=F`, que não deve ser tratado como XAU/USD spot. Validação de contrato, custos, câmbio, spread e dados antigos é obrigatória.
6. Não existe adaptador broker integrado ao painel nem execução real autorizada. Não há monitorização contínua, estratégia automática NEXUS, agendamento/recuperação de worker, backtesting Forex validado, ou kill switch persistente completo. Não declarar produção.
7. `pyproject.toml` exige Python >=3.11 e `pandas>=3.0.6`; `constraints-termux.txt` limita pandas <3. Instalação nativa do motor está bloqueada no script até validação. O utilizador informou Python 3.14.8 / SQLite 3.54.1 e que o painel abriu no seu Termux, mas motor, APIs e a presente versão do status não foram testados nesse aparelho.
8. GitHub: 0 issues e 0 PRs públicos abertos na data da auditoria. `main.py` original é uma demonstração com ticker/data fixos; preferir CLI/adaptador separado em vez de executá-lo como se fosse NEXUS.

## Testes e limitações

- 26 testes focados do painel Paper, validador e backup passaram em Linux Python 3.13; a execução emitiu `ResourceWarning` de conexões SQLite em testes legados.
- Suíte global: `pytest` inicialmente ausente; após instalar dependências de teste numa cópia temporária, a execução foi interrompida pelo limite de espaço. **Não aprovada**. A tentativa com `unittest` também teve erros de importação (o upstream usa pytest e bibliotecas ausentes). Não extrapolar os 26 testes para o engine inteiro.
- Alteração de status: executar `python -m unittest discover -s tests -p 'test_nexus_status.py' -v` e `python -m unittest discover -s tests -p 'test_nexus_termux.py' -v`; 21 testes passaram em Linux, sem testes de rede nem Android.
- A opção `a` mostra apenas verificações locais e nomes de chaves detetadas no processo; não lê `.env`, não imprime chaves e não afirma conectividade.

## Ordem de implementação recomendada

1. Estabilizar o núcleo Paper: consolidar risco, persistência transacional, reinício, idempotência, quote freshness e kill switch persistente; validar backups e concorrência.
2. Definir interface de mercado com origem/timestamps, dados reais de um fornecedor oficialmente documentado, validar instrumentos e falhas de rede com testes simulados antes de chamadas reais.
3. Integrar o grafo original através de adaptador restrito a pesquisa, usando credenciais locais e validação de respostas; manter propostas separadas de execução. Testar limites/timeout e Termux.
4. Só depois criar automação opt-in exclusivamente Paper, com observabilidade e retoma segura; cobertura de riscos e simulação com custos conhecidos.
5. Backtest Forex e relatórios auditáveis com dados de origem identificada; documentar conclusões sem alegar rentabilidade.
6. Planejar adaptadores de corretora somente numa fase futura separada: sem ligação a conta real até validações rigorosas e autorização expressa do utilizador.

Todas as etapas dependentes de APIs reais exigem fornecedor, credenciais e eventual plano/custos; nenhum segredo deve ser incluído no repositório ou numa captura. O estado atual não é produção.

## Adenda — interface compacta

Foi criada uma camada de apresentação independente `nexus_ui.py`, mantendo o menu e o motor Paper existente. A vista identifica cotações manuais ou indisponíveis, sem assumir variação. Todos os agentes aparecem como DISABLED porque não há execução do grafo pelo painel. O teste automatizado cobre larguras de 24, 40 e 45 colunas em Linux; requer confirmação visual no Termux.
