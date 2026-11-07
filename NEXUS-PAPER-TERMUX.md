# NEXUS Paper — protótipo para Termux

Camada independente do motor original TradingAgents. O painel funciona offline usando a biblioteca padrão do Python 3.10+ e SQLite, sem APIs nem corretora. O motor original continua a exigir as próprias dependências e não está integrado ao painel.

## Arranque

No Termux, se Python e Git ainda não estiverem presentes: `pkg install python git`. Depois, num clone deste repositório, executar `bash nexus-start.sh`. O capital inicial por defeito é 1000 USD na primeira execução. O ficheiro de estado fica em `~/.nexus-trading/nexus.sqlite3`. Nenhuma chave é necessária para esta parte.

Para um teste isolado, executar `python nexus_termux.py --db /caminho/novo.sqlite3 --capital 10000`. O capital apenas é usado ao criar uma base nova. Para testes automáticos: `python -m unittest discover -s tests -p 'test_nexus_termux.py'`.

## Como funciona

O menu recebe cotações **manuais** com bid e ask; permite abrir e fechar posições simuladas, ver histórico e acompanhar P&L realizado. As posições ficam guardadas em SQLite. Ao atualizar uma cotação, o programa verifica os limites de stop e take-profit e simula o fecho no bid/ask informado, incluindo o spread. Se houver um salto de preço, o fecho é simulado na nova cotação, não no preço do stop. Apenas são verificados preços manualmente inseridos. Não há vigilância contínua; parar o programa ou não atualizar preços impede saídas automáticas.

O tamanho é limitado por 1% do capital realizado por posição e 100% de exposição agregada em notional. O bloqueio de perda diária usa 3% do capital inicial e somente P&L fechado desde 00:00 UTC. São limites de protótipo; P&L não realizado, múltiplas posições, oscilações bruscas, comissões, swaps, granularidade de lotes, margens, latência, liquidez e risco real podem produzir perdas superiores. O capital apresentado é saldo realizado, não equity em tempo real. Não existe fonte de cotação, alerta de atualidade da fonte real nem automatismo de entrada. A idade dos dados mede apenas quando foram digitados.

## Em falta

A conexão ao grafo TradingAgents, DeepSeek/Gemini/OpenRouter, dados Forex verificados, fontes de notícias, análise automática, orquestração e execução autónoma ainda não foram implementadas ou testadas. Não assumir que o motor original ou as suas dependências funcionam no Android. Este protótipo foi testado fora do Termux e não foi validado no Realme C33. Apenas demonstra simulação manual e não é aconselhamento financeiro.

## Opções do menu

Os comandos originais mantêm o significado: `0` sair, `1` atualizar cotação manual, `2` abrir posição simulada, `3` abertas, `4` histórico, `5` fechar posição simulada. Opções adicionadas: `6` resumo de conta (estimativas), `7` detalhes por ID, `8` ajustar limites de risco dentro de tetos rígidos, `9` exportar CSV/TXT, `b` criar backup da base, `r` restaurar uma cópia (pede confirmação `RESTORE` e cria backup do estado atual antes), `a` estado local, `k` kill switch Paper persistente, `h` ajuda. O relatório e backup ficam sob o diretório de dados NEXUS em `~/.nexus-trading/`.

Restauro substitui as posições/configurações atuais pela base escolhida após verificar integridade. Mantém cópias de segurança importantes fora do telefone antes de experimentar e fecha outras sessões NEXUS antes do restauro.

## Estado do sistema

A opção `a` verifica localmente módulos, presença de chaves no ambiente sem exibir valores e integridade SQLite. Não verifica `.env`, conectividade ou fornecedores online; IA, feed Forex e broker continuam não integrados ao painel.

## Interface JD NEXUS compacta

O painel apresenta cabeçalho pequeno (o arranque já não desenha banner separado) e secções de estado, mercado manual, conta Paper e agentes desativados. A largura adapta-se ao terminal e palavras longas são quebradas entre palavras; cores só são ativadas em terminal interativo. Sem animação nem pedidos de rede. `0`–`9` conservam as funções anteriores. Agentes, feed Forex e broker são estados desconectados/pendentes, não operações disponíveis.

## Variação compacta com moldura

A moldura exibe JD/♓/peixes e slogan. Em terminais com largura suficiente, menu em duas colunas; no telemóvel, uma coluna. O estado continua Paper/local, cotações manuais, sem feed, sem broker e sem ordens reais.

## Kill switch persistente Paper

A opção `k` bloqueia novas posições simuladas usando o registo `paper_halted` na tabela `settings` já existente; não altera o esquema da base e sobrevive a reinícios do processo. Ativar exige escrever `HALT`; desativar exige escrever `RESUME`. Estado desconhecido/corrompido falha fechado e impede novas posições. O bloqueio é apenas do painel Paper, não fecha automaticamente posições existentes, que continuam a poder ser geridas/fechadas manualmente. O limite diário de perdas mantém-se independente e também bloqueia novas entradas. Não há ligação de corretora, execução real, monitorização de fundo ou promessa de proteção contra perdas.
