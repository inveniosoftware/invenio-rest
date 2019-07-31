# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API serializers."""

import warnings

from marshmallow import Schema, fields, missing


class MarshalResultBase(object):
    """Wrapper class to provide backward compatibility with marshmallow 2."""

    def __new__(cls, result, errors=None, *args, **kwargs):
        """Instanciate Marshal Result class."""
        def data(self):
            warnings.warn(
                "Schema().dump().data and Schema().dump().errors attributes "
                "are deprecated in marshmallow v3.x. Use .dump() "
                "and error handler instead.",
                category=PendingDeprecationWarning, stacklevel=2)
            return result

        setattr(cls, 'data', property(data))
        return super(MarshalResultBase, cls).__new__(
            cls, result, errors, *args, **kwargs)

    def __init__(self, result):
        """Initialize MarshalResult."""
        super(MarshalResultBase, self).__init__(result)


def dump_wrapper(result):
    """Wrap schema returned dump value."""
    if isinstance(result, tuple):
        return result
    MarshalResult = type('MarshalResult',
                         (MarshalResultBase, type(result)), {})
    return MarshalResult(result)


class BaseSchema(Schema):
    """Base schema for all serializations."""

    def dump(self, obj, many=None, update_fields=True, **kwargs):
        """Wrap dump result for backward compatibility."""
        result = super(BaseSchema, self).dump(obj, many=many, **kwargs)
        return dump_wrapper(result)

    def dumps(self, obj, many=None, update_fields=True, *args, **kwargs):
        """Wrap dumps result for backward compatibility."""
        result = super(BaseSchema, self).dumps(obj, *args, many=many, **kwargs)
        return dump_wrapper(result)
