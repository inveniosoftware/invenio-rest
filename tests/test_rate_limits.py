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

"""Rate limit tests."""

import json

from flask import Blueprint, jsonify
from flask_security import url_for_security

from invenio_rest import InvenioREST, limit_per_user


def test_application_factory(app):
    """Test limits can be defined before Invenio-Rest has been initialized."""
    rest = InvenioREST()

    @app.route('/')
    @limit_per_user(app, '3 per hour')
    def route():
        pass


def test_blueprint_limiting(accounts):
    """Test a limit can be applied to a Blueprint."""
    app = accounts
    rest = InvenioREST(app)

    blueprint = Blueprint(
        'limited',
        __name__,
    )

    @blueprint.route('/')
    @limit_per_user(blueprint, '3 per hour')
    def route():
        return jsonify({'status': 200})

    app.register_blueprint(blueprint)

    with app.test_client() as client:
        for x in range(3):
            resp = client.get('/')
            assert resp.status_code == 200
            data = json.loads(resp.get_data(as_text=True))
            assert data['status'] == 200
        resp = client.get('/')
        assert resp.status_code == 429
        data = json.loads(resp.get_data(as_text=True))
        assert data['status'] == 429


def test_unauthenticated_per_user_limit(accounts):
    """Test per user limit for unauthenticated users."""
    app = accounts
    rest = InvenioREST(app)

    @app.route('/')
    @limit_per_user(app, '3 per hour')
    def limited():
        return jsonify({'status': 200})

    with app.test_client() as client:
        for x in range(3):
            resp = client.get('/')
            assert resp.status_code == 200
            data = json.loads(resp.get_data(as_text=True))
            assert data['status'] == 200
        resp = client.get('/')
        assert resp.status_code == 429
        data = json.loads(resp.get_data(as_text=True))
        assert data['status'] == 429


def test_authenticated_per_user_limit(accounts):
    """Test per user limit for authenticated users."""
    app = accounts

    rest = InvenioREST(app)

    @app.route('/')
    @limit_per_user(app, '3 per hour')
    def limited():
        return jsonify({'status': 200})

    with app.test_client() as client:
        for x in range(3):
            resp = client.get('/')
            assert resp.status_code == 200
            data = json.loads(resp.get_data(as_text=True))
            assert data['status'] == 200
        resp = client.get('/')
        assert resp.status_code == 429
        data = json.loads(resp.get_data(as_text=True))
        assert data['status'] == 429

        sign_up(app, client)
        login(app, client)

        for x in range(3):
            resp = client.get('/')
            assert resp.status_code == 200
            data = json.loads(resp.get_data(as_text=True))
            assert data['status'] == 200
        resp = client.get('/')
        assert resp.status_code == 429
        data = json.loads(resp.get_data(as_text=True))
        assert data['status'] == 429


def sign_up(app, client):
    """Register a user."""
    client.post(url_for_security('register'), data=dict(
        email=app.config['TEST_USER_EMAIL'],
        password=app.config['TEST_USER_PASSWORD'],
    ))


def login(app, client):
    """Log the user in with the test client."""
    client.post(url_for_security('login'), data=dict(
        email=app.config['TEST_USER_EMAIL'],
        password=app.config['TEST_USER_PASSWORD'],
    ))
