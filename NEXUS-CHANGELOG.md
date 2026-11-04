# NEXUS Changelog

Alterações à personalização NEXUS; o changelog original do TradingAgents permanece separado.

## 2026-11-04 — validação e teste opcional de API

- Adicionado `nexus_safety.py`, a partir do patch de auditoria enviado: valida bid/ask, origem, horário, frescura e risco linear genérico. Testes adicionais rejeitam timestamps futuros e quantidades não finitas.
- Adicionado `nexus_api.py`: teste de conectividade opcional para DeepSeek, Google Gemini e OpenRouter com chave por ambiente, sem imprimir segredos ou seguir redirecionamentos. O teste não inicia agentes e não cria ordens.
- `NEXUS-API.md` documenta configuração temporária, limitações e ausência de integração ao painel.
- Testes locais: 14 casos em `python -m unittest test_nexus_safety test_nexus_api -v` para segurança e API com rede simulada; 13 testes NEXUS pré-existentes também passaram.
- Limitações: os controlos de segurança ainda não foram ligados ao painel. O cálculo é genérico, não Forex/lote real. As APIs não foram testadas com chaves reais. Android/Termux não foi validado. Sem corretora, sem ordens reais.
