"""Shared OpenAI client construction with verified Windows TLS roots."""

from __future__ import annotations

import os
import ssl
import sys
from typing import Optional

import httpx
from openai import OpenAI


def build_ssl_context() -> ssl.SSLContext:
    """Build a verified context compatible with Python 3.13 on Windows.

    httpx's bundled CA set can omit locally managed Windows roots. Python 3.13
    also enables strict extension validation that rejects some certificates
    already trusted by Windows. Certificate and hostname verification remain
    enabled; only that strict extension flag is relaxed on Windows.
    """
    context = ssl.create_default_context()
    if sys.platform.startswith("win") and hasattr(ssl, "enum_certificates"):
        for certificate, encoding, _trust in ssl.enum_certificates("ROOT"):
            if encoding != "x509_asn":
                continue
            try:
                context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(certificate))
            except ssl.SSLError:
                continue
        strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
        if strict_flag:
            context.verify_flags &= ~strict_flag
    return context


def build_openai_client(api_key: Optional[str] = None, timeout: float = 60.0) -> OpenAI:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    transport = httpx.Client(verify=build_ssl_context(), timeout=timeout)
    return OpenAI(api_key=key, http_client=transport)
