#!/usr/bin/env python3
"""Optional provider authentication preflight; no trading, storage, model calls or orders."""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

@dataclass(frozen=True)
class Provider:
    key_env: str
    endpoint: str
    key_header: str
    prefix: str = ""

PROVIDERS = {
    "deepseek": Provider("DEEPSEEK_API_KEY", "https://api.deepseek.com/models", "Authorization", "Bearer "),
    "google": Provider("GOOGLE_API_KEY", "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1", "x-goog-api-key"),
    "openrouter": Provider("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/key", "Authorization", "Bearer "),
}

class ProbeError(Exception):
    pass

def check_provider(provider: str, timeout: int = 15, opener=None) -> str:
    """Opt-in live request to fixed provider URL; do not print keys or response bodies."""
    if provider not in PROVIDERS:
        raise ProbeError("Fornecedor desconhecido")
    config = PROVIDERS[provider]
    key = os.environ.get(config.key_env, "").strip()
    if not key:
        raise ProbeError(f"Falta a variável {config.key_env} nesta sessão")
    if any(c in key for c in '\r\n'):
        raise ProbeError("Chave inválida: contém quebra de linha")
    req = urllib.request.Request(config.endpoint, headers={config.key_header: config.prefix + key, "Accept": "application/json"}, method="GET")
    # Do not follow redirects; never transmit authorization to a redirected host.
    if opener is None:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(NoRedirect()).open
    try:
        with opener(req, timeout=timeout) as response:
            if response.status != 200:
                raise ProbeError(f"Fornecedor devolveu HTTP {response.status}")
            body = response.read(1024 * 1024 + 1)
            if len(body) > 1024 * 1024:
                raise ProbeError("Resposta do fornecedor demasiado grande")
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ProbeError("Resposta inesperada do fornecedor")
    except urllib.error.HTTPError as exc:
        raise ProbeError(f"Fornecedor devolveu HTTP {exc.code}; verifica chave, permissões ou limites") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise ProbeError("Falha de rede ou resposta inválida; verifica ligação e configuração") from None
    return f"{provider}: resposta HTTP 200 recebida. Não confirma créditos, modelo ou execução dos agentes."

def main():
    parser = argparse.ArgumentParser(description="Teste opcional da chave de IA; não inicia agentes ou trading.")
    parser.add_argument("provider", choices=sorted(PROVIDERS))
    parser.add_argument("--check", action="store_true", help="autorizar um pedido de rede de verificação")
    args = parser.parse_args()
    if not args.check:
        parser.error("usa --check para autorizar a chamada à API")
    try:
        print(check_provider(args.provider))
    except ProbeError as exc:
        print(f"Verificação não concluída: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
