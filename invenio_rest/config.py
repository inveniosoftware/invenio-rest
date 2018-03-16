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

CORS_RESOURCES = '*'
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
    'ETag',
    'Link',
    'X-RateLimit-Limit',
    'X-RateLimit-Remaining',
    'X-RateLimit-Reset',
    'Content-Type',
]
"""Expose the following headers.

.. note:: Overwrites
   `Flask-CORS
   <https://flask-cors.readthedocs.io/en/latest/api.html#flask_cors.CORS>`_
   configuration.
"""

REST_ENABLE_CORS = False
"""Enable CORS configuration. (Default: ``False``)"""

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
