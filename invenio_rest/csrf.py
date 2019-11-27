import re
import string
# from urllib.parse import urlparse

from flask import g, request, session, current_app, abort

import jwt
from .errors import RESTCSRFError

REASON_NO_REFERER = "Referer checking failed - no Referer."
REASON_BAD_REFERER = "Referer checking failed - %s does not match any trusted origins."
REASON_NO_CSRF_COOKIE = "CSRF cookie not set."
REASON_BAD_TOKEN = "CSRF token missing or incorrect."
REASON_MALFORMED_REFERER = "Referer checking failed - Referer is malformed."
REASON_INSECURE_REFERER = "Referer checking failed - Referer is insecure while host is secure."

CSRF_SECRET_LENGTH = 32
CSRF_TOKEN_LENGTH = 2 * CSRF_SECRET_LENGTH
CSRF_ALLOWED_CHARS = string.ascii_letters + string.digits
CSRF_SESSION_KEY = '_csrftoken'
CSRF_COOKIE_NAME = '_csrftoken'
CSRF_USE_SESSIONS = True


def _get_new_csrf_token():
    encoded_jwt = jwt.encode(
        {'some': 'payload'},
        current_app.config.get('CSRF_SECRET', 'secret'),
        algorithm='HS256'
    )

    return encoded_jwt


def _decode_jwt(data):
    try:
        return jwt.decode(
            data,
            current_app.config.get('CSRF_SECRET', 'secret'),
            algorithms=['HS256'])
    except jwt.InvalidSignatureError:
        raise RESTCSRFError()


def rotate_token(request):
    """
    Change the CSRF token in use for a request - should be done on login
    for security purposes.
    """
    request.META.update({
        "CSRF_COOKIE_USED": True,
        "CSRF_COOKIE": _get_new_csrf_token(),
    })
    request.csrf_cookie_needs_reset = True


class CsrfViewMiddleware():
    """
    Require a present and correct csrfmiddlewaretoken for POST requests that
    have a CSRF cookie, and set an outgoing CSRF cookie.
    This middleware should be used in conjunction with the {% csrf_token %}
    template tag.
    """

    def __init__(self, app=None):
        self._exempt_views = set()
        self._exempt_blueprints = set()

        if app:
            self.init_app(app)

    def init_app(self, app):
        app.extensions['invenio_csrf'] = self

        app.config.setdefault('CSRF_ENABLED', True)
        app.config.setdefault('CSRF_CHECK_DEFAULT', True)
        app.config['CSRF_METHODS'] = set(app.config.get(
            'CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE']
        ))
        app.config.setdefault('CSRF_FIELD_NAME', 'csrf_token')
        app.config.setdefault(
            'CSRF_HEADERS', ['X-CSRFToken', 'X-CSRF-Token']
        )
        app.config.setdefault('CSRF_TIME_LIMIT', 3600)
        app.config.setdefault('CSRF_SSL_STRICT', True)

        @app.after_request
        def csrf_send(response):
            return self.process_response(request, response)

        @app.before_request
        def csrf_protect():
            # Check if request was made through an oauth token
            # import ipdb; ipdb.set_trace()
            # if request.oauth:
            #     return

            if request.method not in app.config['CSRF_METHODS']:
                return

            # if not request.endpoint:
            #     return

            # if request.blueprint in self._exempt_blueprints:
            #     return

            # view = app.view_functions.get(request.endpoint)
            # dest = '{0}.{1}'.format(view.__module__, view.__name__)

            # if dest in self._exempt_views:
            #     return

            return self.process_view()

    # The _accept and _reject methods currently only exist for the sake of the
    #  decorator.
    def _accept(self, request):
        # Avoid checking the request twice by adding a custom attribute to
        # request.  This will be relevant when both decorator and middleware
        # are used.
        return None

    def _reject(self, request, reason):
        abort(403)

    def _get_cookie_token(self, request):
        # if current_app.config.get('CSRF_USE_SESSIONS', False):
        #     try:
        #         return session.get(CSRF_SESSION_KEY)
        #     except AttributeError:
        #         raise RESTCSRFError(
        #             'CSRF_USE_SESSIONS is enabled, but request.session is not '
        #             'set. SessionMiddleware must appear before CsrfViewMiddleware '
        #             'in MIDDLEWARE.'
        #         )
        # else:
        try:
            cookie_token = request.cookies[CSRF_COOKIE_NAME]
        except KeyError:
            return None

        return _decode_jwt(cookie_token)

    def _set_token(self, request, response):
        # if current_app.config.get('CSRF_USE_SESSIONS'):
        #     if session.get(CSRF_SESSION_KEY) != request.CSRF_COOKIE:
        #         session[CSRF_SESSION_KEY] = request.CSRF_COOKIE
        # else:
        response.set_cookie(
            CSRF_COOKIE_NAME,
            _get_new_csrf_token(),
            max_age=current_app.config.get('CSRF_COOKIE_AGE', None),
            expires=current_app.config.get('CSRF_COOKIE_EXPIRES', None),
            domain=current_app.config.get('CSRF_COOKIE_DOMAIN', None),
            path=current_app.config.get('CSRF_COOKIE_PATH', '/'),
            # secure=current_app.config.get('CSRF_COOKIE_SECURE', True),
            httponly=current_app.config.get('CSRF_COOKIE_HTTPONLY', False),
            samesite=current_app.config.get('CSRF_COOKIE_SAMESITE', 'Lax'),
        )
        # # Set the Vary header since content varies with the CSRF cookie.
        # patch_vary_headers(response, ('Cookie',))

    def _get_csrf_token(self):
        # find the token in the form data
        field_name = current_app.config['CSRF_FIELD_NAME']
        base_token = request.form.get(field_name)

        if base_token:
            return base_token

        # if the form has a prefix, the name will be {prefix}-csrf_token
        for key in request.form:
            if key.endswith(field_name):
                csrf_token = request.form[key]

                if csrf_token:
                    return csrf_token

        # find the token in the headers
        for header_name in current_app.config['CSRF_HEADERS']:
            csrf_token = request.headers.get(header_name)

            if csrf_token:
                return csrf_token

        return None

    def process_request(self, request):
        csrf_token = self._get_cookie_token(request)
        if csrf_token is not None:
            # Use same token next time.
            request.META['CSRF_COOKIE'] = csrf_token

    def process_view(self):
        if getattr(request, 'csrf_processing_done', False):
            return None

        # Assume that anything not defined as 'safe' by RFC7231 needs protection
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            if getattr(request, '_dont_enforce_csrf_checks', False):
                # Mechanism to turn off CSRF checks for test suite.
                # It comes after the creation of CSRF cookies, so that
                # everything else continues to work exactly the same
                # (e.g. cookies are sent, etc.), but before any
                # branches that call reject().
                return self._accept(request)

            # if request.is_secure():
            #     # Suppose user visits http://example.com/
            #     # An active network attacker (man-in-the-middle, MITM) sends a
            #     # POST form that targets https://example.com/detonate-bomb/ and
            #     # submits it via JavaScript.
            #     #
            #     # The attacker will need to provide a CSRF cookie and token, but
            #     # that's no problem for a MITM and the session-independent
            #     # secret we're using. So the MITM can circumvent the CSRF
            #     # protection. This is true for any HTTP connection, but anyone
            #     # using HTTPS expects better! For this reason, for
            #     # https://example.com/ we need additional protection that treats
            #     # http://example.com/ as completely untrusted. Under HTTPS,
            #     # Barth et al. found that the Referer header is missing for
            #     # same-domain requests in only about 0.2% of cases or less, so
            #     # we can use strict Referer checking.
            #     referer = request.META.get('HTTP_REFERER')
            #     if referer is None:
            #         return self._reject(request, REASON_NO_REFERER)

            #     # referer = urlparse(referer)

            #     # # Make sure we have a valid URL for Referer.
            #     # if '' in (referer.scheme, referer.netloc):
            #     #     return self._reject(request, REASON_MALFORMED_REFERER)

            #     # Ensure that our Referer is also secure.
            #     if referer.scheme != 'https':
            #         return self._reject(request, REASON_INSECURE_REFERER)

            #     # If there isn't a CSRF_COOKIE_DOMAIN, require an exact match
            #     # match on host:port. If not, obey the cookie rules (or those
            #     # for the session cookie, if CSRF_USE_SESSIONS).
            #     good_referer = (
            #         settings.SESSION_COOKIE_DOMAIN
            #         if settings.CSRF_USE_SESSIONS
            #         else settings.CSRF_COOKIE_DOMAIN
            #     )
            #     if good_referer is not None:
            #         server_port = request.get_port()
            #         if server_port not in ('443', '80'):
            #             good_referer = '%s:%s' % (good_referer, server_port)
            #     else:
            #         try:
            #             # request.get_host() includes the port.
            #             good_referer = request.get_host()
            #         except DisallowedHost:
            #             pass

            #     # Create a list of all acceptable HTTP referers, including the
            #     # current host if it's permitted by ALLOWED_HOSTS.
            #     good_hosts = list(settings.CSRF_TRUSTED_ORIGINS)
            #     if good_referer is not None:
            #         good_hosts.append(good_referer)

            #     if not any(is_same_domain(referer.netloc, host) for host in good_hosts):
            #         reason = REASON_BAD_REFERER % referer.geturl()
            #         return self._reject(request, reason)

            csrf_token = self._get_cookie_token(request)

            if csrf_token is None:
                # No CSRF cookie. For POST requests, we insist on a CSRF cookie,
                # and in this way we can avoid all CSRF attacks, including login
                # CSRF.
                return self._reject(request, REASON_NO_CSRF_COOKIE)

            # Fall back to X-CSRFToken, to make things easier for AJAX,
            # and possible for PUT/DELETE.
            request_csrf_token = self._get_csrf_token()

            # decoded_csrf_token = _decode_jwt(csrf_token)
            decoded_request_csrf_token = _decode_jwt(request_csrf_token)

            if csrf_token != decoded_request_csrf_token:
                return self._reject(request, REASON_BAD_TOKEN)

        return self._accept(request)

    def process_response(self, request, response):
        # if not getattr(request, 'csrf_cookie_needs_reset', False):
        #     if getattr(response, 'csrf_cookie_set', False):
        #         return response

        # if not request.META.get("CSRF_COOKIE_USED", False):
        #     return response

        # Set the CSRF cookie even if it's already set, so we renew
        # the expiry timer.
        self._set_token(request, response)
        response.csrf_cookie_set = True
        return response
