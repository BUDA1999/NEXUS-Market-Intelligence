# TRADING AGENTS NEXUS — Estado e Termux

TradingAgents é o projeto original da Tauric Research. NEXUS é uma personalização em desenvolvimento. O repositório contém o motor original, o banner JD NEXUS e o diagnóstico. A presença de ficheiros não comprova instalação ou funcionamento no Android.

## Diagnóstico primeiro

O projeto declara Python 3.11 ou superior. Num clone atualizado deste repositório, executar `bash nexus-diagnostico.sh`. O teste não instala nada e não expõe as chaves. A versão do Python, RAM, espaço e dependências precisam de ser avaliadas no próprio telefone. Se houver falha, partilhe a mensagem sem segredos.

A compatibilidade com Termux/Android, incluindo bibliotecas com código nativo, ainda não foi validada. Não instalar o pacote completo nem ferramentas de compilação antes do diagnóstico e da revisão das dependências. O banner é visual e não inicia agentes.

## Fornecedores de IA

O motor prevê vários fornecedores, incluindo DeepSeek, Google e OpenRouter. Um fornecedor configurado poderá ser suficiente para testes iniciais dos agentes; uma chave DeepSeek válida requer conta, saldo/limites e configuração adequados. O funcionamento concreto ainda precisa de ser testado. Gemini e OpenRouter são opcionais para começar. Outras fontes de dados ou funcionalidades também podem exigir chaves próprias. Não inserir chaves neste repositório público, em capturas, logs ou conversas.

## Forex e ouro

O TradingAgents original é orientado a ações, não é uma plataforma Forex pronta. Os analistas de fundamentos de ações não são apropriados para Forex. Uma experiência com market e news e símbolos Yahoo como EURUSD=X e XAUUSD=X depende de verificar suporte, disponibilidade e qualidade reais no fluxo original. Dados Yahoo podem ter atraso e não representam necessariamente preços executáveis ou spread de corretora. Não assumir que funcionam ou são em tempo real. Dados desatualizados devem impedir uma decisão simulada.

## Camada NEXUS pendente

A camada de mercado Forex, dashboard, controlo de risco e execução automática simulada NEXUS não está instalada neste repositório. Antes de integrar qualquer pacote externo, inspecionar código, dependências e segurança; testar sem ligar a conta real. O TradingAgents pode conter recursos próprios de simulação, mas isso não valida o uso para Forex nem substitui a camada NEXUS.

## Etapas seguintes

1. Diagnosticar o Realme C33 com Termux.
2. Validar e instalar dependências viáveis sem comprometer a instalação existente.
3. Configurar e testar um fornecedor de IA sem divulgar credenciais.
4. Rever e integrar a camada NEXUS separadamente do motor original.
5. Validar uma fonte adequada para EUR/USD e XAU/USD, incluindo atraso e spread.
6. Desenvolver/testar gestão de risco, rejeição por dados inválidos, stop de emergência e execução exclusivamente simulada.
7. Testar em conjunto no Android, incluindo falhas de rede e reinícios.

A conta real, a corretora XM e qualquer execução com dinheiro real ficam fora desta fase e exigem decisão e integração separadas. A simulação não garante resultados reais.
