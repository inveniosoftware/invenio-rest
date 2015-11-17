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

from flask import Blueprint, current_app, request

from .errors import InvalidContentType
from .key_functions import key_per_user


def require_content_types(*allowed_content_types):
    """Decorator to test if proper content-type is provided."""
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if request.content_type not in allowed_content_types:
                raise InvalidContentType(allowed_content_types)
            return f(*args, **kwargs)
        return inner
    return decorator


def limit_per_user(app, limit_value, per_method=False, methods=None,
                   error_message=None, exempt_when=None, **kwargs):
    """Limit a route per user.

    Anonymous users get limited per IP address.
    """
    def decorator(f):
        """Decorate function with lazy limit registering."""
        if isinstance(app, Blueprint):
            before_first_request = app.before_app_first_request
        else:
            before_first_request = app.before_first_request

        @before_first_request
        def lazy_register():
            """Register a limit lazily to ensure Limiter has loaded."""
            return current_app.extensions['limiter'].limit(
                limit_value,
                key_per_user,
                per_method,
                methods,
                error_message,
                exempt_when,
                **kwargs
            )(f)

        return f

    return decorator
