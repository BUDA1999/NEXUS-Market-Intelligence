# NEXUS — verificação opcional de API de IA

O TradingAgents original já conhece fornecedores DeepSeek, Google e OpenRouter; ver `.env.example` e o guia original. O painel paper NEXUS ainda **não está integrado** aos agentes originais. `nexus_api.py` é um teste de conectividade de autenticação separado; não inicia agentes, não envia ordens, não valida dados de mercado, não garante crédito ou compatibilidade do modelo, e não foi validado no Termux. Pode consumir quota do fornecedor. Funciona com Python e biblioteca padrão.

## Testar uma chave temporariamente no Termux

Obtenha a chave no fornecedor e não a envie no chat, em capturas ou no GitHub. Dentro de uma sessão Bash, estando no diretório do repositório:

```bash
read -rsp 'Cole a chave DeepSeek (não aparece no ecrã): ' DEEPSEEK_API_KEY; echo
export DEEPSEEK_API_KEY
python nexus_api.py deepseek --check
unset DEEPSEEK_API_KEY
```

Para Gemini, use `GOOGLE_API_KEY` e `python nexus_api.py google --check`. Para OpenRouter, `OPENROUTER_API_KEY` e `python nexus_api.py openrouter --check`. As chaves permanecem apenas nessa sessão e são removidas com `unset` ou ao fechar a sessão. Um HTTP 200 só demonstra que aquele pedido recebeu uma resposta bem-sucedida. Alguns endpoints podem autorizar respostas públicas sem provar que um modelo pode ser usado: faça uma análise real apenas depois de validar dependências, modelo, cotação e riscos. O teste de rede acontece apenas com `--check`, usa URLs fixos, não segue redirecionamentos e não imprime a chave nem o corpo da resposta.

`nexus_safety.py` é aditivo e os seus controlos não estão ainda ligados ao painel existente. Risco linear genérico não substitui cálculo específico de contrato, custos ou conversão Forex. O projeto mantém-se estritamente em Paper Trading.
