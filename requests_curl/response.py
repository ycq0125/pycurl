import io
import six

from http.client import parse_headers
from requests import Response as RequestResponse
from requests.utils import get_encoding_from_headers
from requests.structures import CaseInsensitiveDict
from requests.cookies import extract_cookies_to_jar
from urllib3.response import HTTPResponse as URLLib3Rresponse


class _MockHTTPResponse:
    """Mocks HTTPResponse class to be used as original response when
    building the urllib3 response for later parsing cookies."""

    def __init__(self, headers_fp):
        headers_fp.seek(0)
        self.msg = parse_headers(headers_fp)

    def isclosed(self):
        return True


class CURLResponse(object):
    """This class represents a CURL response"""

    def __init__(self, curl_request, initial_http_code=200):
        """Initializes a new response object.

        Args:
            curl_request (CURLRequest): the request that originated this response.
        """

        self.curl_request = curl_request
        self.request = curl_request.request
        self.headers = dict()
        self.body = six.BytesIO()
        self.reason = None
        self.http_code = initial_http_code
        self._headers_buff = io.BytesIO(b"")

    def to_requests_response(self):
        """Returns an instance of `requests.Response` based on this response.

        Returns:
            request.Response: the generated response.
        """

        # Make sure that body is at position 0 before returning
        self.body.seek(0)

        urllib3_response = URLLib3Rresponse(
            body=self.body,
            headers=self.headers,
            status=self.http_code,
            request_method=self.request.method,
            reason=self.reason,
            preload_content=False,
            original_response=_MockHTTPResponse(self._headers_buff),
        )

        response = RequestResponse()
        response.request = self.request
        response.raw = urllib3_response
        response.status_code = self.http_code
        response.reason = self.reason
        response.headers = CaseInsensitiveDict(response.raw.headers)
        response.encoding = get_encoding_from_headers(response.headers)

        extract_cookies_to_jar(response.cookies, self.request, urllib3_response)

        if isinstance(self.request.url, six.binary_type):
            response.url = self.request.url.decode("utf-8")
        else:
            response.url = self.request.url

        return response

    def add_header_from_raw_line(self, raw_header_line):
        """This method is to be used as a callback to configure pycurl.HEADERFUNCTION
        option, which parses each line of the response headers.

        The line must an array of bytes, encoded in iso-8859-1, representing the line.

        Args:
            raw_header_line: a line of the headers section, as bytes.
        """

        # HTTP standard specifies that headers are encoded in iso-8859-1.
        header_line = raw_header_line.decode("iso-8859-1")

        # Header lines include the first status line (HTTP/1.x ...).
        # We are going to ignore all lines that don't have a colon in them.
        # This will botch headers that are split on multiple lines...
        if ":" not in header_line:
            return

        # Save the header line for later parsing cookies
        self._headers_buff.write(raw_header_line)

        name, value = header_line.split(":", 1)
        self.headers[name.strip()] = value.strip()

    def add_headers_from_raw_lines(self, raw_header_lines):
        """This method parses and adds all headers defined by the iterable of raw header lines.

        Each line is a byte array encoded in iso-8859-1, representing a line string.

        Args:
            raw_header_lines: an iterable of raw lines to be added to the respponse.
        """
        for raw_header_line in raw_header_lines:
            self.add_header_from_raw_line(raw_header_line)
