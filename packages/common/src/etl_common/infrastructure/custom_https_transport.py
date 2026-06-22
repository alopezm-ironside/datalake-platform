import http
import ssl
import xmlrpc.client


class CustomHTTPSTransport(xmlrpc.client.SafeTransport):
    def __init__(self, use_https=True, check_hostname=False, verify_ssl=False):
        super().__init__()
        self.use_https = use_https
        self.check_hostname = check_hostname
        self.verify_ssl = verify_ssl
        self._timeout = 300

    def make_connection(self, host):
        if not self.verify_ssl:
            context = ssl._create_unverified_context()
            context.check_hostname = self.check_hostname
            context.verify_mode = ssl.CERT_NONE
            return http.client.HTTPSConnection(host, context=context, timeout=self._timeout)
        return super().make_connection(host)
