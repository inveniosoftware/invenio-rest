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

from invenio_rest import InvenioREST
from invenio_rest.decorators import require_content_types


def test_require_content_types(app):
    """Error handlers view."""
    InvenioREST(app)

    @app.route("/", methods=['POST'])
    @require_content_types('application/json', 'text/plain')
    def test_view():
        return "OK"

    with app.test_client() as client:
        res = client.post("/", content_type='application/json', data="{}")
        assert res.status_code == 200
        res = client.post("/", content_type='text/plain', data="test")
        assert res.status_code == 200
        res = client.post("/", content_type='application/json;charset=utf-8',
                          data="{}")
        assert res.status_code == 200
        res = client.post("/", content_type='application/xml', data="<d></d>")
        assert res.status_code == 415
        data = json.loads(res.get_data(as_text=True))
        assert data['status'] == 415
        assert 'application/json' in data['message']
        assert 'text/plain' in data['message']
