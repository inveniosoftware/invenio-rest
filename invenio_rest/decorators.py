# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
