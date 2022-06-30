import os
import six
import pycurl

from requests.adapters import DEFAULT_CA_BUNDLE_PATH


class CURLRequest(object):
    """Representation of a request to be made using CURL."""

    def __init__(self, request, timeout=None, verify=None, cert=None):
        """Initializes a CURL request from a given prepared request

        Args:
            request (PreparedRequest): the prepared request comming from `requests` library.
            timeout (float, optional): Defaults to None. How many seconds to
                wait for the server to send data before giving up, as a float,
                or a `(connect timeout, read timeout)` tuple.
            verify (bool, optional): Defaults to True. Either a boolean, in
                which case it controls whether we verify the server's TLS
                certificate, or a string, in which case it must be a path
                to a CA bundle to use.
            cert (str, optional): Defaults to None. Any user-provided SSL
                certificate to be trusted.
        """
        self._CIPHER_LIST = None
        self._request = request
        self._timeout = timeout
        self._cert = cert
        self._verify = verify
        self._curl_options = None
        self._body_stream = None

    @property
    def use_chunked_upload(self):
        return hasattr(self._request.body, "read")

    @property
    def request(self):
        return self._request

    @property
    def options(self):
        if self._curl_options is None:
            self._curl_options = self._build_curl_options()

        return self._curl_options

    @property
    def set_cipher(self):
        CIPHER_LIST = [
            'TLS_AES_128_GCM_SHA256', 'TLS_AES_256_GCM_SHA384', 'TLS_CHACHA20_POLY1305_SHA256',
            'ECDHE-ECDSA-AES128-GCM-SHA256', 'ECDHE-RSA-AES128-GCM-SHA256', 'ECDHE-ECDSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES256-GCM-SHA384', 'ECDHE-ECDSA-CHACHA20-POLY1305', 'ECDHE-RSA-CHACHA20-POLY1305',
            'ECDHE-RSA-AES128-SHA', 'ECDHE-RSA-AES256-SHA', 'AES128-GCM-SHA256', 'AES256-GCM-SHA384',
            'AES128-SHA,AES256-SHA'
        ]
        if self._CIPHER_LIST is None:
            self._CIPHER_LIST = ','.join(CIPHER_LIST)
        return self._CIPHER_LIST

    def _build_curl_options(self):
        options = {
            pycurl.URL: self._request.url,
            pycurl.SSL_CIPHER_LIST: self.set_cipher,
            pycurl.HTTP_VERSION: pycurl.CURL_HTTP_VERSION_2_0,
            pycurl.SSLVERSION: pycurl.SSLVERSION_TLSv1_2,
            pycurl.SSL_ENABLE_ALPS: 1,
            pycurl.SSL_CERT_COMPRESSION: "brotli",
            pycurl.HTTP2_PSEUDO_HEADERS_ORDER: "masp",
            pycurl.SSL_ENABLE_NPN: 0
        }

        options.update(self.build_headers_option())
        options.update(self.build_body_options())
        # HTTP method must come after the body options since
        # we may need to overwrite the method being used, for example
        # when using post but uploading binary data
        options.update(self.build_http_method_options())
        options.update(self.build_timeout_options())
        options.update(self.build_ca_options())
        options.update(self.build_cert_options())

        return options

    def build_headers_option(self):
        """Returns a dict with the pycurl option for the headers."""
        req_headers = self._request.headers.copy()

        headers = [
            "{name}: {value}".format(name=name, value=value)
            for name, value in six.iteritems(req_headers)
        ]

        return {pycurl.HTTPHEADER: headers}

    def build_http_method_options(self):
        method = self._request.method
        method = method.upper() if method else "GET"

        if method == "GET":
            return {}
        else:
            return {pycurl.CUSTOMREQUEST: method}

    def build_body_options(self):
        if self._request.method == "HEAD":
            # Body is not allowed for HEAD
            return {pycurl.NOBODY: True}

        elif self._request.body:
            content_type = self._request.headers.get("Content-Type", "").lower()
            is_encoded_form = content_type == "application/x-www-form-urlencoded"

            if is_encoded_form:
                return {pycurl.POSTFIELDS: self._request.body}
            else:
                if hasattr(self._request.body, "read"):
                    self._body_stream = self._request.body
                else:
                    self._body_stream = six.BytesIO(
                        six.ensure_binary(self._request.body)
                    )

                return {
                    pycurl.UPLOAD: True,
                    pycurl.READFUNCTION: self._body_stream.read,
                }

        else:
            return {}

    def build_timeout_options(self):
        """Returns the curl timeout options."""
        if isinstance(self._timeout, (tuple, list)):
            conn_timeout, read_timeout = self._timeout
            total_timeout = conn_timeout + read_timeout
            return {
                pycurl.TIMEOUT_MS: int(1000 * total_timeout),
                pycurl.CONNECTTIMEOUT_MS: int(1000 * conn_timeout),
            }
        elif self._timeout:
            return {pycurl.TIMEOUT_MS: int(1000 * self._timeout)}
        else:
            return {}

    def build_ca_options(self):
        """Configures the CA of this curl request."""
        if self._verify:
            ca_value = (
                self._verify
                if isinstance(self._verify, six.string_types)
                else DEFAULT_CA_BUNDLE_PATH
            )

            # Requests allows the verify parameter to be a file or a directory. This requires
            # a different CURL option for each case
            ca_opt = pycurl.CAPATH if os.path.isdir(ca_value) else pycurl.CAINFO

            return {
                pycurl.SSL_VERIFYHOST: 2,
                pycurl.SSL_VERIFYPEER: 2,
                ca_opt: ca_value,
            }
        else:
            return {
                pycurl.SSL_VERIFYHOST: 0,
                pycurl.SSL_VERIFYPEER: 0,
            }

    def build_cert_options(self):
        """Configures the SSL certificate of this curl request."""

        if self._cert:
            if isinstance(self._cert, six.string_types):
                cert_path = self._cert
                return {pycurl.SSLCERT: cert_path}
            else:
                cert_path, key_path = self._cert
                return {
                    pycurl.SSLCERT: cert_path,
                    pycurl.SSLKEY: key_path,
                }
        else:
            return {}
