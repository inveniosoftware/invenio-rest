# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2021      TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API module for Invenio."""

from __future__ import absolute_import, print_function

from datetime import timezone

import sentry_sdk
from flask import Response, abort, current_app, g, jsonify, make_response, request
from flask.views import MethodView
from werkzeug.exceptions import HTTPException

from .errors import RESTException, SameContentException


def create_api_errorhandler(**kwargs):
    r"""Create an API error handler.

    E.g. register a 404 error:

    .. code-block:: python

        app.errorhandler(404)(create_api_errorhandler(
            status=404, message='Not Found'))

    :param \*\*kwargs: It contains the ``'status'`` and the ``'message'``
        to describe the error.
    """

    def api_errorhandler(e):
        if isinstance(e, RESTException):
            return e.get_response()
        elif isinstance(e, HTTPException) and e.description:
            kwargs["message"] = e.description
        if kwargs.get("status", 400) >= 500:
            sentry_event_id = sentry_sdk.last_event_id()
            if sentry_event_id:
                kwargs["error_id"] = str(sentry_event_id)
        return make_response(jsonify(kwargs), kwargs["status"])

    return api_errorhandler


class ContentNegotiatedMethodView(MethodView):
    """MethodView with content negotiation.

    Dispatch HTTP requests as MethodView does and build responses using the
    registered serializers. It chooses the right serializer using the request's
    accept type. It also provides a helper method for handling ETags.
    """

    def __init__(
        self,
        serializers=None,
        method_serializers=None,
        serializers_query_aliases=None,
        default_media_type=None,
        default_method_media_type=None,
        *args,
        **kwargs
    ):
        """Register the serializing functions.

        Serializing functions will receive all named and non named arguments
        provided to ``make_response`` or returned by request handling methods.
        Recommended prototype is: ``serializer(data, code=200, headers=None)``
        and it should return :class:`flask.Response` instances.

        Serializing functions can also be overridden by setting
        ``self.serializers``.

        :param serializers: A mapping from mediatype to a serializer function.
        :param method_serializers: A mapping of HTTP method name (GET, PUT,
            PATCH, POST, DELETE) -> dict(mediatype -> serializer function). If
            set, it overrides the serializers dict.
        :param serializers_query_aliases: A mapping of values of the defined
            query arg (see `config.REST_MIMETYPE_QUERY_ARG_NAME`) to valid
            mimetypes: dict(alias -> mimetype).
        :param default_media_type: Default media type used if no accept type
            has been provided and global serializers are used for the request.
            Can be None if there is only one global serializer or None. This
            media type is used for method serializers too if
            ``default_method_media_type`` is not set.
        :param default_method_media_type: Default media type used if no accept
            type has been provided and a specific method serializers are used
            for the request. Can be ``None`` if the method has only one
            serializer or ``None``.
        """
        super(ContentNegotiatedMethodView, self).__init__(*args, **kwargs)
        self.serializers = serializers or None
        self.default_media_type = default_media_type
        self.default_method_media_type = default_method_media_type or {}

        # set default default media_types if none has been given
        if self.serializers and not self.default_media_type:
            if len(self.serializers) == 1:
                self.default_media_type = next(iter(self.serializers.keys()))
            elif len(self.serializers) > 1:
                raise ValueError("Multiple serializers with no default media" " type")
        # set method serializers
        self.method_serializers = (
            {key.upper(): func for key, func in method_serializers.items()}
            if method_serializers
            else {}
        )
        # set serializer aliases
        self.serializers_query_aliases = serializers_query_aliases or {}
        # create default method media_types dict if none has been given
        if self.method_serializers and not self.default_method_media_type:
            self.default_method_media_type = {}
            for http_method, meth_serial in self.method_serializers.items():
                if len(self.method_serializers[http_method]) == 1:
                    self.default_method_media_type[http_method] = next(
                        iter(self.method_serializers[http_method].keys())
                    )
                elif len(self.method_serializers[http_method]) > 1:
                    # try to use global default media type
                    if default_media_type in self.method_serializers[http_method]:
                        self.default_method_media_type[http_method] = default_media_type
                    else:
                        raise ValueError(
                            "Multiple serializers for method {0}"
                            "with no default media type".format(http_method)
                        )

    def get_method_serializers(self, http_method):
        """Get request method serializers + default media type.

        Grab serializers from ``method_serializers`` if defined, otherwise
        returns the default serializers. Uses GET serializers for HEAD requests
        if no HEAD serializers were specified.

        The method also determines the default media type.

        :param http_method: HTTP method as a string.
        :returns: Tuple of serializers and default media type.
        """
        if http_method == "HEAD" and "HEAD" not in self.method_serializers:
            http_method = "GET"

        return (
            self.method_serializers.get(http_method, self.serializers),
            self.default_method_media_type.get(http_method, self.default_media_type),
        )

    def _match_serializers_by_query_arg(self, serializers):
        """Match serializer by query arg."""
        # if the format query argument is present, match the serializer
        arg_name = current_app.config.get("REST_MIMETYPE_QUERY_ARG_NAME")
        if arg_name:
            arg_value = request.args.get(arg_name, None)

            if arg_value is None:
                return None
            # Search for the serializer matching the format
            try:
                return serializers[self.serializers_query_aliases[arg_value]]
            except KeyError:  # either no serializer for this format
                return None

        return None

    def _match_serializers_by_accept_headers(self, serializers, default_media_type):
        """Match serializer by `Accept` headers."""
        # Bail out fast if no accept headers were given.
        if len(request.accept_mimetypes) == 0:
            return serializers[default_media_type]

        # Determine best match based on quality.
        best_quality = -1
        best = None
        has_wildcard = False
        for client_accept, quality in request.accept_mimetypes:
            if quality <= best_quality:
                continue
            if client_accept == "*/*":
                has_wildcard = True
            for s in serializers:
                if s in ["*/*", client_accept] and quality > 0:
                    best_quality = quality
                    best = s

        # If no match found, but wildcard exists, them use default media
        # type.
        if best is None and has_wildcard:
            best = default_media_type

        if best is not None:
            return serializers[best]
        return None

    def match_serializers(self, serializers, default_media_type):
        """Choose serializer for a given request based on query arg or headers.

        Checks if query arg `format` (by default) is present and tries to match
        the serializer based on the arg value, by resolving the mimetype mapped
        to the arg value.
        Otherwise, chooses the serializer by retrieving the best quality
        `Accept` headers and matching its value (mimetype).

        :param serializers: Dictionary of serializers.
        :param default_media_type: The default media type.
        :returns: Best matching serializer based on `format` query arg first,
            then client `Accept` headers or None if no matching serializer.
        """
        return self._match_serializers_by_query_arg(
            serializers
        ) or self._match_serializers_by_accept_headers(serializers, default_media_type)

    def make_response(self, *args, **kwargs):
        """Create a Flask Response.

        Dispatch the given arguments to the serializer best matching the
        current request's Accept header.

        :return: The response created by the serializing function.
        :rtype: :class:`flask.Response`
        :raises werkzeug.exceptions.NotAcceptable: If no media type
            matches current Accept header.
        """
        serializer = self.match_serializers(
            *self.get_method_serializers(request.method)
        )

        if serializer:
            return serializer(*args, **kwargs)
        abort(406)

    def dispatch_request(self, *args, **kwargs):
        """Dispatch current request.

        Dispatch the current request using
        :class:`flask.views.MethodView` `dispatch_request()` then, if the
        result is not already a :py:class:`flask.Response`, search for the
        serializing function which matches the best the current request's
        Accept header and use it to build the :py:class:`flask.Response`.

        :rtype: :class:`flask.Response`
        :raises werkzeug.exceptions.NotAcceptable: If no media type matches
            current Accept header.
        :returns: The response returned by the request handler or created by
            the serializing function.
        """
        result = super(ContentNegotiatedMethodView, self).dispatch_request(
            *args, **kwargs
        )

        if isinstance(result, Response):
            return result
        elif isinstance(result, (list, tuple)):
            return self.make_response(*result)
        else:
            return self.make_response(result)

    def check_etag(self, etag, weak=False):
        """Validate the given ETag with current request conditions.

        Compare the given ETag to the ones in the request header If-Match
        and If-None-Match conditions.

        The result is unspecified for requests having If-Match and
        If-None-Match being both set.

        :param str etag: The ETag of the current resource. For PUT and PATCH
            it is the one before any modification of the resource. This ETag
            will be tested with the Accept header conditions. The given ETag
            should not be quoted.
        :raises werkzeug.exceptions.PreconditionFailed: If the
            condition is not met.
        :raises invenio_rest.errors.SameContentException: If the
            the request is GET or HEAD and the If-None-Match condition is not
            met.
        """
        # bool(:py:class:`werkzeug.datastructures.ETags`) is not consistent
        # in Python 3. bool(Etags()) == True even though it is empty.
        if (
            len(request.if_match.as_set(include_weak=weak)) > 0
            or request.if_match.star_tag
        ):
            contains_etag = (
                request.if_match.contains_weak(etag)
                if weak
                else request.if_match.contains(etag)
            )
            if not contains_etag and "*" not in request.if_match:
                abort(412)
        if (
            len(request.if_none_match.as_set(include_weak=weak)) > 0
            or request.if_none_match.star_tag
        ):
            contains_etag = (
                request.if_none_match.contains_weak(etag)
                if weak
                else request.if_none_match.contains(etag)
            )
            if contains_etag or "*" in request.if_none_match:
                if request.method in ("GET", "HEAD"):
                    raise SameContentException(etag)
                else:
                    abort(412)

    def check_if_modified_since(self, dt, etag=None):
        """Validate If-Modified-Since with current request conditions."""
        dt = dt.replace(microsecond=0)

        # since Werkzeug v2.0, request-related datetime values are
        # timezone-aware, which compared dates to be timezone-aware as well
        if (
            request.if_modified_since
            and request.if_modified_since.tzinfo
            and not dt.tzinfo
        ):
            dt = dt.replace(tzinfo=timezone.utc)

        if request.if_modified_since and dt <= request.if_modified_since:
            raise SameContentException(etag, last_modified=dt)
