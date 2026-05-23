# SPDX-FileCopyrightText: 2015-2019 CERN.
# SPDX-FileCopyrightText: 2025-2026 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""REST API serializers."""

import warnings

from marshmallow import Schema
from marshmallow_utils.context import context_schema


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
            category=PendingDeprecationWarning,
            stacklevel=2,
        )
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
            category=PendingDeprecationWarning,
            stacklevel=2,
        )
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


def _init_context(kwargs):
    """Init context_schema from kwargs only if context exists.

    Nested calls can't provide context, therefor they inherit the open context.
    """
    if "context" in kwargs:
        context = kwargs.pop("context")
        token = context_schema.set(context)
        return lambda: context_schema.reset(token)
    else:
        try:
            # nested calls of schema methods
            context_schema.get()
            return lambda: None
        except LookupError:
            # situation if a context_schema.get() is used but e.g. dump is not
            # called with a context parameter
            warnings.warn(
                "context_schema will in future only be set if and only if context is given.",
                category=DeprecationWarning,
                stacklevel=2,
            )

            token = context_schema.set({})
            return lambda: context_schema.reset(token)


class BaseSchema(Schema):
    """Base schema for all serializations."""

    def dump(self, obj, *args, **kwargs):
        """Wrap dump result for backward compatibility."""
        clear_context = _init_context(kwargs)
        try:
            result = super(BaseSchema, self).dump(obj, **kwargs)
            return result_wrapper(result)
        finally:
            clear_context()

    def dumps(self, obj, *args, **kwargs):
        """Wrap dumps result for backward compatibility."""
        clear_context = _init_context(kwargs)
        try:
            result = super(BaseSchema, self).dumps(obj, *args, **kwargs)
            return result_wrapper(result)
        finally:
            clear_context()

    def load(self, obj, *args, **kwargs):
        """Wrap load result for backward compatibility."""
        clear_context = _init_context(kwargs)
        try:
            result = super(BaseSchema, self).load(obj, *args, **kwargs)
            return result_wrapper(result)
        finally:
            clear_context()

    def loads(self, obj, *args, **kwargs):
        """Wrap loads result for backward compatibility."""
        clear_context = _init_context(kwargs)
        try:
            result = super(BaseSchema, self).loads(obj, *args, **kwargs)
            return result_wrapper(result)
        finally:
            clear_context()
