# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Exceptions used in Invenio REST module."""

from __future__ import absolute_import, print_function

import json

from werkzeug.exceptions import HTTPException


class RESTException(HTTPException):
    """HTTP Exception delivering JSON error responses."""

    def get_description(self, environ=None):
        """Get the description."""
        return self.description

    def get_body(self, environ=None):
        """Get the request body."""
        return json.dumps(dict(
            status=self.code,
            message=self.get_description(environ)
        ))

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [('Content-Type', 'application/json')]


class SameContentException(Exception):
    """304 Same Content exception.

    Exception thrown when request is GET or HEAD, ETag is If-None-Match and
    one or more of the ETag values match.
    """

    def __init__(self, etag):
        """Constructor.

        :param etag: matching etag
        """
        self.etag = etag


class InvalidContentType(RESTException):
    """Error for when an invalid content-type is provided."""

    code = 415

    def __init__(self, allowed_contet_types=None):
        """Initialize exception."""
        self.allowed_contet_types = allowed_contet_types
        self.description = \
            "Invalid 'Content-Type' header. Expected one of: {0}".format(
                ", ".join(allowed_contet_types))
