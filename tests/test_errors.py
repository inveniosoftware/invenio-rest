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

"""Error module tests."""

from __future__ import absolute_import, print_function

import json

from invenio_rest import InvenioREST
from invenio_rest.errors import FieldError, InvalidContentType, \
    RESTException, RESTValidationError


def test_errors(app):
    """Error handlers view."""
    InvenioREST(app)

    @app.route('/', methods=['GET'])
    def test_rest():
        raise RESTException(description='error description')

    @app.route('/contenttype', methods=['GET'])
    def test_content_type():
        raise InvalidContentType(allowed_content_types=['application/json'])

    @app.route('/validationerror', methods=['GET'])
    def test_validation_error():
        raise RESTValidationError(
            errors=[FieldError('myfield', 'mymessage', code=10)])

    with app.test_client() as client:
        res = client.get('/')
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data['status'] is None
        assert data['message'] == 'error description'

        res = client.get('/contenttype')
        assert res.status_code == 415
        data = json.loads(res.get_data(as_text=True))
        assert data['status'] == 415
        assert 'application/json' in data['message']

        res = client.get('/validationerror')
        assert res.status_code == 400
        data = json.loads(res.get_data(as_text=True))
        print(data)
        assert data['status'] == 400
        assert data['message'] == 'Validation error.'
        assert data['errors'] == [
            dict(field='myfield', message='mymessage', code=10)
        ]
