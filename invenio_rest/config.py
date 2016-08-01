# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Invenio REST configuration."""

from __future__ import unicode_literals

CORS_SEND_WILDCARD = True
"""Sending wildcard CORS header.

Overwrite Flask-CORS configuration.
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

.. note:: Overwrite Flask-CORS configuration.
"""

REST_ENABLE_CORS = False
"""Enable CORS configuration. (Default: ``False``)"""

RATELIMIT_GLOBAL = '5000/hour'
"""Global rate limit.

.. note:: Overwrite Flask-Limiter configuration.
"""

RATELIMIT_HEADERS_ENABLED = True
"""Enable rate limit headers. (Default: ``True``)

.. note:: Overwrite Flask-Limiter configuration.
"""
