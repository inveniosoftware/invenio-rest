# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CSRF Middleware.

The implementation is highly inspred from Django's initial implementation
about CSRF protection. For more information you can see here:
<https://github.com/django/django/blob/master/django/middleware/csrf.py>
"""

import re
import secrets
import string

from flask import Blueprint, abort, current_app, request
from itsdangerous import BadSignature, TimedJSONWebSignatureSerializer
from six import string_types
from six.moves.urllib.parse import urlparse

from .errors import RESTCSRFError

REASON_NO_REFERER = "Referer checking failed - no Referer."
REASON_BAD_REFERER = (
    "Referer checking failed - %s does not match any trusted origins."
)
REASON_NO_CSRF_COOKIE = "CSRF cookie not set."
REASON_BAD_TOKEN = "CSRF token missing or incorrect."
REASON_MALFORMED_REFERER = "Referer checking failed - Referer is malformed."
REASON_INSECURE_REFERER = (
    "Referer checking failed - Referer is insecure while host is secure."
)


def _get_csrf_serializer():
    """Note that this serializer is used to encode/decode the CSRF cookie.

    In case you change this implementation bear in mind that the token
    generated must be signed so as to avoid any client-side tampering.
    """
    return TimedJSONWebSignatureSerializer(
        current_app.config.get(
            'CSRF_SECRET',
            current_app.config.get('SECRET_KEY') or 'CHANGE_ME'),
        salt=current_app.config['CSRF_SECRET_SALT'])


def _get_random_string(length, allowed_chars):
    return ''.join(secrets.choice(allowed_chars) for i in range(length))


def _get_new_csrf_token():
    csrf_serializer = _get_csrf_serializer()
    encoded_token = csrf_serializer.dumps(
        _get_random_string(
            current_app.config['CSRF_TOKEN_LENGTH'],
            current_app.config['CSRF_ALLOWED_CHARS'],
        )
    )
    return encoded_token


def _get_csrf_token():
    try:
        csrf_cookie = request.cookies[
            current_app.config['CSRF_COOKIE_NAME']]
    except KeyError:
        return None
    return _decode_csrf(csrf_cookie)


def _decode_csrf(data):
    csrf_serializer = _get_csrf_serializer()
    try:
        return csrf_serializer.loads(data)
    except BadSignature:
        raise RESTCSRFError()


def _set_token(response):
    response.set_cookie(
        current_app.config['CSRF_COOKIE_NAME'],
        _get_new_csrf_token(),
        max_age=current_app.config.get(
            'CSRF_COOKIE_MAX_AGE', 60*60*24*7*52),
        domain=current_app.config.get(
            'CSRF_COOKIE_DOMAIN',
            current_app.session_interface.get_cookie_domain(
                current_app)),
        path=current_app.session_interface.get_cookie_path(
                current_app),
        secure=current_app.config.get('SESSION_COOKIE_SECURE', True),
        httponly=False,
        samesite=current_app.config['CSRF_COOKIE_SAMESITE'],
    )


def _get_submitted_csrf_token():
    header_name = current_app.config['CSRF_HEADER']
    csrf_token = request.headers.get(header_name)
    if csrf_token:
        return csrf_token
    return None


def _is_referer_secure(referer):
    return 'https' in referer.scheme or \
        not current_app.config['CSRF_FORCE_SECURE_REFERER']


def _abort400(reason):
        abort(400, reason)


def csrf_validate():
    """Check CSRF cookie against request headers."""
    if request.is_secure:
        referer = request.referrer

        if referer is None:
            return _abort400(REASON_NO_REFERER)

        referer = urlparse(referer)
        # Make sure we have a valid URL for Referer.
        if '' in (referer.scheme, referer.netloc):
            return _abort400(REASON_MALFORMED_REFERER)

        # Ensure that our Referer is also secure.
        if not _is_referer_secure(referer):
            return _abort400(REASON_INSECURE_REFERER)

        is_hostname_allowed = referer.hostname in \
            current_app.config.get('APP_ALLOWED_HOSTS')
        if not is_hostname_allowed:
            reason = REASON_BAD_REFERER % referer.geturl()
            return _abort400(reason)

    csrf_token = _get_csrf_token()
    if csrf_token is None:
        return _abort400(REASON_NO_CSRF_COOKIE)

    request_csrf_token = _get_submitted_csrf_token()
    if not request_csrf_token:
        _abort400(REASON_BAD_TOKEN)

    decoded_request_csrf_token = _decode_csrf(request_csrf_token)

    if csrf_token != decoded_request_csrf_token:
        return _abort400(REASON_BAD_TOKEN)


def reset_token():
        """Change the CSRF token in use for a request."""
        request.csrf_cookie_needs_reset = True


class CSRFTokenMiddleware():
    """CSRF Token Middleware."""

    def __init__(self, app=None):
        """Middleware initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware extension.

        :param app: An instance of :class:`flask.Flask`.
        """
        app.config.setdefault('CSRF_COOKIE_NAME', 'csrftoken')
        app.config.setdefault('CSRF_HEADER', 'HTTP_X_CSRFTOKEN')
        app.config.setdefault(
            'CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE'])
        app.config.setdefault('CSRF_TOKEN_LENGTH', 32)
        app.config.setdefault(
            'CSRF_ALLOWED_CHARS', string.ascii_letters + string.digits)
        app.config.setdefault('CSRF_SECRET_SALT', 'invenio-csrf-token')
        app.config.setdefault('CSRF_FORCE_SECURE_REFERER', True)
        app.config.setdefault(
            'CSRF_COOKIE_SAMESITE',
            app.config.get('SESSION_COOKIE_SAMESITE') or 'Lax')

        @app.after_request
        def csrf_send(response):
            is_method_vulnerable = request.method in app.config['CSRF_METHODS']
            cookie_needs_reset = getattr(
                request, 'csrf_cookie_needs_reset', False)
            cookie_is_missing = current_app.config['CSRF_COOKIE_NAME'] not in \
                request.cookies
            if is_method_vulnerable or cookie_needs_reset or cookie_is_missing:
                _set_token(response)
            return response

        app.extensions['invenio-csrf'] = self


class CSRFProtectMiddleware(CSRFTokenMiddleware):
    """CSRF Middleware."""

    def __init__(self, app=None):
        """Middleware initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        self._exempt_views = set()
        self._exempt_blueprints = set()

        self._before_protect_funcs = []
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware extension.

        :param app: An instance of :class:`flask.Flask`.
        """
        super(CSRFProtectMiddleware, self).init_app(app)

        @app.before_request
        def csrf_protect():
            """CSRF protect method."""
            for func in self._before_protect_funcs:
                func()

            is_method_vulnerable = request.method in app.config['CSRF_METHODS']
            if not is_method_vulnerable:
                return

            if request.blueprint in self._exempt_blueprints:
                return

            if hasattr(request, 'skip_csrf_check'):
                return

            view = app.view_functions.get(request.endpoint)
            dest = '{0}.{1}'.format(view.__module__, view.__name__)

            if dest in self._exempt_views:
                return

            return csrf_validate()

    def before_csrf_protect(self, f):
        """Register functions to be invoked before checking csrf.

        The function accepts nothing as parameters.
        """
        self._before_protect_funcs.append(f)
        return f

    def exempt(self, view):
        """Mark a view or blueprint to be excluded from CSRF protection."""
        if isinstance(view, Blueprint):
            self._exempt_blueprints.add(view.name)
            return view

        if isinstance(view, string_types):
            view_location = view
        else:
            view_location = '.'.join((view.__module__, view.__name__))

        self._exempt_views.add(view_location)
        return view

csrf = CSRFProtectMiddleware()
