import io
import os
import unittest
import urllib.error
from unittest.mock import patch
from nexus_api import PROVIDERS, ProbeError, check_provider

class Response:
    status=200
    def __init__(self, content=b'{}'): self.content=content
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self, limit): return self.content[:limit]

class ApiTest(unittest.TestCase):
    def test_all_provider_urls_and_header(self):
        for name, config in PROVIDERS.items():
            with self.subTest(name=name), patch.dict(os.environ, {config.key_env:'fake-key'}, clear=True):
                def opener(req, timeout):
                    self.assertEqual(req.full_url,config.endpoint)
                    self.assertEqual(req.get_header(config.key_header.capitalize()),config.prefix+'fake-key')
                    self.assertEqual(timeout,15)
                    return Response()
                self.assertIn('HTTP 200',check_provider(name,opener=opener))
    def test_missing_key_never_calls_network(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ProbeError): check_provider('deepseek',opener=lambda *a,**k: self.fail('network'))
    def test_http_error_body_not_exposed(self):
        def fail(req,timeout): raise urllib.error.HTTPError(req.full_url,401,'bad',{},io.BytesIO(b'secret'))
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'fake-key'},clear=True):
            with self.assertRaises(ProbeError) as error: check_provider('deepseek',opener=fail)
            self.assertNotIn('fake-key',str(error.exception)); self.assertIn('401',str(error.exception))
    def test_invalid_response(self):
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'fake'},clear=True):
            with self.assertRaises(ProbeError): check_provider('deepseek',opener=lambda *a,**k:Response(b'broken'))
    def test_no_redirects_in_default_opener(self):
        import urllib.request
        from unittest.mock import MagicMock
        result = MagicMock(); result.open.return_value=Response()
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'fake'},clear=True), patch('urllib.request.build_opener',return_value=result) as factory:
            check_provider('deepseek')
            handler=factory.call_args.args[0]
            self.assertIsNone(handler.redirect_request(None,None,302,None,None,'https://other.example'))

if __name__=='__main__': unittest.main()
