# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import shutil
import tempfile

import pytest
from flask import Flask

from invenio_rest.ext import InvenioREST


@pytest.fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask("testapp", instance_path=instance_path)
    app_.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        REST_CSRF_ENABLED=False,
    )

    @app_.route("/ping")
    def ping():
        return "ping"

    return app_


@pytest.fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def csrf_app(base_app):
    """Flask application fixture with csrf enabled."""
    InvenioREST(base_app)

    @base_app.route("/csrf-protected", methods=["POST"])
    def csrf_test():
        return "test"

    with base_app.app_context():
        yield base_app


@pytest.fixture()
def csrf(csrf_app):
    """Initialize CSRF object on every test function.

    We don't import `csrf` from `invenio_rest.csrf` because
    like that it is not cleared after every test fuction run.
    """
    from invenio_rest.csrf import CSRFProtectMiddleware

    csrf = CSRFProtectMiddleware(csrf_app)
    assert "invenio-csrf" in csrf_app.extensions
    yield csrf
