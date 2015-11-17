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


"""Minimal Flask application example for development.

Run example development server:

.. code-block:: console

   $ cd examples
   $ pip install -r requirements.txt
   $ flask -a app.py db init
   $ flask -a app.py db create
   $ flask -a app.py --debug run
"""

from __future__ import absolute_import, print_function

from flask import Flask, jsonify
from flask_babelex import Babel
from flask_cli import FlaskCLI
from flask_mail import Mail
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint
from invenio_db import InvenioDB

from invenio_rest import InvenioREST
from invenio_rest.key_functions import key_per_user

# Create Flask application
app = Flask(__name__)
app.config.update(
    MAIL_SUPPRESS_SEND=True,
    SECRET_KEY='CHANGE_ME',
    ACCOUNTS_USE_CELERY=False,
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
)
Babel(app)
FlaskCLI(app)
Mail(app)
InvenioDB(app)
InvenioAccounts(app)
app.register_blueprint(blueprint)
rest = InvenioREST(app)


@app.route('/limited/user')
@rest.limit_per_user(
    '1 per 5 seconds',
    error_message=lambda: 'limit exceeded for user {0}'.format(key_per_user())
)
def limited_user():
    """Route limited per user."""
    return jsonify(dict(
        message='passed limiter as user {0}'.format(key_per_user()),
        status=200
    ))
