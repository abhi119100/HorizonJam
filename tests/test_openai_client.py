import ssl
import unittest
from unittest.mock import patch

from utils.openai_client import build_openai_client, build_ssl_context


class OpenAIClientTests(unittest.TestCase):
    def test_ssl_context_keeps_certificate_and_hostname_verification(self):
        context = build_ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
        if strict_flag:
            self.assertFalse(context.verify_flags & strict_flag)

    @patch("utils.openai_client.OpenAI")
    def test_client_factory_requires_key_and_supplies_verified_transport(self, openai):
        sentinel = object()
        openai.return_value = sentinel
        result = build_openai_client("test-key", timeout=12.0)
        self.assertIs(result, sentinel)
        kwargs = openai.call_args.kwargs
        self.assertEqual(kwargs["api_key"], "test-key")
        self.assertIsNotNone(kwargs["http_client"])
        kwargs["http_client"].close()


if __name__ == "__main__":
    unittest.main()
