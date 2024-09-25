# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2022 Northwestern University.
# Copyright (C) 2023-2024 Graz University of Technology.
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
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from flask import Blueprint, abort, current_app, request
from itsdangerous import BadSignature, SignatureExpired

try:
    # itsdangerous < 2.1.0
    from itsdangerous import TimedJSONWebSignatureSerializer
except ImportError:
    # itsdangerous >= 2.1.0
    from invenio_base.jws import TimedJSONWebSignatureSerializer

REASON_NO_REFERER = "Referer checking failed - no Referer."
REASON_BAD_REFERER = "Referer checking failed - %s does not match any trusted origins."
REASON_NO_CSRF_COOKIE = "CSRF cookie not set."
REASON_BAD_TOKEN = "CSRF token missing or incorrect."
REASON_MALFORMED_REFERER = "Referer checking failed - Referer is malformed."
REASON_INSECURE_REFERER = (
    "Referer checking failed - Referer is insecure while host is secure."
)
REASON_TOKEN_EXPIRED = "CSRF token expired. Try again."


def _get_csrf_serializer(expires_in=None):
    """Note that this serializer is used to encode/decode the CSRF cookie.

    In case you change this implementation bear in mind that the token
    generated must be signed so as to avoid any client-side tampering.
    """
    expires_in = expires_in or current_app.config["CSRF_TOKEN_EXPIRES_IN"]

    return TimedJSONWebSignatureSerializer(
        current_app.config.get(
            "CSRF_SECRET", current_app.config.get("SECRET_KEY") or "CHANGE_ME"
        ),
        salt=current_app.config["CSRF_SECRET_SALT"],
        expires_in=expires_in,
    )


def _get_random_string(length, allowed_chars):
    return "".join(secrets.choice(allowed_chars) for i in range(length))


def _get_new_csrf_token(expires_in=None):
    csrf_serializer = _get_csrf_serializer(expires_in=expires_in)
    encoded_token = csrf_serializer.dumps(
        _get_random_string(
            current_app.config["CSRF_TOKEN_LENGTH"],
            current_app.config["CSRF_ALLOWED_CHARS"],
        )
    )
    return encoded_token


def _get_csrf_token():
    try:
        csrf_cookie = request.cookies[current_app.config["CSRF_COOKIE_NAME"]]
    except KeyError:
        return None
    return _decode_csrf(csrf_cookie)


def _decode_csrf(data):
    csrf_serializer = _get_csrf_serializer()
    try:
        return csrf_serializer.loads(data)
    except SignatureExpired as e:
        grace_period = timedelta(seconds=current_app.config["CSRF_TOKEN_GRACE_PERIOD"])
        # Because we support ItsDangerous 1.X and 2.X we need to compute the
        # appropriately-timezone-aware-or-naive datetime. See
        # https://github.com/pallets/itsdangerous/blob/1.0.x/src/itsdangerous/jws.py#L212  # noqa
        # https://github.com/pallets/itsdangerous/blob/2.0.x/src/itsdangerous/jws.py#L244  # noqa
        now = (
            datetime.now(tz=timezone.utc) if e.date_signed.tzinfo else datetime.utcnow()
        )  # noqa
        if e.date_signed < now - grace_period:
            # Grace period for token rotation exceeded.
            _abort400(REASON_TOKEN_EXPIRED)
        else:
            # Accept expired token, but rotate it to a new one.
            reset_token()
            return e.payload
    except BadSignature:
        _abort400(REASON_BAD_TOKEN)


def _set_token(response):
    response.set_cookie(
        current_app.config["CSRF_COOKIE_NAME"],
        _get_new_csrf_token().decode("utf-8"),
        max_age=current_app.config.get(
            # 1 week for cookie (but we rotate the token every day)
            "CSRF_COOKIE_MAX_AGE",
            60 * 60 * 24 * 7,
        ),
        domain=current_app.config.get(
            "CSRF_COOKIE_DOMAIN",
            current_app.session_interface.get_cookie_domain(current_app),
        ),
        path=current_app.session_interface.get_cookie_path(current_app),
        secure=current_app.config.get("SESSION_COOKIE_SECURE", True),
        httponly=False,
        samesite=current_app.config["CSRF_COOKIE_SAMESITE"],
    )


def _get_submitted_csrf_token():
    header_name = current_app.config["CSRF_HEADER"]
    csrf_token = request.headers.get(header_name)
    if csrf_token:
        return csrf_token
    return None


def _is_referer_secure(referer):
    return (
        "https" in referer.scheme or not current_app.config["CSRF_FORCE_SECURE_REFERER"]
    )


def _abort400(reason):
    abort(400, reason)


def csrf_validate():
    """Check CSRF cookie against request headers."""
    # If the cookie is not set, we don't need to check anything.
    if not request.cookies:
        return

    csrf_token = _get_csrf_token()
    if csrf_token is None:
        return _abort400(REASON_NO_CSRF_COOKIE)

    request_csrf_token = _get_submitted_csrf_token()
    if not request_csrf_token:
        _abort400(REASON_BAD_TOKEN)

    if request.is_secure:
        referer = request.referrer
        if referer is None:
            return _abort400(REASON_NO_REFERER)

        referer = urlparse(referer)
        # Make sure we have a valid URL for Referer.
        if "" in (referer.scheme, referer.netloc):
            return _abort400(REASON_MALFORMED_REFERER)

        # Ensure that our Referer is also secure.
        if not _is_referer_secure(referer):
            return _abort400(REASON_INSECURE_REFERER)

        is_hostname_allowed = referer.hostname in current_app.config.get(
            "APP_ALLOWED_HOSTS"
        )
        if not is_hostname_allowed:
            reason = REASON_BAD_REFERER % referer.geturl()
            return _abort400(reason)

    decoded_request_csrf_token = _decode_csrf(request_csrf_token)

    if csrf_token != decoded_request_csrf_token:
        return _abort400(REASON_BAD_TOKEN)


def reset_token():
    """Change the CSRF token in use for a request."""
    request.csrf_cookie_needs_reset = True


class CSRFTokenMiddleware:
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
        app.config.setdefault("CSRF_COOKIE_NAME", "csrftoken")
        app.config.setdefault("CSRF_HEADER", "X-CSRFToken")
        app.config.setdefault("CSRF_METHODS", ["POST", "PUT", "PATCH", "DELETE"])
        app.config.setdefault("CSRF_TOKEN_LENGTH", 32)
        app.config.setdefault(
            "CSRF_ALLOWED_CHARS", string.ascii_letters + string.digits
        )
        app.config.setdefault("CSRF_SECRET_SALT", "invenio-csrf-token")
        app.config.setdefault("CSRF_FORCE_SECURE_REFERER", True)
        app.config.setdefault(
            "CSRF_COOKIE_SAMESITE", app.config.get("SESSION_COOKIE_SAMESITE") or "Lax"
        )
        # The token last for 24 hours, but the cookie for 7 days. This allows
        # us to implement transparent token rotation during those 7 days. Note,
        # that the token is automatically rotated on login, thus you can also
        # change PERMANENT_SESSION_LIFETIME
        app.config.setdefault("CSRF_TOKEN_EXPIRES_IN", 60 * 60 * 24)
        # We allow usage of an expired CSRF token during this period. This way
        # we can rotate the CSRF token without the user getting an CSRF error.
        # Align with CSRF_COOKIE_MAX_AGE
        app.config.setdefault("CSRF_TOKEN_GRACE_PERIOD", 60 * 60 * 24 * 7)

        @app.after_request
        def csrf_send(response):
            is_method_vulnerable = request.method in app.config["CSRF_METHODS"]
            cookie_needs_reset = getattr(request, "csrf_cookie_needs_reset", False)
            cookie_is_missing = (
                current_app.config["CSRF_COOKIE_NAME"] not in request.cookies
            )
            if (is_method_vulnerable and cookie_is_missing) or cookie_needs_reset:
                _set_token(response)
            return response

        app.extensions["invenio-csrf"] = self


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

            is_method_vulnerable = request.method in app.config["CSRF_METHODS"]
            if not is_method_vulnerable:
                return

            if request.blueprint in self._exempt_blueprints:
                return

            if hasattr(request, "skip_csrf_check"):
                return

            view = app.view_functions.get(request.endpoint)
            if view:
                dest = "{0}.{1}".format(view.__module__, view.__name__)
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

        if isinstance(view, str):
            view_location = view
        else:
            view_location = ".".join((view.__module__, view.__name__))

        self._exempt_views.add(view_location)
        return view


csrf = CSRFProtectMiddleware()
