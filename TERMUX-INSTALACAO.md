# Guia de instalação do NEXUS Market Intelligence no Termux

Este guia separa o protótipo NEXUS do motor original. **Começa pelo painel paper**: não precisa de chaves API nem de instalar as dependências pesadas do TradingAgents.

> Compatibilidade do motor completo com o Realme C33/Android ainda não foi validada. Os comandos abaixo são uma rota de diagnóstico, não uma promessa de que todas as dependências funcionarão.

## O que vai rodar

- **NEXUS Paper** (`nexus_termux.py`): Python padrão + SQLite; cotações são introduzidas manualmente, não há feed ao vivo.
- **Motor TradingAgents** (`tradingagents/`, `cli/`): requer Python >=3.11 e dependências definidas em `pyproject.toml`. É independente do painel; ainda não está integrado com ele.

## 0. Preparar Termux

Instala Termux de uma fonte atualmente mantida, como [F-Droid](https://f-droid.org/packages/com.termux/) ou a página oficial do [Termux no GitHub](https://github.com/termux/termux-app). Evita instalar APKs de fontes desconhecidas. Depois abre Termux e executa:

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git curl
```

Não é preciso conceder acesso ao armazenamento compartilhado para clonar e executar o projeto dentro de `$HOME`. `termux-setup-storage` só é necessário se quiseres aceder aos teus ficheiros partilhados do Android. O `termux-wake-lock` e alterar otimização de bateria não são necessários para experimentar o painel interativo; não deixam o processo protegido contra todos os encerramentos do Android.

Confere espaço e memória:

```bash
df -h "$HOME"
free -h
```

## 1. Clonar e diagnosticar

```bash
cd "$HOME" || exit 1
if [ -d "$HOME/NEXUS-Market-Intelligence/.git" ]; then
  echo 'Repositório já existe; vou atualizá-lo.'
  cd "$HOME/NEXUS-Market-Intelligence" && git pull --ff-only
else
  git clone https://github.com/BUDA1999/NEXUS-Market-Intelligence.git "$HOME/NEXUS-Market-Intelligence" || exit 1
  cd "$HOME/NEXUS-Market-Intelligence" || exit 1
fi
bash nexus-diagnostico.sh
```

O diagnóstico lê versões, memória, espaço e presença de ficheiros. Não instala pacotes nem verifica as chaves. Confirma Python e arquitetura antes de continuar. Para o motor original, é necessário Python 3.11 ou superior.

## 2. Executar primeiro o NEXUS Paper

```bash
python nexus_termux.py --check
python -m unittest discover -s tests -p 'test_nexus_termux.py' -v
bash nexus-start.sh
```

O primeiro comando confirma Python/SQLite; o segundo executa testes sem fazer chamadas de rede; o terceiro abre o menu. Corre-o numa sessão interativa de Termux, não com `nohup` ou por pipe.

Uso manual do menu:

1. Atualiza uma cotação e insere `EUR/USD`, bid e ask. Exemplo fictício: `1.08500` e `1.08520`.
2. Cria uma posição `BUY` com stop abaixo da entrada e take-profit acima, ou `SELL` com a ordem invertida.
3. Consulta posição aberta; `4` mostra histórico; `5` fecha pelo bid/ask manual atual; `0` sai.

A cotação é manual e a monitorização só acontece quando atualizas o preço no painel. Não é trading automático nem feed de mercado. O programa apresenta saldo realizado e tem limitações descritas em [NEXUS-PAPER-TERMUX.md](NEXUS-PAPER-TERMUX.md); usa apenas valores de demonstração.

A base fica em `~/.nexus-trading/nexus.sqlite3`. Para criar uma cópia (substitui o destino se já existir; escolhe um nome novo para preservar cópias anteriores):

```bash
python nexus_backup.py "$HOME/.nexus-trading/nexus.sqlite3" "$HOME/nexus-backup.sqlite3"
```

## 3. Motor original: opção isolada com proot-distro

Recomendo experimentar o painel primeiro. Para testar o motor original sem instalar bibliotecas pesadas no Python nativo do Termux, pode-se tentar uma distribuição Linux em proot. É uma tentativa de compatibilidade, não uma validação; requer bastante espaço e rede. O proot não é uma máquina virtual completa e pode ter limitações de desempenho.

No Termux:

```bash
pkg install -y proot-distro
df -h "$HOME"
proot-distro install debian
proot-distro login debian
```

Dentro do Debian:

```bash
apt update
apt install -y python3 python3-venv python3-pip git build-essential libsqlite3-dev
python3 --version
python3 -m venv "$HOME/ta-venv"
. "$HOME/ta-venv/bin/activate"
git clone https://github.com/BUDA1999/NEXUS-Market-Intelligence.git
cd NEXUS-Market-Intelligence
python -m pip install --upgrade pip
python -m pip install .
```

Se a versão do Debian for inferior a Python 3.11, ou se `pip install .` falhar, para e guarda o erro completo sem chaves. Não mistures `pip install --no-deps` e pacotes do Termux ao acaso: isso pode deixar uma instalação incompleta ou incompatível. O painel NEXUS pode continuar a ser executado diretamente no Termux, separado do proot.

### Rota nativa opcional — avançada e não validada

É possível investigar pacotes nativos do Termux e depois instalar dependências uma a uma, mas não recomendo começar por compilar Pandas e dependências nativas num telefone com pouca memória. Os requisitos `pandas>=3.0.6`, `cryptography`, componentes LangChain/LangGraph e dependências transitivas podem não ter wheels Android compatíveis; o resultado depende das versões e do ambiente. Não há garantia de que a lista de pacotes ou os comandos de compilação funcionem em todas as versões do Termux. Faz backup e anota cada erro; não declares a rota funcional até importar módulos e executar testes no aparelho.

## 4. API de IA — só depois de instalar e testar o motor

O TradingAgents já tem suporte a vários fornecedores. Uma chave de API não instala dependências nem liga automaticamente o agente ao painel NEXUS. Guarda a chave apenas num `.env` local (já ignorado pelo `.gitignore`) e nunca a coloques em commits, capturas ou mensagens.

Só depois de `pip install .` terminar com sucesso, dentro do ambiente isolado:

```bash
cp .env.example .env
nano .env
```

Preenche apenas a variável do fornecedor escolhido, por exemplo `DEEPSEEK_API_KEY=...`, e seleciona o fornecedor/modelo conforme o README do motor original. Não partilhes o ficheiro `.env`. Confere que `.env` está ignorado antes de qualquer commit:

```bash
git check-ignore .env
```

A chamada de análise pode consumir quota/custos do fornecedor. O `nexus_api.py ... --check` só testa um endpoint de autenticação: não executa o grafo TradingAgents, não verifica uma cotação Forex e não cria integração ao painel.

Para primeira análise do motor, consulta a ajuda e os argumentos suportados pela versão instalada:

```bash
tradingagents --help
```

O uso de tickers Yahoo como `EURUSD=X` **não comprova** cotação Forex executável ou em tempo real. Não uses o motor para abrir operações; Forex, execução automática e integração NEXUS ainda não estão validados.


### OpenRouter: configuração persistente no Debian/proot

Depois de instalar o motor no Debian e atualizar/clonar a versão que contém os scripts:

```bash
cd ~/NEXUS-Market-Intelligence
bash scripts/setup-openrouter.sh
```

O instalador pede a chave com entrada oculta e guarda-a fora do clone em `~/.config/nexus/openrouter.env` (permissão 600; diretório 700). Guarda fornecedor, modelos gratuitos escolhidos e idioma num `models.env` separado; apenas essas configurações sem segredo são carregadas em novas sessões do Debian via `.bashrc`. A chave **não** é carregada em cada shell nem impressa: o launcher abaixo lê o segredo apenas ao iniciar o motor. O instalador não faz chamada de modelo nem análise.

Para arrancar o motor com a configuração guardada:

```bash
cd ~/NEXUS-Market-Intelligence
bash scripts/nexus-engine-start.sh
```

O launcher inicia o CLI interativo TradingAgents; usar o motor pode consumir créditos conforme o fornecedor/modelo e os limites da chave. Isto não liga o grafo ao painel `nexus_termux.py`, não fornece cotação Forex validada e não envia ordens. O painel Paper inicia à parte no Termux com `bash nexus-start.sh`.

Para apagar a configuração persistente, remove `~/.config/nexus/openrouter.env` e `~/.config/nexus/models.env`, e retira o bloco `NEXUS_MODELS_ENV_START` ... `NEXUS_MODELS_ENV_END` de `~/.bashrc`. Para revogar a chave, usa a página de gestão do OpenRouter. Nunca copies os ficheiros privados para o repositório nem partilhes o seu conteúdo.

## O que enviar se falhar

Envia o texto do erro e a saída de `python --version`, `uname -m`, `df -h "$HOME"` e o ponto em que falhou. Remove chaves, tokens, e-mail privado ou outros dados pessoais antes de partilhar. Distingue erro do painel NEXUS de erro de dependências do motor original.

## Instalador e diagnóstico em etapas

O instalador prepara apenas o básico para o painel paper, sem instalar o motor ou modificar `.env`. Pré-visualiza e depois executa:

```bash
bash install-termux.sh --dry-run
bash install-termux.sh
python -m cli.doctor --profile paper
python -m cli.doctor --profile engine
```

O doctor usa apenas a biblioteca padrão. O perfil `engine` procura as dependências, mas encontrá-las não prova que suas versões são compatíveis ou que funcionam no Android.

**Instalação nativa do motor não foi validada e está bloqueada no script.** `constraints-termux.txt` é experimental: a faixa `pandas<3` conflita com `pandas>=3.0.6` no `pyproject.toml`. Não força uma instalação com `--no-deps` nem substitui as dependências sem resolver essa incompatibilidade. A alternativa proot continua por testar no dispositivo.
