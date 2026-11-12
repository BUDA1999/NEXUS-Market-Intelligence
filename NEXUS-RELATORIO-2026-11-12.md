# NEXUS — relatório de progresso (2026-11-12)

## Estado confirmado

- O painel `nexus_termux.py` continua a ser uma aplicação Paper/manual independente do motor TradingAgents.
- No Realme C33, Termux detectou Python 3.14.10 e SQLite 3.54.1. O painel está presente; o perfil `engine` no Termux nativo não passou por falta de dependências.
- Foi instalado Debian via `proot-distro`; o utilizador clonou o repositório, criou `.venv` e instalou o projeto. Dentro do Debian, Python 3.13.5 satisfaz o requisito do projeto.
- O utilizador reportou que `python -m cli.doctor --profile engine` no Debian terminou com 29 verificações OK. Isto valida a presença das dependências, não uma análise completa no dispositivo.
- OpenRouter: autenticação por `nexus_api.py openrouter --check` devolveu HTTP 200 no Debian. Foi testada uma chamada de inferência simples a um modelo gratuito ERNIE; resposta concluída e custo reportado pela API: $0. Não houve chamada de análise financeira.
- Twelve Data: endpoint de câmbio consultado para EUR/USD e XAU/USD. Retorna uma taxa `rate` e `timestamp`, não bid/ask. A consulta de taxas foi publicada como leitura independente e NÃO alimenta posições Paper.
- A chave OpenRouter não está no repositório nem neste relatório. Não se presume se a variável de ambiente foi removida da sessão Debian.

## Resposta operacional — o que acontece ao arrancar

Atualmente, sim: variáveis `export` definidas na sessão Debian são temporárias. Ao fechar aquela sessão e abrir outra, têm de ser definidas novamente, a menos que seja criado um mecanismo local de configuração persistente. O teste de OpenRouter não integra nem arranca automaticamente os agentes.

O comando `bash nexus-start.sh` no Termux só arranca o painel Paper. Não arranca o Debian, não entra no clone dentro de proot e não inicia o motor. Os agentes ainda não estão ligados ao painel. Não afirmar que o NEXUS está automaticamente conectado ao OpenRouter.

## Próximas tarefas técnicas

1. Preparar configuração local persistente e segura para o motor dentro do Debian, fora do Git, com permissões restritas e sem imprimir a chave; verificar o comportamento real do carregamento de `.env` e a forma de inicialização antes de instruir o utilizador.
2. Fazer uma verificação mínima do CLI com o fornecedor OpenRouter e um modelo gratuito, de forma opt-in, limitada e sem executar ações de trading. Distinguir claramente diagnóstico/autenticação de análise.
3. Investigar separadamente o caminho de integração da análise IA ao NEXUS, porque o painel atual não está ligado ao grafo TradingAgents.
4. Resolver uma fonte de dados de mercado adequada a Forex/metal e compatível com os campos e licença necessários. Não sintetizar bid/ask a partir de uma taxa única e não ligar taxas de leitura às posições.
5. Continuar a preparar modo demo/sandbox de broker apenas em alterações isoladas e mockadas. Não usar credenciais reais, não conectar conta de dinheiro real e não enviar ordens sem autorização explícita posterior.
6. Relatar cada atualização neste repositório em changelog/relatório Markdown, com commit verificável, testes e limitação explícita (Linux vs Termux). Nunca declarar validação no telefone sem confirmação do utilizador.

## Segurança e limites

- Nunca gravar chaves, tokens ou conteúdo de `.env` no GitHub, issue, changelog, captura ou relatório.
- Não instruir o utilizador a colar chaves no chat.
- Não ativar trading real, conta live ou ordens automáticas. A vontade de ir além do Paper significa investigar/preparar a transição, não autorização para executar operações.
- O teste de um modelo gratuito comprovou apenas uma resposta simples; não comprova qualidade, disponibilidade contínua, custo futuro zero ou adequação para análise financeira.


## Atualização — arranque persistente OpenRouter

- Adicionados scripts de configuração de primeira utilização e launcher do motor no Debian/proot.
- Após o utilizador executar uma vez `bash scripts/setup-openrouter.sh` e inserir a chave no prompt oculto, a chave fica em `~/.config/nexus/openrouter.env` fora do clone, diretório 700 e ficheiro 600; `.bashrc` carrega apenas modelo/provider nas novas sessões; o segredo só é carregado pelo launcher.
- `bash scripts/nexus-engine-start.sh` arranca o CLI TradingAgents com configuração persistente. Pode consumir créditos conforme modelo. Não liga o painel Paper ao grafo e não executa trading por conta própria.
- Scripts passaram `bash -n` e teste isolado em Linux com chave sintética; ainda não executados no Debian do telefone. O utilizador precisará atualizar o clone Debian para receber os scripts e configurar uma vez.
