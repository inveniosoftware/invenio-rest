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


"""Module tests."""

from __future__ import absolute_import, print_function

import json
from datetime import datetime

import pkg_resources
import pytest
from flask import Flask, abort, make_response, request
from flask.json import jsonify
from mock import patch
from werkzeug.http import quote_etag, unquote_etag

from invenio_rest import ContentNegotiatedMethodView, InvenioREST
from invenio_rest.errors import RESTException


def test_version():
    """Test version import."""
    from invenio_rest import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioREST(app)
    assert 'invenio-rest' in app.extensions

    app = Flask('testapp')
    ext = InvenioREST()
    assert 'invenio-rest' not in app.extensions
    ext.init_app(app)
    assert 'invenio-rest' in app.extensions


def test_error_handlers(app):
    """Error handlers view."""
    InvenioREST(app)

    @app.route("/<int:status_code>",
               methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD',
                        'TRACE', 'OPTIONS'])
    def test_view(status_code):
        abort(status_code)

    error_codes = [
        400, 401, 403, 404, 405, 406, 409, 410, 412, 422, 415, 429, 500, 501,
        502, 503, 504]

    with app.test_client() as client:
        verbs = [client.get, client.post, client.put, client.delete,
                 client.patch, client.trace, client.options, client.get]
        for s in error_codes:
            for verb in verbs:
                res = verb("/{0}".format(s))
                assert res.status_code == s
                if verb != client.head:
                    data = json.loads(res.get_data(as_text=True))
                    assert data['status'] == s
                    assert data['message']


def test_custom_httpexception(app):
    """Test custom RESTException."""
    InvenioREST(app)

    class CustomBadRequest(RESTException):
        code = 400
        description = 'test'

    @app.route('/')
    def test_view():
        raise CustomBadRequest()

    with app.test_client() as client:
        res = client.get('/')
        assert res.status_code == 400
        data = json.loads(res.get_data(as_text=True))
        assert data['message'] == 'test'
        assert data['status'] == 400


def test_cors_loading(app):
    """Test CORS support."""
    app.config['REST_ENABLE_CORS'] = True

    with patch('flask_cors.CORS') as CORS:
        CORS.side_effect = pkg_resources.DistributionNotFound
        pytest.raises(RuntimeError, InvenioREST, app)


def test_cors(app):
    """Test CORS support."""
    app.config['REST_ENABLE_CORS'] = True
    app.config['CORS_ALWAYS_SEND'] = False

    InvenioREST(app)

    @app.route('/')
    def cors_test():
        return 'test'

    with app.test_client() as client:
        res = client.get('/')
        assert not res.headers.get('Access-Control-Allow-Origin', False)
        assert not res.headers.get('Access-Control-Expose-Headers', False)
        res = client.get('/', headers=[('Origin', 'http://example.com')])
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert len(res.headers['Access-Control-Expose-Headers'].split(',')) \
            == len(app.config['CORS_EXPOSE_HEADERS'])


def _obj_to_json_serializer(data, code=200, headers=None):
    if data:
        res = jsonify(data)
        res.set_etag('abc')
    else:
        res = make_response()
    res.status_code = code
    return res


class _ObjectItem(ContentNegotiatedMethodView):
    view_name = 'object_item'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(_ObjectItem, self).__init__(*args, **kwargs)
        self.modified = datetime.utcnow()

    def get(self, id, **kwargs):
        """GET a resource."""
        self.check_etag('abc', weak='weak_etags' in request.args)
        self.check_if_modified_since(self.modified)
        if id == 42:
            abort(404)
        # return {'id': id, 'method': 'GET'}, 200
        res = self.make_response({'id': id, 'method': 'GET'}, 200)
        res.last_modified = self.modified
        return res

    def put(self, id, **kwargs):
        """PUT a resource."""
        self.check_etag('abc', weak='weak_etags' in request.args)
        if id == 42:
            return self.make_response(None, code=404)
        return self.make_response({'id': id, 'method': 'PUT'}, 200)

    def patch(self, id, **kwargs):
        """PATCH a resource."""
        self.check_etag('abc', weak='weak_etags' in request.args)
        if id == 42:
            return None, 404
        return self.make_response({'id': id, 'method': 'PATCH'})

    def post(self, id, **kwargs):
        """POST a resource."""
        self.check_etag('abc', weak='weak_etags' in request.args)
        if id == 42:
            abort(404)
        return {'id': id, 'method': 'POST'}

    def delete(self, id, **kwargs):
        """DELETE a resource."""
        self.check_etag('abc', weak='weak_etags' in request.args)
        if id == 42:
            abort(404)
        return {'id': id, 'method': 'DELETE'}


def test_content_negotiation_method_view_global_serializers(app):
    """Test ContentNegotiationMethodView. Test default serializers."""
    _subtest_content_negotiation_method_view(app, _ObjectItem, params={
        'serializers': {
            'application/json': _obj_to_json_serializer,
        }
    })


def test_content_negotiation_method_view_method_serializers(app):
    """Test method serializers with no global serializers."""
    _subtest_content_negotiation_method_view(app, _ObjectItem, params={
        'method_serializers': {
            'GET': {'application/json': _obj_to_json_serializer, },
            'PUT': {'application/json': _obj_to_json_serializer, },
            'POST': {'application/json': _obj_to_json_serializer, },
            'PATCH': {'application/json': _obj_to_json_serializer, },
            'DELETE': {'application/json': _obj_to_json_serializer, },
        }
    })


def test_content_negotiation_method_view_method_serializers_2(app):
    """Check that method serializers override global ones."""
    def failing_serializer(data, code=200, headers=None):
        raise Exception('Method serializer was not called.')

    _subtest_content_negotiation_method_view(app, _ObjectItem, params={
        'serializers': {
            'application/json': failing_serializer,
        },
        'method_serializers': {
            'GET': {'application/json': _obj_to_json_serializer, },
            'PUT': {'application/json': _obj_to_json_serializer, },
            'POST': {'application/json': _obj_to_json_serializer, },
            'PATCH': {'application/json': _obj_to_json_serializer, },
            'DELETE': {'application/json': _obj_to_json_serializer, },
        }
    })


def test_content_negotiation_method_view_mixed_serializers(app):
    """Test ContentNegotiationMethodView. Test partial method serializers"""
    _subtest_content_negotiation_method_view(app, _ObjectItem, params={
        'serializers': {
            'application/json': _obj_to_json_serializer,
        },
        'method_serializers': {
            'GET': {'application/json': _obj_to_json_serializer, },
            'PUT': {'application/json': _obj_to_json_serializer, },
        }
    })


def test_default_media_type(app):
    """Test setting default media type."""
    def failing_serializer(data, code=200, headers=None):
        raise Exception('Wrong serializer was called.')
    _subtest_content_negotiation_method_view(app, _ObjectItem, params={
        'serializers': {
            'application/mpeg': failing_serializer,
            'application/json': _obj_to_json_serializer,
        },
        'default_media_type': 'application/json'
    })


def test_default_media_type_for_all_methods(app):
    """Test setting default serializer for all methods."""
    def failing_serializer(data, code=200, headers=None):
        raise Exception('Wrong method serializer was called.')
    _subtest_content_negotiation_method_view(app, _ObjectItem, params={
        'method_serializers': {
            'GET': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'PUT': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'POST': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'PATCH': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'DELETE': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
        },
        'default_media_type': 'application/json'
    })


def test_default_method_media_type(app):
    """Test setting default media type for each method."""
    def failing_serializer(data, code=200, headers=None):
        raise Exception('Wrong method serializer was called.')
    _subtest_content_negotiation_method_view(app, _ObjectItem, params={
        'method_serializers': {
            'GET': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'PUT': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'POST': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'PATCH': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
            'DELETE': {
                'application/json': _obj_to_json_serializer,
                'application/mpeg': failing_serializer,
            },
        },
        'default_method_media_type': {
            'GET': 'application/json',
            'PUT': 'application/json',
            'POST': 'application/json',
            'PATCH': 'application/json',
            'DELETE': 'application/json',
        },
        'default_media_type': 'application/doesnotexist'
    })


def test_default_method_media_type_error(app):
    """Test that there is an error when multiple serializers are given with no
    default media type.
    """
    with pytest.raises(ValueError):
        _ObjectItem(
            method_serializers={
                'GET': {
                    'application/json': _obj_to_json_serializer,
                    'application/json-patch+json': _obj_to_json_serializer,
                },
                'PUT': {
                    'application/json': _obj_to_json_serializer,
                    'application/json-patch+json': _obj_to_json_serializer,
                },
                'POST': {
                    'application/json': _obj_to_json_serializer,
                    'application/json-patch+json': _obj_to_json_serializer,
                },
                'PATCH': {
                    'application/json': _obj_to_json_serializer,
                    'application/json-patch+json': _obj_to_json_serializer,
                },
                'DELETE': {
                    'application/json': _obj_to_json_serializer,
                    'application/json-patch+json': _obj_to_json_serializer,
                },
            },
        )


def test_default_media_type_error(app):
    """Test that there is an error when multiple serializers are given with no
    default media type.
    """
    with pytest.raises(ValueError):
        _ObjectItem(serializers={
            'application/json': _obj_to_json_serializer,
            'application/json-patch+json': _obj_to_json_serializer,
        })


def test_get_method_serializers(app):
    """Test get request method serializers."""
    v = ContentNegotiatedMethodView(
        method_serializers=dict(
            DELETE={'*/*': 'any-delete', },
            GET={'text/plain': 'plain-get', 'text/html': 'html-get'},
            POST={'text/plain': 'plain-post', 'text/html': 'html-post'}
        ),
        serializers={
            'text/plain': 'plain',
            'text/html': 'html',
        },
        default_media_type='application/json',
        default_method_media_type=dict(
            GET='text/plain',
            POST='text/html',
        )
    )
    # Default serializers
    assert v.get_method_serializers('GET')[0] == v.method_serializers['GET']
    assert v.get_method_serializers('HEAD')[0] == v.method_serializers['GET']
    assert v.get_method_serializers('POST')[0] == v.method_serializers['POST']
    assert v.get_method_serializers('PUT')[0] == v.serializers

    # Default media type
    assert v.get_method_serializers('GET')[1] == \
        v.default_method_media_type['GET']
    assert v.get_method_serializers('HEAD')[1] == \
        v.default_method_media_type['GET']
    assert v.get_method_serializers('POST')[1] == \
        v.default_method_media_type['POST']
    assert v.get_method_serializers('PUT')[1] == v.default_media_type

    assert v.get_method_serializers('DELETE')[0] == \
        v.method_serializers['DELETE']


def test_match_serializers(app):
    """Test match serializers."""
    v = ContentNegotiatedMethodView(
        method_serializers=dict(
            DELETE={
                '*/*': 'any-delete',
            },
            GET={
                'application/json': 'json-get',
                'application/marcxml+xml': 'xml-get'},
            POST={
                'application/json': 'json-post',
                'application/marcxml+xml': 'xml-post'}
        ),
        serializers={
            'application/json': 'json',
            'application/marcxml+xml': 'xml',
        },
        default_media_type='application/json',
        default_method_media_type=dict(
            GET='application/json',
            POST='application/marcxml+xml',
        )
    )

    tests = [
        # Should choose application/json
        ('text/plain,application/json,*/*', 'GET', 'json-get'),
        ('text/plain,application/json,*/*', 'HEAD', 'json-get'),
        ('text/plain,application/json,*/*', 'POST', 'json-post'),
        ('text/plain,application/json,*/*', 'PUT', 'json'),
        # Should choose application/json (even with lower quality)
        ('text/plain,application/json; q=0.5, */*', 'GET', 'json-get'),
        ('text/plain,application/json; q=0.5, */*', 'HEAD', 'json-get'),
        ('text/plain,application/json; q=0.5, */*', 'POST', 'json-post'),
        ('text/plain,application/json; q=0.5, */*', 'PUT', 'json'),
        # Should choose application/marcxml+xml
        ('text/plain,application/marcxml+xml,*/*', 'GET', 'xml-get'),
        ('text/plain,application/marcxml+xml,*/*', 'HEAD', 'xml-get'),
        ('text/plain,application/marcxml+xml,*/*', 'POST', 'xml-post'),
        ('text/plain,application/marcxml+xml,*/*', 'PUT', 'xml'),
        # Should choose default defined by default_media_type and
        # default_method_media_type
        ('text/plain,*/*', 'GET', 'json-get'),
        ('text/plain,*/*', 'HEAD', 'json-get'),
        ('text/plain,*/*', 'POST', 'xml-post'),
        ('text/plain,*/*', 'PUT', 'json'),
        # Should choose none
        ('text/plain', 'GET', None),
        ('text/plain', 'HEAD', None),
        ('text/plain', 'POST', None),
        ('text/plain', 'PUT', None),
        # Should choose default
        (None, 'GET', 'json-get'),
        (None, 'HEAD', 'json-get'),
        (None, 'POST', 'xml-post'),
        (None, 'PUT', 'json'),
        # Should choose application/json
        ('application/json', 'GET', 'json-get'),
        # Should choose highest quality
        ('application/json; q=0.5, application/marcxml+xml', 'GET', 'xml-get'),
        ('application/json, application/marcxml+xml; q=0.5', 'GET',
         'json-get'),
        ('application/json; q=0.4, application/marcxml+xml; q=0.6', 'GET',
         'xml-get'),
        ('application/marcxml+xml; q=0.6, application/json; q=0.4', 'GET',
         'xml-get'),
        # Test delete
        ('application/marcxml+xml; q=0.6, application/json; q=0.4', 'DELETE',
         'any-delete'),
        ('video/mp4', 'DELETE', 'any-delete'),
    ]

    for accept, method, expected_serializer in tests:
        params = dict(headers=[('Accept', accept)]) if accept else {}
        with app.test_request_context(**params):
            assert v.match_serializers(*v.get_method_serializers(method)) == \
                expected_serializer, "Accept: {0}, Method: {1}".format(
                    accept, method)


def _subtest_content_negotiation_method_view(app, content_negotiated_class,
                                             params):
    """Test a given ContentNegotiatedMethodView subclass."""
    app.add_url_rule('/objects/<int:id>',
                     view_func=content_negotiated_class
                     .as_view(content_negotiated_class.view_name,
                              **params))

    with app.test_client() as client:
        read_methods = [client.get, client.head]
        write_methods = [client.patch, client.put, client.post, client.delete]
        all_methods = read_methods + write_methods
        method_names = {
            'GET': client.get,
            'POST': client.post,
            'PUT': client.put,
            'PATCH': client.patch,
            'DELETE': client.delete,
        }

        def check_normal_response(res, method):
            if method != client.head:
                parsed = json.loads(res.get_data(as_text=True))
                expected = {'id': 1, 'method': parsed['method']}
                assert parsed == expected
                # check that the right method was called
                assert method_names[parsed['method']] == method
                assert res.content_type == 'application/json'
            assert res.status_code == 200
            # check that the ETag is correct
            assert unquote_etag(res.headers['ETag']) == \
                unquote_etag(quote_etag('abc'))

        def check_304_response(res):
            assert res.status_code == 304
            # check that the ETag is correct
            assert unquote_etag(res.headers['ETag']) == \
                unquote_etag(quote_etag('abc'))

        # check valid call with condition
        headers = [('Accept', 'application/json')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            check_normal_response(res, method)

        # check valid call without condition
        for method in all_methods:
            res = method('/objects/1')
            check_normal_response(res, method)

        # check that non accepted mime types are not accepted
        headers = [('Accept', 'application/xml')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            assert res.status_code == 406

        # check that errors are forwarded properly
        headers = [('Accept', 'application/json')]
        for method in all_methods:
            res = method('/objects/42', headers=headers)
            assert res.status_code == 404

        # check Matching If-None-Match
        headers_nonmatch_match = [('Accept', 'application/json'),
                                  ('If-None-Match', '"xyz", "abc"')]
        headers_nonmatch_star = [('Accept', 'application/json'),
                                 ('If-None-Match', '"xyz", "*"')]
        for method in read_methods:
            res = method('/objects/1', headers=headers_nonmatch_match)
            check_304_response(res)
            res = method('/objects/1', headers=headers_nonmatch_star)
            check_304_response(res)

        for method in write_methods:
            res = method('/objects/1', headers=headers_nonmatch_match)
            assert res.status_code == 412
            res = method('/objects/1', headers=headers_nonmatch_star)
            assert res.status_code == 412

        # check Matching If-None-Match with weak ETags
        headers_nonmatch_match = [('Accept', 'application/json'),
                                  ('If-None-Match', 'W/"xyz", W/"abc"')]
        headers_nonmatch_star = [('Accept', 'application/json'),
                                 ('If-None-Match', 'W/"xyz", "*"')]
        query_string_weak_etags = {'weak_etags': True}
        for method in read_methods:
            res = method('/objects/1',
                         headers=headers_nonmatch_match,
                         query_string=query_string_weak_etags)
            check_304_response(res)
            res = method('/objects/1',
                         headers=headers_nonmatch_star,
                         query_string=query_string_weak_etags)
            check_304_response(res)

        for method in write_methods:
            res = method('/objects/1',
                         headers=headers_nonmatch_match,
                         query_string=query_string_weak_etags)
            assert res.status_code == 412
            res = method('/objects/1',
                         headers=headers_nonmatch_star,
                         query_string=query_string_weak_etags)
            assert res.status_code == 412

        # check non matching If-None-Match
        headers = [('Accept', 'application/json'),
                   ('If-None-Match', '"xyz", "def"')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            check_normal_response(res, method)

        # check non matching If-None-Match with weak ETags
        headers = [('Accept', 'application/json'),
                   ('If-None-Match', 'W/"xyz", W/"def"')]
        query_string_weak_etags = {'weak_etags': True}
        for method in all_methods:
            res = method('/objects/1',
                         headers=headers,
                         query_string=query_string_weak_etags)
            check_normal_response(res, method)

        # check matching If-Match
        headers = [('Accept', 'application/json'),
                   ('If-Match', '"abc", "def"')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            check_normal_response(res, method)

        # check matching If-Match with weak ETags
        headers = [('Accept', 'application/json'),
                   ('If-Match', 'W/"abc", W/"def"')]
        query_string_weak_etags = {'weak_etags': True}
        for method in all_methods:
            res = method('/objects/1',
                         headers=headers,
                         query_string=query_string_weak_etags)
            check_normal_response(res, method)

        # check non matching If-Match
        headers = [('Accept', 'application/json'),
                   ('If-Match', '"xyz", "def"')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            assert res.status_code == 412

        # check non matching If-Match with weak ETags
        headers = [('Accept', 'application/json'),
                   ('If-Match', 'W/"xyz", W/"def"')]
        query_string_weak_etags = {'weak_etags': True}
        for method in all_methods:
            res = method('/objects/1',
                         headers=headers,
                         query_string=query_string_weak_etags)
            assert res.status_code == 412

        # check If-Modified-Since
        res = client.get('/objects/1')
        last_modified = res.headers['Last-Modified']
        res = client.get(
            '/objects/1', headers={'If-Modified-Since': last_modified})
        assert res.status_code == 304
