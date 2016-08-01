# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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
from werkzeug.http import http_date


class FieldError(object):
    """Represents a field level error.

    .. note:: This is not an actual exception.
    """

    def __init__(self, field, message, code=None):
        """Init object.

        :param field: Field name.
        :param message: The text message to show.
        :param code: The HTTP status to return. (Default: ``None``)
        """
        self.res = dict(field=field, message=message)
        if code:
            self.res['code'] = code

    def to_dict(self):
        """Convert to dictionary.

        :returns: A dictionary with field, message and, if initialized, the
            HTTP status code.
        """
        return self.res


class RESTException(HTTPException):
    """HTTP Exception delivering JSON error responses."""

    errors = None

    def __init__(self, errors=None, **kwargs):
        """Initialize RESTException."""
        super(RESTException, self).__init__(**kwargs)
        if errors is not None:
            self.errors = errors

    def get_errors(self):
        """Get errors.

        :returns: A list containing a dictionary representing the errors.
        """
        return [e.to_dict() for e in self.errors] if self.errors else None

    def get_description(self, environ=None):
        """Get the description."""
        return self.description

    def get_body(self, environ=None):
        """Get the request body."""
        body = dict(
            status=self.code,
            message=self.get_description(environ),
        )

        errors = self.get_errors()
        if self.errors:
            body['errors'] = errors

        return json.dumps(body)

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [('Content-Type', 'application/json')]


class InvalidContentType(RESTException):
    """Error for when an invalid Content-Type is provided."""

    code = 415
    """HTTP Status code."""

    def __init__(self, allowed_content_types=None, **kwargs):
        """Initialize exception."""
        super(InvalidContentType, self).__init__(**kwargs)
        self.allowed_content_types = allowed_content_types
        self.description = \
            "Invalid 'Content-Type' header. Expected one of: {0}".format(
                ", ".join(allowed_content_types))


class RESTValidationError(RESTException):
    """A standard REST validation error."""

    code = 400
    """HTTP Status code."""

    description = 'Validation error.'
    """Error description."""


class SameContentException(RESTException):
    """304 Same Content exception.

    Exception thrown when request is GET or HEAD, ETag is If-None-Match and
    one or more of the ETag values match.
    """

    code = 304
    """HTTP Status code."""

    description = 'Same Content.'
    """Error description."""

    def __init__(self, etag, last_modified=None, **kwargs):
        """Constructor.

        :param etag: matching etag
        :param last_modified: The last modefied date. (Default: ``None``)
        """
        super(SameContentException, self).__init__(**kwargs)
        self.etag = etag
        self.last_modified = last_modified

    def get_response(self, environ=None):
        """Get a list of headers."""
        response = super(SameContentException, self).get_response(
            environ=environ
        )
        if self.etag is not None:
            response.set_etag(self.etag)
        if self.last_modified is not None:
            response.headers['Last-Modified'] = http_date(self.last_modified)
        return response
