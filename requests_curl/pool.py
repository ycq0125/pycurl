import pycurl

from six.moves import queue, range

from .response import CURLResponse, curl_http_versions


class PoolException(Exception):
    pass


class EmptyPool(PoolException):
    pass


class ClosedPool(PoolException):
    pass


class CURLHandlerPool(object):
    """Thread-safe connection pool for one host. Tries to emulate HTTPConnectionPool."""

    def __init__(self, curl_factory=pycurl.Curl, maxsize=1, **kwargs):
        self._block = kwargs.get("block", False)
        self._pool = queue.LifoQueue(maxsize)

        for _ in range(maxsize):
            handler = curl_factory()
            self._pool.put(handler, block=False)

    def send(self, curl_request):
        """Performs a CURL request of the given CURLRequest instance, and returns
        an appropiate response.

        Args:
            curl_request (CURLRequest): an instance of a given CURL request.

        Returns:
            CURLResponse: the response of the request.

        Raises:
            pycurl.error: if there is any error while performing the request.
            EmptyPool: if there are no more connections available to perform the request.
        """

        curl_handler = self.get_handler_from_pool()

        response = CURLResponse(curl_request)

        curl_options = curl_request.options
        curl_options.update(_get_curl_options_for_response(response))
        curl_options.update(self.get_additional_curl_options())
        for option, value in curl_options.items():
            curl_handler.setopt(option, value)

        curl_handler.perform()

        response.http_version = curl_http_versions.get(curl_handler.getinfo(pycurl.INFO_HTTP_VERSION))
        response.http_code = curl_handler.getinfo(pycurl.HTTP_CODE)

        self.put_handler_back(curl_handler)

        return response

    def get_additional_curl_options(self):
        return {}

    def get_handler_from_pool(self):
        """Get a CURL handler. Will return a pooled handler if one is available.

        Returns:
            pycurl.Curl: CURL handler, if available.

        Raises:
            EmptyPool: if the pool is empty and there are no more free handlers available.
        """

        try:
            curl_handler = self._pool.get(block=self._block)
            curl_handler.reset()

            return curl_handler

        except queue.Empty:
            raise EmptyPool(
                "Pool reached maximum size and no more connections are allowed."
            )

        except AttributeError:
            raise ClosedPool("Pool is no longer available")

    def put_handler_back(self, curl_handler):
        """Put a curl handler back into the pool.

        Args:
            curl_handler (pycurl.Curl:): the handler to put back into the pool.
        """
        try:
            self._pool.put(curl_handler, block=False)

        except AttributeError:
            pass  # Pool was closed

    def close(self):
        """Close all pooled connections and disable the pool."""
        # This is almost identical to the HTTPConnectionPool.close implementation

        if self._pool is None:
            return

        # Disable access to the pool
        old_pool, self._pool = self._pool, None

        try:
            while True:
                curl_handler = old_pool.get(block=False)
                curl_handler.close()

        except queue.Empty:
            pass  # Done.


class ProxyCURLHandlerPool(CURLHandlerPool):
    def __init__(self, proxy_url, maxsize=1, **kwargs):
        super(ProxyCURLHandlerPool, self).__init__(maxsize=maxsize, **kwargs)

        self._proxy_url = proxy_url

    def get_additional_curl_options(self):
        options = []
        if self._proxy_url.auth:
            options.append((pycurl.PROXYUSERPWD, self._proxy_url.auth))
            options.append((pycurl.PROXY, self._proxy_url.netloc))
        else:
            options.append((pycurl.PROXY, self._proxy_url.netloc))
        return options

    @property
    def proxy_url(self):
        return self._proxy_url


def _get_curl_options_for_response(response):
    return {
        pycurl.HEADERFUNCTION: response.add_header_from_raw_line,
        pycurl.WRITEFUNCTION: response.body.write,
    }
