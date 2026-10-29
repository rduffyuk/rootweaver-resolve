"""Fixed HTTPS-only bounded Token Factory POST, no redirects or retries."""

import http.client
import json
import ssl
from time import monotonic

from rootweaver_resolve.nebius import HOST, ProviderError


def post(method, path, body, key):
    # Fixed HTTPS destination, no redirect, proxy, retry or model-supplied endpoint.
    if method != "POST" or path != "/v1/chat/completions":
        raise ProviderError("endpoint_denied")
    connection = http.client.HTTPSConnection(
        HOST, timeout=360, context=ssl.create_default_context()
    )
    deadline = monotonic() + 360
    try:
        connection.request(
            method,
            path,
            body=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
            },
        )
        response = connection.getresponse()
        chunks = []
        size = 0
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError
            if connection.sock:
                connection.sock.settimeout(remaining)
            chunk = response.read1(8192)
            if not chunk:
                break
            size += len(chunk)
            if size > 1048576:
                raise ProviderError("response_size_exceeded")
            chunks.append(chunk)
        if response.status != 200:
            return response.status, {}
        text = b"".join(chunks).decode("utf-8")
        if key and key in text:
            raise ProviderError("credential_echo_blocked")
        return response.status, json.loads(text)
    except ProviderError:
        raise
    except ssl.SSLCertVerificationError:
        raise Stop("tls_verification_failed") from None
    except (TimeoutError, OSError, ValueError, http.client.HTTPException):
        raise ProviderError("transport_failed") from None
    finally:
        connection.close()
