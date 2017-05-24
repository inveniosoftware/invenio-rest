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

"""Tools for Dispatching requests to different applications."""

from werkzeug.http import parse_accept_header
from werkzeug.wrappers import Response


class AcceptType(object):
    """Parsed Accept Type from an Accept Header"""
    def __init__(self, mime, params=None, kwparams=None, quality=None):
        """Constructor.

        :param mime: mime type.
        :param params: accept type's positional parameters.
        :param kwparams: accept type's named parameters.
        :param quality: accept type's quality (see HTTP ACCEPT HEADER RFC).
        """
        self.mime = mime
        self.params = params
        self.kwparams = kwparams
        self.quality = quality

    def __str__(self):
        """Serialize as a valid accept type."""
        result = self.mime
        if self.params:
            result += ';{}'.format(';'.join(self.params))
        if self.kwparams:
            result += ';{}'.format(';'.join(['{0}={1}'.format(k, v) for k, v in
                                             self.kwparams.iteritems()]))
        if self.quality:
            result += ';q={}'.format(self.quality)
        return result


def parse_media_type(accept_type, quality):
    """Parse the provided accept_type.

    :param accept_type: accept type as returned by
    py:func::`werkzeug.http.parse_accept_header`.
    :param quality: accept type's quality.

    :return: the parsed py:class::`AcceptType`.
    """
    elements = [elt.strip() for elt in accept_type.split(';')]
    mime = elements[0]
    elements = elements[1:]
    params = []
    kwparams = {}
    for elt in elements:
        if '=' in elt:
            key, value = elt.split('=')
            kwparams[key.strip()] = value.strip()
        else:
            params = elt
    return AcceptType(mime, params, kwparams, quality)


class HTTPAcceptDispatcherMiddleware(object):
    """Application Dispatcher filtering on request's Accept Header."""

    def __init__(self, dispatch_function=None,
                 accept_header_rewriter=None, *args):
        """Constructor.

        :param dispatch_function: function used to dispatch the requests. It
        will receive a list of py:class::`AcceptType` as argument.
        :param accept_header_rewriter: function used to rewrite the accept.
        header once an application has been chosen.
        :param *args: additional arguments forwarded to the dispatch function.
        """

        self.dispatch_function = dispatch_function
        self.accept_header_rewriter = accept_header_rewriter
        self.args = args

    def __call__(self, environ, start_response):
        """Dispatch a request.

        :param environ: request environment.
        :param start_response: used to send the request's response.
        """
        accept_header = environ.get('HTTP_ACCEPT')
        if accept_header is None:
            app = self.dispatch_function(self.default_app,
                                         *(self.args))
            if self.accept_header_rewriter is not None:
                environ['HTTP_ACCEPT'] = self.accept_header_rewriter([])
            return app(environ, start_response)
        else:
            # parse all accept headers
            parsed_accept = [parse_media_type(type, quality)
                             for type, quality in
                             parse_accept_header(accept_header)]
            # use the dispatcher to find the right application
            for accept_type in parsed_accept:
                app = self.dispatch_function(accept_type,
                                             *(self.args))
                if app is not None:
                    if self.accept_header_rewriter is not None:
                        # overwrite the HTTP_ACCEPT header
                        environ['HTTP_ACCEPT'] = \
                            ','.join([str(a) for a in
                                      self.accept_header_rewriter(
                                          accept_type,
                                          parsed_accept,
                                          *(self.args))])
                    return app(environ, start_response)
        # if no application matchs the given accept header, return 406 error
        response = Response(
            '{ "message": "Not Acceptable", "status_code": 406 }',
            mimetype='appliction/json')
        response.status_code = 406
        return response(environ, start_response)


def dispatch_by_http_accept_parameter(parameter, default_app, mapping):
    """Factory of application dispatchers using HTTPAccept parameters.

    :param parameter: Accept type's parameter name used for the dispatch. Can
    be None if the Accept header is empty.
    :param default_app: parameter's value corresponding to the default
    application returned when the parameter is not set in the given
    accept_type.
    :param mapping: dict of parameter value -> application used for dispatch.

    :return: the application which should handle the request, or None if the
    given accept_type has
    """

    default = mapping.get(default_app)

    def dispatch_function(accept_type=None):
        """Choose the application which should handle the given accept type.

        :param accept_type: accept type used to choose the application which
        should process the request.
        """
        if not accept_type or parameter not in accept_type.kwparams:
            return default
        else:
            return mapping.get(accept_type.kwparams[parameter])
    return dispatch_function


def parametrized_http_accept_rewriter(parameter):
    """Filter Accept Header using the parameter and accepted accept type.

    This factory builds functions which can remove all accept types containing
    a parameter value different from the accepted type one. It also removes
    the parameter from all accept types.

    Example:
    .. code-block::
        Parameter: 'version'
        Accept Header: 'text/html; version=1, text/plain; version=1; q=2, \
            application/*; version=2'
        Accepted type: 'text/html; version=1'

        Returned Header: 'text/html,text/plain;q=2' because the version match

    This can be used for API versioning. It can keep only the media types
    corresponding to the chosen API version.

    :param parameter: the accept type parameter used for filtering
    """
    def rewriter(accepted_type, accept_header):
        dispatch_value = accepted_type.kwparams.get(parameter)
        new_accept_header = []
        for accept in accept_header:
            if accept.kwparams.get(parameter) == dispatch_value:
                if parameter in accept.kwparams:
                    del accept.kwparams[parameter]
                new_accept_header.append(accept)
        return new_accept_header
    return rewriter
