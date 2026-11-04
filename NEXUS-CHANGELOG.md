# NEXUS Changelog

Alterações à personalização NEXUS; o changelog original do TradingAgents permanece separado.

## 2026-11-04 — guia de instalação Termux por camadas

- Adicionado `TERMUX-INSTALACAO.md`, com instalação/diagnóstico do painel primeiro e rota separada para tentar o motor original em proot-distro.
- Incluídas instruções cautelosas de dependências, espaço, backup, chaves locais ignoradas pelo Git e recolha de erros sem segredos.
- Conferido `pyproject.toml`: motor declara Python >=3.11 e pandas >=3.0.6. Não afirmamos incompatibilidade definitiva com Android sem testar pacotes.
- Issues e pull requests públicos verificados: zero abertos.
- Validação: revisão documental e conferência dos comandos com os ficheiros públicos; nenhuma execução foi feita no Termux.
- Limitações: não testado no Realme/Android; proot e instalação nativa continuam por validar; painel não tem agentes ou cotações Forex ao vivo.

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
