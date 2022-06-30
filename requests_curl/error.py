import pycurl
import re

from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    SSLError,
    ProxyError,
)

_PYCURL_SSL_ERRORS = {
    pycurl.E_SSL_CACERT,
    pycurl.E_SSL_CACERT_BADFILE,
    pycurl.E_SSL_CERTPROBLEM,
    pycurl.E_SSL_CIPHER,
    pycurl.E_SSL_CONNECT_ERROR,
    pycurl.E_SSL_CRL_BADFILE,
    pycurl.E_SSL_ENGINE_INITFAILED,
    pycurl.E_SSL_ENGINE_NOTFOUND,
    pycurl.E_SSL_ENGINE_SETFAILED,
    pycurl.E_SSL_INVALIDCERTSTATUS,
    pycurl.E_SSL_ISSUER_ERROR,
    pycurl.E_SSL_PEER_CERTIFICATE,
    pycurl.E_SSL_PINNEDPUBKEYNOTMATCH,
    pycurl.E_SSL_SHUTDOWN_FAILED,
}


_PYCURL_TIMEOUT_ERRORS = {pycurl.E_OPERATION_TIMEOUTED, pycurl.E_OPERATION_TIMEDOUT}


_PROXY_AUTH_ERR_PATTERN = re.compile(
    r"Received HTTP code \d{3} from proxy after CONNECT"
)


def _to_ssl_error(error_code, error_msg):
    if error_code in _PYCURL_SSL_ERRORS:
        return SSLError


def _to_proxy_error(error_code, error_msg):
    is_proxy_error = (
        error_code == pycurl.E_COULDNT_RESOLVE_PROXY
        or _PROXY_AUTH_ERR_PATTERN.match(error_msg) is not None
    )

    if is_proxy_error:
        return ProxyError


def _to_timeout_error(error_code, error_msg):
    if error_code in _PYCURL_TIMEOUT_ERRORS:
        if error_msg.startswith("Connection timed out"):
            return ConnectTimeout
        else:
            return ReadTimeout


_ERROR_TRANSLATE_FUNCS = (_to_ssl_error, _to_proxy_error, _to_timeout_error)


def translate_curl_exception(curl_exception):
    """This function will make the best effort to translate a given PyCURL error
    to a requests exception.

    Args:
        curl_exception (pycurl.error): PyCURL error to be translated.

    Returns:
        requests.exceptions.RequestException: the requests exception that
            matches to the CURL error.
    """

    error_code, error_msg = curl_exception.args
    default_error = ConnectionError

    for translate_func in _ERROR_TRANSLATE_FUNCS:
        requests_error = translate_func(error_code, error_msg)
        if requests_error is not None:
            return requests_error

    return default_error
