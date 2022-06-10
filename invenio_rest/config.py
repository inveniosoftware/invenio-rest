# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio REST configuration.

Please also see
`Flask-CORS <https://flask-cors.readthedocs.io/en/latest/>`__ for many more
configuration options.
"""

from __future__ import unicode_literals

CORS_RESOURCES = "*"
"""Dictionary for configuring CORS for endpoints.

   See Flask-CORS for further details.

.. note:: Overwrites
   `Flask-CORS
   <https://flask-cors.readthedocs.io/en/latest/api.html#flask_cors.CORS>`_
   configuration.
"""

CORS_SEND_WILDCARD = True
"""Sending wildcard CORS header.

.. note:: Overwrites
   `Flask-CORS
   <https://flask-cors.readthedocs.io/en/latest/api.html#flask_cors.CORS>`_
   configuration.
"""

CORS_EXPOSE_HEADERS = [
    "ETag",
    "Link",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "Content-Type",
]
"""Expose the following headers.

.. note:: Overwrites
   `Flask-CORS
   <https://flask-cors.readthedocs.io/en/latest/api.html#flask_cors.CORS>`_
   configuration.
"""

REST_ENABLE_CORS = False
"""Enable CORS configuration. (Default: ``False``)."""

REST_MIMETYPE_QUERY_ARG_NAME = None
"""Name of the query argument to specify the mimetype wanted for the output.
   Set it to None to disable.

.. note::
   You can customize the query argument name by specifying it as a string::

        REST_MIMETYPE_QUERY_ARG_NAME = 'format'

   With this value, the url will be::

        /api/record/<id>?format=<value>

   You can set the accepted values passing a dictionary to the key
   `record_serializers_aliases`::

       record_serializers_aliases={
          'json': 'application/json',
          'marc21': 'application/marcxml+xml'
       }
"""

REST_CSRF_ENABLED = False
"""Enable CSRF middleware. (Default: ``False``).

.. note::
   The CSRF middleware accepts some configuration parameters that are used to
   adjust the workflow of the CSRF validation. The available options are:

   \\`CSRF_SAFE_METHODS\\`: HTTP methods against which the csrf check should
   NOT run.
   Defaults to \\`['POST', 'PUT', 'PATCH', 'DELETE']\\`.

   \\`CSRF_HEADER\\`: The name of the request header used for CSRF
   authentication. Defaults to \\`X-CSRF-Token\\`.

   \\`CSRF_COOKIE_NAME\\`: The name of the request cookie used for CSRF
   authentication. Defaults to \\`_csrftoken\\`.

   \\`CSRF_COOKIE_MAX_AGE\\`: The maximum time until the cookie expires. After
   the expiration the cookie will be removed. Defaults to \\`60*60*24*7*52\\`
   (1 year).

   \\`CSRF_COOKIE_DOMAIN\\`: The domain for which the CSRF cookie should be
   valid. Defaults to \\`flask.sessions.SessionInterface.get_cookie_domain\\`.

   \\`CSRF_COOKIE_PATH\\`: The url path for which the cookie is set. This is
   useful if you have multiple Flask instances running under the same hostname.
   They can use different cookie paths, and each instance will only see its own
   CSRF cookie.
   Defaults to \\`flask.sessions.SessionInterface.get_cookie_path\\`.

   \\`CSRF_COOKIE_SAMESITE\\`: Restrict if CSRF cookie should be sent along
   requests coming from external sites. Defaults to
   \\`SESSION_COOKIE_SAMESITE\\` configuation variable, if this is set to
   a not \\`None\\` value, or \\`Lax\\`. Lax prevents sending cookies with
   CSRF-prone requests from external sites, such as submitting a form.

   \\`CSRF_SECRET\\`: Secret key to encode/decode csrf token. Defaults to
   application \\`SECRET_KEY\\`.

   \\`CSRF_SECRET_SALT\\`: The salt value used to encode/decode csrf token.
   Defaults to \\`invenio-csrf-token\\`.

   \\`CSRF_TOKEN_LENGTH\\`: The length of the generated csrf token. Defaults to
   \\`12\\`.

   \\`CSRF_ALLOWED_CHARS\\`: The allowed characters that can be included in the
   generation of the csrf token. Defaults to \\`string.ascii_letters\\` +
   \\`string.digits\\`.

   \\`CSRF_FORCE_SECURE_REFERER\\`: Flag to disable secure referrer check. This
   should used only in development if you run your UI application over HTTP.
   Defaults to \\`True\\`.
"""
