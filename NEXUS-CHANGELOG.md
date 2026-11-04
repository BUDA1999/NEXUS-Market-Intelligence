# NEXUS Changelog

Alterações à personalização NEXUS; o changelog original do TradingAgents permanece separado.

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
