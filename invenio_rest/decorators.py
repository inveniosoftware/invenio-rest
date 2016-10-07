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

"""Decorators for testing certain assertions."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import request

from .errors import InvalidContentType


def require_content_types(*allowed_content_types):
    r"""Decorator to test if proper Content-Type is provided.

    :param \*allowed_content_types: List of allowed content types.
    :raises invenio_rest.errors.InvalidContentType: It's rised if a content
        type not allowed is required.
    """
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if request.mimetype not in allowed_content_types:
                raise InvalidContentType(allowed_content_types)
            return f(*args, **kwargs)
        return inner
    return decorator
