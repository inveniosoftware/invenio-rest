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
from itsdangerous import BadSignature, URLSafeSerializer
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

CSRF_COOKIE_NAME = '_csrftoken'
CSRF_TOKEN_LENGTH = 32
CSRF_ALLOWED_CHARS = string.ascii_letters + string.digits
CSRF_SECRET_SALT = 'ISSUE_CSRF'


def _get_csrf_secret():
    return current_app.config.get(
        'CSRF_SECRET',
        current_app.config.get('SECRET_KEY') or 'CHANGE_ME')


def _get_random_string(length=12,
                       allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                     'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    return ''.join(secrets.choice(allowed_chars) for i in range(length))


def _get_new_csrf_token():
    csrf_serializer = URLSafeSerializer(
        _get_csrf_secret(), salt=current_app.config['CSRF_SECRET_SALT'])
    encoded_token = csrf_serializer.dumps(
        _get_random_string(
            current_app.config['CSRF_TOKEN_LENGTH'],
            current_app.config['CSRF_ALLOWED_CHARS'],
        )
    )
    return encoded_token


def _decode_csrf(data):
    csrf_serializer = URLSafeSerializer(
        _get_csrf_secret(), salt=current_app.config['CSRF_SECRET_SALT'])
    try:
        return csrf_serializer.loads(data)
    except BadSignature:
        raise RESTCSRFError()


class CSRFMiddleware():
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
        app.extensions['invenio-csrf'] = self

        app.config['CSRF_METHODS'] = set(app.config.get(
            'CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE']
        ))
        app.config.setdefault('CSRF_HEADER', 'X-CSRF-Token')
        app.config.setdefault('CSRF_COOKIE_NAME', CSRF_COOKIE_NAME)
        app.config.setdefault('CSRF_TOKEN_LENGTH', CSRF_TOKEN_LENGTH)
        app.config.setdefault('CSRF_ALLOWED_CHARS', CSRF_ALLOWED_CHARS)
        app.config.setdefault('CSRF_SECRET_SALT', CSRF_SECRET_SALT)

        @app.after_request
        def csrf_send(response):
            if getattr(request, 'csrf_cookie_needs_reset', False) or \
               current_app.config['CSRF_COOKIE_NAME'] not in request.cookies:
                self._set_token(response)
            return response

        @app.before_request
        def csrf_protect():

            for func in self._before_protect_funcs:
                func()

            if request.method not in app.config['CSRF_METHODS']:
                return

            if not request.endpoint:
                return

            if request.blueprint in self._exempt_blueprints:
                return

            if hasattr(request, 'skip_csrf_check'):
                return

            view = app.view_functions.get(request.endpoint)
            dest = '{0}.{1}'.format(view.__module__, view.__name__)

            if dest in self._exempt_views:
                return

            return self.csrf_validate()

    def reset_token(self):
        """Change the CSRF token in use for a request."""
        request.csrf_cookie_needs_reset = True

    def _reject(self, reason):
        abort(400, reason)

    def _get_csrf_token(self):
        try:
            csrf_cookie = request.cookies[
                current_app.config['CSRF_COOKIE_NAME']]
        except KeyError:
            return None
        return _decode_csrf(csrf_cookie)

    def _set_token(self, response):
        response.set_cookie(
            CSRF_COOKIE_NAME,
            _get_new_csrf_token(),
            max_age=current_app.config.get(
                'CSRF_COOKIE_MAX_AGE', 60*60*24*7*52),
            domain=current_app.config.get(
                'CSRF_COOKIE_DOMAIN',
                current_app.session_interface.get_cookie_domain(
                    current_app)),
            path=current_app.session_interface.get_cookie_path(
                 current_app),
            secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
            httponly=False,
            samesite=current_app.config.get(
                'CSRF_COOKIE_SAMESITE',
                current_app.config.get('SESSION_COOKIE_SAMESITE')) or 'Lax',
        )

    def _get_submitted_csrf_token(self):
        header_name = current_app.config['CSRF_HEADER']
        csrf_token = request.headers.get(header_name)
        if csrf_token:
            return csrf_token
        return None

    def _is_referrer_secure(self, referrer):
        return 'https' in referrer.scheme or \
            not current_app.config.get('CSRF_FORCE_SECURE_REFERRER', True)

    def csrf_validate(self):
        """Check csrf cookie against request headers."""
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            if request.is_secure:
                referrer = request.referrer

                if referrer is None:
                    return self._reject(REASON_NO_REFERER)

                referrer = urlparse(referrer)
                # Make sure we have a valid URL for Referer.
                if '' in (referrer.scheme, referrer.netloc):
                    return self._reject(REASON_MALFORMED_REFERER)

                # Ensure that our Referer is also secure.
                if not self._is_referrer_secure(referrer):
                    return self._reject(REASON_INSECURE_REFERER)

                if referrer.hostname not in current_app.config.get(
                                                'APP_ALLOWED_HOSTS'):
                    reason = REASON_BAD_REFERER % referrer.geturl()
                    return self._reject(reason)

            csrf_token = self._get_csrf_token()
            if csrf_token is None:
                return self._reject(REASON_NO_CSRF_COOKIE)

            request_csrf_token = self._get_submitted_csrf_token()
            if not request_csrf_token:
                self._reject(REASON_BAD_TOKEN)

            decoded_request_csrf_token = _decode_csrf(request_csrf_token)

            if csrf_token != decoded_request_csrf_token:
                return self._reject(REASON_BAD_TOKEN)

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

csrf = CSRFMiddleware()
