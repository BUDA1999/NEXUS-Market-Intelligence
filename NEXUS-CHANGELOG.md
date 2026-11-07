# NEXUS Changelog

Alterações à personalização NEXUS; o changelog original do TradingAgents permanece separado.

## 2026-11-07 — kill switch persistente de novas posições Paper

- Adicionado controlo explícito de ativação `HALT` e retoma `RESUME` via opção `k`, guardado em `settings.paper_halted` sem migração nem perda dos dados SQLite existentes.
- A criação de novas posições verifica o estado persistido; o estado corrompido/inesperado falha fechado. O kill switch bloqueia só novas entradas: posições abertas continuam geríveis/fecháveis e o limite diário de perda segue ativo.
- O dashboard e o resumo identificam o estado; opções existentes `0–9`, `a`, `b`, `r`, `h` permanecem no menu. Sem broker, operações reais, automação ou feed.
- Testes em Linux Python 3.13: 20 testes do painel passaram, incluindo reinício, reativação, dado inválido e gestão de posição preexistente. Termux/Android não testado.

## 2026-11-06 — moldura compacta no estilo JD NEXUS

- Ajustado `nexus_ui.py` para uma moldura terminal com logótipo JD em ASCII, ♓ Pisces, dois peixes, slogan, secções do exemplo e menu compacto em duas colunas em terminais largos; em 24–45 colunas quebra para uma coluna sem overflow.
- Mostra Paper/local, cotações manuais e ordens reais desativadas; evita “online/real” e exibe quando cada cotação está ausente/antiga. Removida variação fictícia; agentes ficam DISABLED.
- Compatibilidade preservada: números `0–9` conservam as ações; opções extra permanecem visíveis. Nenhuma dependência ou alteração de trading.
- Testes: 31 testes em Linux passaram, incluindo larguras 24, 40, 42, 45 e 60; modo de cores sem TTY e execução Paper. Android/Termux não validado.

## 2026-11-06 — redesenho responsivo do terminal JD NEXUS

- Substituído o banner alto no fluxo do painel por cabeçalho compacto JD NEXUS / ♓ PISCES EDITION / THINK BEYOND THE MARKET e identidade visual de peixes; atualizado `nexus-start.sh` para remover o banner shell duplicado/limpar e não sobrepor o dashboard.
- Nova apresentação por secções: estado, mercado EUR/USD e XAU/USD, conta Paper, dez agentes e menu de operações. Estados de cotações sem feed, agentes não ligados, modelo desconhecido e broker ausente são explicitamente honestos; sem simular variações, atividade, preços ou conectividade.
- Criado `nexus_ui.py` como camada de apresentação independente do motor; largura obtida dinamicamente, quebra sem dividir palavras, cores ANSI só em TTY e selecionado indicado com `>`. Sem animação, dependências novas, redraw contínuo ou alteração da lógica Paper.
- Os números existentes `0`–`9` mantêm as suas ações; `a`, `b`, `h`, `r` continuam disponíveis. Menu mostra apenas as ações que existem, não exibe ordem real ou análise de IA como funcional.
- Testes locais: 30 testes de status, UI e regressão Paper passaram em Linux, incluindo largura 24/40/45 colunas, execução honesta dos estados, seleção visual e preservação das funções existentes. `py_compile` executado. Não validado no Termux/aparelho.

## 2026-11-06 — auditoria e estado local no painel

- Adicionado `NEXUS-AUDITORIA-2026-11-06.md` com estado real, bloqueios, testes e plano por prioridades; sem declarar produção.
- Adicionado `nexus_status.py` e opção `a` no painel: dependências detetadas, presença de chaves apenas no processo sem exibir valores, integridade SQLite em leitura e estados honestos da IA/mercado/automação/broker. Não faz chamadas de rede nem inicia agentes.
- Testes: 21 testes do painel e status passaram em Linux; suíte upstream completa não foi concluída e não foi validada no Android nesta sessão. Mantidos os restantes comandos do menu e Paper Trading.

## 2026-11-05 — opções do painel Paper

- Mantidos sem alteração de significado os comandos numéricos `0`–`5`; adicionados `6` resumo, `7` detalhes, `8` limites de risco, `9` exportação CSV/TXT, `b` backup SQLite, `r` restauro confirmado e `h` ajuda.
- Resumo e detalhes são somente leitura. Acrescentados limites configuráveis com tetos fixos; as alterações são validadas por inteiro e persistidas.
- Exportação gera CSV/TXT. Restauro valida integridade e esquema, faz automaticamente uma cópia pré-restauro e depois usa a API de cópia SQLite para restituir a base ativa. A confirmação exige digitar `RESTORE`.
- Testes: `python -m unittest discover -s tests -v` — 17 testes do painel passaram fora do Termux, incluindo preservação dos números do menu e ciclo de backup/restauro.
- Limitações: continua Paper Trading com cotações manuais; P&L não realizado é estimativa, não equity de corretora. Código testado fora do Android, não no Realme/Termux.

## 2026-11-05 — identidade JD Pisces no painel

- Adicionado `jd_banner.py` com moldura azul-neon, peixes azul/dourado, iniciais JD, símbolo ♓ PEIXES e slogan STAY LIVE.
- Integrado uma vez no arranque do menu em `nexus_termux.py`; o menu, posições, cotações manuais e persistência SQLite foram preservados.
- Adicionado teste de apresentação que confirma os elementos visuais e a preservação dos dados de menu.
- Testes locais: `python -m unittest discover -s tests -v` — 8 testes do painel passaram fora do Termux.
- Limitação: o visual foi testado em Linux, não no Realme/Termux; cores dependem do terminal.

## 2026-11-04 — instalação Termux em etapas e doctor sem dependências

- Adicionado `cli/doctor.py`, diagnóstico com Python standard library que pode correr quando dependências do motor estão ausentes; suporta perfis `paper`/`engine` e JSON, sem imprimir valores de chaves.
- Adicionado `install-termux.sh`: por defeito prepara apenas o básico para o painel; `--install-engine` está bloqueado enquanto constraints conflitam com o requisito original. `--dry-run` e `--skip-system` disponíveis.
- Adicionado `constraints-termux.txt` apenas para rota nativa experimental; a faixa Pandas não satisfaz o requisito upstream `pandas>=3.0.6`, portanto não representa instalação suportada do motor.
- Atualizado `TERMUX-INSTALACAO.md` com instruções do instalador e bloqueio explícito da instalação incompatível.
- Comentários/issues/PRs públicos consultados: nenhum aberto.
- Testes locais: `python -m unittest discover -s tests -v` (7 testes novos e backup incluído); `bash -n install-termux.sh`; `python -m py_compile cli/doctor.py nexus_backup.py`. Ambiente Linux x86_64, não Termux.
- Limitações: instalação nativa/proot não validada; nenhuma integração IA/Forex executada.

## 2026-11-04 — cópia de segurança SQLite

- Adicionado `nexus_backup.py`, utilitário de linha de comando para criar snapshot consistente SQLite sem afetar o banco ativo; cria diretório de destino, recusa o próprio arquivo ativo e aceita caminho de destino separado.
- Testes: `python -m unittest discover -s tests -p 'test_nexus_termux.py' -v` — 9 testes passaram; `python -m unittest test_nexus_safety test_nexus_api -v` — 14 passaram; teste isolado do utilitário `test_nexus_backup_local` — 3 passaram.
- Limitações: sem rotação, cifragem ou restauração automática; testes rodaram neste ambiente, não no Android/Termux. O protótipo continua manual e paper-only; sem broker nem dados ao vivo.

## Feedback revisado — 2026-11-04

- Não havia issues nem pull requests listados pela API pública do GitHub.
- Considerado o relatório de auditoria local de 2026-11-03, que recomenda estabilizar persistência e validar cópias antes de integrações e automação; mantidas a separação do motor TradingAgents e as limitações paper-only.

## 2026-11-04 — novo nome do projeto

- Repositório renomeado para NEXUS Market Intelligence; painel atualizado para mostrar o novo nome.
- Preservada a atribuição ao projeto original TradingAgents da Tauric Research.
- Testes: `python -m unittest discover -s tests -p test_nexus_termux.py -v` (7 testes fora do Android).
- Compatibilidade Termux ainda não validada no dispositivo.

## 2026-11-04 — validação e teste opcional de API

- Adicionado `nexus_safety.py`: valida bid/ask, origem, horário, frescura e risco linear genérico; testes rejeitam timestamps futuros e quantidades não finitas.
- Adicionado `nexus_api.py`: teste de conectividade opcional para DeepSeek, Google Gemini e OpenRouter com chave por ambiente, sem imprimir segredos ou seguir redirecionamentos. O teste não inicia agentes nem cria ordens.
- `NEXUS-API.md` documenta configuração temporária, limitações e ausência de integração ao painel.
- Testes locais: 14 casos para segurança e API com rede simulada; 13 testes NEXUS pré-existentes também passaram.
- Limitações: controlos de segurança ainda não estão ligados ao painel. Cálculo genérico, não Forex/lote real. APIs não testadas com chaves reais. Android/Termux não validado. Sem corretora, sem ordens reais.
