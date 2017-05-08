# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016, 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio REST configuration.

Please also see
`Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_ and
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

.. note:: Overwrite
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

.. note:: Overwrite
   `Flask-CORS
   <https://flask-cors.readthedocs.io/en/latest/api.html#flask_cors.CORS>`_
   configuration.
"""

REST_ENABLE_CORS = False
"""Enable CORS configuration. (Default: ``False``)"""

RATELIMIT_DEFAULT = '5000/hour'
"""Default rate limit.

.. note:: Overwrite
   Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_
   configuration.
"""

RATELIMIT_HEADERS_ENABLED = True
"""Enable rate limit headers. (Default: ``True``)

.. note:: Overwrite
   Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_
   configuration.
"""
