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


"""Module tests."""

from __future__ import absolute_import, print_function

import json

import pkg_resources
import pytest
from flask import Flask, abort, make_response
from flask.json import jsonify
from mock import patch
from werkzeug.exceptions import HTTPException
from werkzeug.http import quote_etag, unquote_etag

from invenio_rest import ContentNegotiatedMethodView, InvenioREST


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
        400, 401, 403, 404, 405, 406, 409, 410, 412, 415, 429, 500, 501, 502,
        503, 504]

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
    """Test custom HTTPException."""
    InvenioREST(app)

    class CustomBadRequest(HTTPException):
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
    InvenioREST(app)

    @app.route('/')
    def cors_test():
        return 'test'

    with app.test_client() as client:
        res = client.get('/')
        assert not res.headers.get('Access-Control-Allow-Origin', False)
        res = client.get('/', headers=[('Origin', 'http://example.com')])
        assert res.headers['Access-Control-Allow-Origin'] == '*'


def test_ratelimt(app):
    """Test CORS support."""
    app.config['RATELIMIT_GLOBAL'] = '1/day'
    app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
    ext = InvenioREST(app)

    for handler in app.logger.handlers:
        ext.limiter.logger.addHandler(handler)

    @app.route('/a')
    def view_a():
        return 'a'

    @app.route('/b')
    def view_b():
        return 'b'

    with app.test_client() as client:
        res = client.get('/a')
        assert res.status_code == 200
        assert res.headers['X-RateLimit-Limit'] == '1'
        assert res.headers['X-RateLimit-Remaining'] == '0'
        assert res.headers['X-RateLimit-Reset']

        res = client.get('/a')
        assert res.status_code == 429
        assert res.headers['X-RateLimit-Limit']
        assert res.headers['X-RateLimit-Remaining']
        assert res.headers['X-RateLimit-Reset']

        # Global limit is per view.
        res = client.get('/b')
        assert res.status_code == 200
        assert res.headers['X-RateLimit-Limit']
        assert res.headers['X-RateLimit-Remaining']
        assert res.headers['X-RateLimit-Reset']


def test_content_negotiation_method_view(app):
    """Test ContentNegotiationMethodView."""
    def obj_to_json_serializer(data, code=200, headers=None):
        if data:
            res = jsonify(data)
            res.set_etag('abc')
        else:
            res = make_response()
        res.status_code = code
        return res

    class ObjectItem(ContentNegotiatedMethodView):
        view_name = 'object_item'

        def __init__(self, *args, **kwargs):
            super(ObjectItem, self).__init__(serializers={
                'application/json': obj_to_json_serializer,
            }, *args, **kwargs)

        def get(self, id, **kwargs):
            self.check_etag('abc')
            if id == 42:
                abort(404)
            return {'id': id, 'method': 'GET'}, 200

        def put(self, id, **kwargs):
            self.check_etag('abc')
            if id == 42:
                return self.make_response(None, code=404)
            return self.make_response({'id': id, 'method': 'PUT'}, 200)

        def patch(self, id, **kwargs):
            self.check_etag('abc')
            if id == 42:
                return None, 404
            return self.make_response({'id': id, 'method': 'PATCH'})

        def post(self, id, **kwargs):
            self.check_etag('abc')
            if id == 42:
                abort(404)
            return {'id': id, 'method': 'POST'}

    app.add_url_rule('/objects/<int:id>',
                     view_func=ObjectItem
                     .as_view(ObjectItem.view_name))

    with app.test_client() as client:
        read_methods = [client.get, client.head]
        write_methods = [client.patch, client.put, client.post]
        all_methods = read_methods + write_methods
        method_names = {
            'GET': client.get,
            'POST': client.post,
            'PUT': client.put,
            'PATCH': client.patch,
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

        # check valid call without condition
        headers = [('Accept', 'application/json')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
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

        # check non matching If-None-Match
        headers = [('Accept', 'application/json'),
                   ('If-None-Match', '"xyz", "def"')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            check_normal_response(res, method)

        # check matching If-Match
        headers = [('Accept', 'application/json'),
                   ('If-Match', '"abc", "def"')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            check_normal_response(res, method)

        # check non matching If-Match
        headers = [('Accept', 'application/json'),
                   ('If-Match', '"xyz", "def"')]
        for method in all_methods:
            res = method('/objects/1', headers=headers)
            assert res.status_code == 412
