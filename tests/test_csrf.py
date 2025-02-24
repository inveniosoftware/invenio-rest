# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
# Copyright (C) 2024 Graz University of Technology.
# Copyright (C) 2025 University of Münster.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import json

from flask import Blueprint, Flask, request

from invenio_rest.csrf import (
    REASON_BAD_REFERER,
    REASON_BAD_TOKEN,
    REASON_INSECURE_REFERER,
    REASON_MALFORMED_REFERER,
    REASON_NO_REFERER,
    CSRFProtectMiddleware,
    _get_new_csrf_token,
)


def test_csrf_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = CSRFProtectMiddleware(app)
    assert "invenio-csrf" in app.extensions

    app = Flask("testapp")
    ext = CSRFProtectMiddleware()
    assert "invenio-csrf" not in app.extensions
    ext.init_app(app)
    assert "invenio-csrf" in app.extensions


def test_csrf_disabled(csrf_app):
    """Test CSRF disabled."""
    with csrf_app.test_client() as client:
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.status_code == 200


def test_csrf_enabled(csrf_app, csrf):
    """Test CSRF enabled."""
    with csrf_app.test_client() as client:
        # First request to set the cookie
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        # obtain a token
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.json["message"] == REASON_BAD_TOKEN
        assert res.status_code == 400

        # don't send the token
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.json["message"] == REASON_BAD_TOKEN
        assert res.status_code == 400

        # send the token
        CSRF_COOKIE_NAME = csrf_app.config["CSRF_COOKIE_NAME"]
        CSRF_HEADER_NAME = csrf_app.config["CSRF_HEADER"]

        cookie = client.get_cookie(CSRF_COOKIE_NAME)

        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: cookie.value},
        )
        assert res.status_code == 200

        # The CSRF token should not have changed.
        new_cookie = client.get_cookie(CSRF_COOKIE_NAME)

        assert cookie.value == new_cookie.value


def test_csrf_before_csrf_protect(csrf_app, csrf):
    """Test before CSRF protect decorator."""
    assert csrf._before_protect_funcs == []

    @csrf.before_csrf_protect
    def before_protect():
        pass

    assert csrf._before_protect_funcs == [before_protect]

    csrf.before_csrf_protect(before_protect)

    assert csrf._before_protect_funcs == [before_protect, before_protect]


def test_csrf_exempt(csrf_app, csrf):
    """Test before CSRF protect decorator."""

    # Test `exempt` as a function passing the name of the view as string
    csrf.exempt("conftest.csrf_test")
    with csrf_app.test_client() as client:
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.status_code == 200


def test_csrf_exempt_dec(csrf_app, csrf):
    # Test `exempt` as a decorator on a view
    @csrf_app.route("/another-csrf-protect", methods=["POST"])
    @csrf.exempt
    def another_csrf_test():
        return "another test"

    with csrf_app.test_client() as client:
        res = client.post(
            "/another-csrf-protect",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.status_code == 200


def test_csrf_exempt_bp(csrf_app, csrf):
    # Test `exempt` as a decorator on a blueprint
    blueprint = Blueprint("test_csrf_bp", __name__, url_prefix="")

    @blueprint.route("/csrf-protect-bp", methods=["POST"])
    def csrf_bp():
        return "csrf bp test"

    @blueprint.route("/csrf-protect-bp-2", methods=["POST"])
    def csrf_bp_2():
        return "csrf bp test 2"

    csrf_app.register_blueprint(blueprint)

    csrf.exempt(blueprint)

    with csrf_app.test_client() as client:
        res = client.post(
            "/csrf-protect-bp",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.status_code == 200

        res = client.post(
            "/csrf-protect-bp-2",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.status_code == 200


def test_skip_csrf_check(csrf_app, csrf):
    """Test skipping CSRF check."""
    with csrf_app.test_client() as client:
        # First request to set the cookie
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.json["message"] == REASON_BAD_TOKEN
        assert res.status_code == 400

        @csrf.before_csrf_protect
        def csrf_skip():
            request.skip_csrf_check = True

        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        assert res.status_code == 200


def test_csrf_not_signed_correctly(csrf_app, csrf):
    """Test CSRF malicious attempt with passing malicious cookie and header."""
    from invenio_base.jws import TimedJSONWebSignatureSerializer

    with csrf_app.test_client() as client:
        # try to pass our own signed cookie and header in an attempt to bypass
        # the CSRF check
        csrf_serializer = TimedJSONWebSignatureSerializer(
            "invalid_secret",
            salt="invalid_salt",
        )
        malicious_cookie = csrf_serializer.dumps({"user": "malicious"}, "my_secret")
        CSRF_COOKIE_NAME = csrf_app.config["CSRF_COOKIE_NAME"]
        CSRF_HEADER_NAME = csrf_app.config["CSRF_HEADER"]
        client.set_cookie(
            CSRF_COOKIE_NAME, malicious_cookie.decode("utf-8"), domain="localhost"
        )

        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: malicious_cookie},
        )

        assert res.json["message"] == REASON_BAD_TOKEN
        assert res.status_code == 400


def test_csrf_token_rotation(csrf_app, csrf):
    """Test CSRF token rotation."""
    with csrf_app.test_client() as client:
        CSRF_COOKIE_NAME = csrf_app.config["CSRF_COOKIE_NAME"]
        CSRF_HEADER_NAME = csrf_app.config["CSRF_HEADER"]

        # Token in grace period - succeeds but token gets rotated
        expired_token = _get_new_csrf_token(expires_in=-1)
        client.set_cookie(CSRF_COOKIE_NAME, expired_token, domain="localhost")
        old_cookie = client.get_cookie(CSRF_COOKIE_NAME)
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: expired_token},
        )
        assert res.status_code == 200
        # Token was rotated and new requests succeeds
        new_cookie = client.get_cookie(CSRF_COOKIE_NAME)
        assert new_cookie.value != old_cookie.value
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: new_cookie.value},
        )
        assert res.status_code == 200
        # Subsequent requests doesn't rotate CSRF token
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: new_cookie.value},
        )
        last_cookie = client.get_cookie(CSRF_COOKIE_NAME)
        assert new_cookie.value == last_cookie.value
        assert res.status_code == 200

        # Token outside grace period
        # - Hack to have a negative grace period to force the error.
        csrf_app.config["CSRF_TOKEN_GRACE_PERIOD"] = -10000
        expired_token = _get_new_csrf_token(expires_in=-60 * 60 * 24 * 14)
        client.set_cookie(CSRF_COOKIE_NAME, expired_token, domain="localhost")
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: expired_token},
        )
        assert res.status_code == 400


def test_csrf_no_referer(csrf_app, csrf):
    """Test CSRF no referrer in a secure request."""
    with csrf_app.test_client() as client:
        # First request to set the cookie
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        # send the token to reach the CSRF check
        CSRF_COOKIE_NAME = csrf_app.config["CSRF_COOKIE_NAME"]
        CSRF_HEADER_NAME = csrf_app.config["CSRF_HEADER"]

        cookie = client.get_cookie(CSRF_COOKIE_NAME)

        res = client.post(
            "/csrf-protected",
            base_url="https://localhost",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: cookie.value},
        )
        assert res.json["message"] == REASON_NO_REFERER
        assert res.status_code == 400


def test_csrf_malformed_referer(csrf_app, csrf):
    """Test CSRF malformed referrer in a secure request."""
    with csrf_app.test_client() as client:
        # First request to set the cookie
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        # send the token to reach the CSRF check
        CSRF_COOKIE_NAME = csrf_app.config["CSRF_COOKIE_NAME"]
        CSRF_HEADER_NAME = csrf_app.config["CSRF_HEADER"]

        cookie = client.get_cookie(CSRF_COOKIE_NAME)

        res = client.post(
            "/csrf-protected",
            base_url="https://localhost",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: cookie.value, "Referer": "bad-referer"},
        )
        assert res.json["message"] == REASON_MALFORMED_REFERER
        assert res.status_code == 400


def test_csrf_insecure_referer(csrf_app, csrf):
    """Test CSRF insecure referrer in a secure request."""
    with csrf_app.test_client() as client:
        # First request to set the cookie
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        # send the token to reach the CSRF check
        CSRF_COOKIE_NAME = csrf_app.config["CSRF_COOKIE_NAME"]
        CSRF_HEADER_NAME = csrf_app.config["CSRF_HEADER"]

        cookie = client.get_cookie(CSRF_COOKIE_NAME)

        res = client.post(
            "/csrf-protected",
            base_url="https://localhost",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={
                CSRF_HEADER_NAME: cookie.value,
                "Referer": "http://insecure-referer",
            },
        )
        assert res.json["message"] == REASON_INSECURE_REFERER
        assert res.status_code == 400


def test_csrf_bad_referer(csrf_app, csrf):
    """Test CSRF bad referrer in a secure request."""
    with csrf_app.test_client() as client:
        # First request to set the cookie
        res = client.post(
            "/csrf-protected",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )
        # send the token to reach the CSRF check
        CSRF_COOKIE_NAME = csrf_app.config["CSRF_COOKIE_NAME"]
        CSRF_HEADER_NAME = csrf_app.config["CSRF_HEADER"]

        cookie = client.get_cookie(CSRF_COOKIE_NAME)

        csrf_app.config["TRUSTED_HOSTS"] = ["allowed-referer"]
        not_allowed_referer = "https://not-allowed-referer"
        res = client.post(
            "/csrf-protected",
            base_url="https://localhost",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
            headers={CSRF_HEADER_NAME: cookie.value, "Referer": not_allowed_referer},
        )
        assert res.json["message"] == REASON_BAD_REFERER % not_allowed_referer
        assert res.status_code == 400
