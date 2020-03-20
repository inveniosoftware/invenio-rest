# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API module for Invenio."""

from __future__ import absolute_import, print_function

import warnings

import pkg_resources

from . import config
from .views import create_api_errorhandler


class InvenioREST(object):
    """Invenio-REST extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        Initialize the Rate-Limiter, CORS and error handlers.

        :param app: An instance of :class:`flask.Flask`.
        """
        self.init_config(app)

        # Enable CORS support if desired
        if app.config['REST_ENABLE_CORS']:
            from flask_cors import CORS
            CORS(app)
            # CORS can be configured using CORS_* configuration variables.

        # Enable CSRF support if desired
        if app.config['REST_CSRF_ENABLED']:
            from .csrf import csrf
            csrf.init_app(app)
        else:
            warnings.warn(
                "CSRF validation will be enabled by default in the version"
                " 1.3.x",
                category=FutureWarning, stacklevel=2)

        app.errorhandler(400)(create_api_errorhandler(
            status=400, message='Bad Request'))
        app.errorhandler(401)(create_api_errorhandler(
            status=401, message='Unauthorized'))
        app.errorhandler(403)(create_api_errorhandler(
            status=403, message='Forbidden'))
        app.errorhandler(404)(create_api_errorhandler(
            status=404, message='Not Found'))
        app.errorhandler(405)(create_api_errorhandler(
            status=405, message='Method Not Allowed'))
        app.errorhandler(406)(create_api_errorhandler(
            status=406, message='Not Acceptable'))
        app.errorhandler(409)(create_api_errorhandler(
            status=409, message='Conflict'))
        app.errorhandler(410)(create_api_errorhandler(
            status=410, message='Gone'))
        app.errorhandler(412)(create_api_errorhandler(
            status=412, message='Precondition Failed'))
        app.errorhandler(415)(create_api_errorhandler(
            status=415, message='Unsupported media type'))
        app.errorhandler(422)(create_api_errorhandler(
            status=422, message='Unprocessable Entity'))
        app.errorhandler(429)(create_api_errorhandler(
            status=429, message='Rate limit exceeded'))
        app.errorhandler(500)(create_api_errorhandler(
            status=500, message='Internal Server Error'))
        app.errorhandler(501)(create_api_errorhandler(
            status=501, message='Not Implemented'))
        app.errorhandler(502)(create_api_errorhandler(
            status=502, message='Bad Gateway'))
        app.errorhandler(503)(create_api_errorhandler(
            status=503, message='Service Unavailable'))
        app.errorhandler(504)(create_api_errorhandler(
            status=504, message='Gateway Timeout'))

        app.extensions['invenio-rest'] = self

    def init_config(self, app):
        """Initialize configuration.

        .. note:: Change Flask-CORS and Flask-Limiter defaults.

        :param app: An instance of :class:`flask.Flask`.
        """
        config_apps = ['REST_', 'CORS_', ]
        for k in dir(config):
            if any([k.startswith(prefix) for prefix in config_apps]):
                app.config.setdefault(k, getattr(config, k))
