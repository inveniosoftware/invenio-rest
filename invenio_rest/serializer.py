# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API serializers."""

import warnings

from marshmallow import Schema


class MarshmalDict(dict):
    """Wrapping class for result of type dictionary."""

    def __init__(self, result):
        """Initialize MarshmalDict."""
        self.update(result)

    @property
    def data(self):
        """Substituting data property for backwards compatibility."""
        warnings.warn(
            "Schema().dump().data and Schema().dump().errors "
            "as well as Schema().load().data and Schema().loads().data"
            "attributes are deprecated in marshmallow v3.x.",
            category=PendingDeprecationWarning, stacklevel=2)
        return self


class MarshmalList(list):
    """Wrapping class for result of type list."""

    def __init__(self, result):
        """Initialize MarshmalList."""
        self.extend(result)

    @property
    def data(self):
        """Substituting data property for backwards compatibility."""
        warnings.warn(
            "Schema().dump().data and Schema().dump().errors "
            "as well as Schema().load().data and Schema().loads().data"
            "attributes are deprecated in marshmallow v3.x.",
            category=PendingDeprecationWarning, stacklevel=2)
        return self


def result_wrapper(result):
    """Wrap schema returned dump value."""
    if isinstance(result, tuple):
        return result
    elif isinstance(result, dict):
        return MarshmalDict(result)
    elif isinstance(result, list):
        return MarshmalList(result)
    return result


class BaseSchema(Schema):
    """Base schema for all serializations."""

    def dump(self, obj, *args, **kwargs):
        """Wrap dump result for backward compatibility."""
        result = super(BaseSchema, self).dump(obj, **kwargs)
        return result_wrapper(result)

    def dumps(self, obj, *args, **kwargs):
        """Wrap dumps result for backward compatibility."""
        result = super(BaseSchema, self).dumps(obj, *args, **kwargs)
        return result_wrapper(result)

    def load(self, obj, *args, **kwargs):
        """Wrap load result for backward compatibility."""
        result = super(BaseSchema, self).load(obj, *args, **kwargs)
        return result_wrapper(result)

    def loads(self, obj, *args, **kwargs):
        """Wrap loads result for backward compatibility."""
        result = super(BaseSchema, self).loads(obj, *args, **kwargs)
        return result_wrapper(result)
