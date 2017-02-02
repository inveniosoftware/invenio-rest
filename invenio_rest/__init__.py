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

"""REST API module for Invenio.

Invenio-REST takes care of installing basic error handling on a Flask API
application, as well as initializing Flask-Limiter for rate limiting and
Flask-CORS for Cross-Origin Resources Sharing (not enabled by default).

Initialization
--------------
First create a Flask application:

    >>> from flask import Flask
    >>> app = Flask('myapp')

Next, initialize your extension:

    >>> from invenio_rest import InvenioREST
    >>> InvenioREST(app)
    <invenio_rest.ext.InvenioREST ...>

Serializers
-----------
Let's create 2 serializers that will return our answer to the correct format.
For instance, our server will be able to either answer in JSON or in XML:

    >>> import dicttoxml
    >>> from flask import jsonify, make_response
    >>> def json_v1_search(search_result):
    ...     return make_response(jsonify(search_result))
    >>> def xml_v1_search(search_result):
    ...     return make_response(dicttoxml.dicttoxml((search_result,)))

Views
-----
Now we create our view that will handle the requests and return the answer. To
do so, we need to create a class that inherit
:class:`~.views.ContentNegotiatedMethodView`. In the constructor, we register
our two serializers, and we create a `get` method for the `GET` requests:

    >>> from invenio_rest import ContentNegotiatedMethodView
    >>> class RecordsListResource(ContentNegotiatedMethodView):
    ...     def __init__(self, **kwargs):
    ...         super(RecordsListResource, self).__init__(
    ...             method_serializers={
    ...                 'GET': {
    ...                     'application/json': json_v1_search,
    ...                     'application/xml': xml_v1_search,
    ...                 },
    ...             },
    ...             default_method_media_type={
    ...                 'GET': 'application/json',
    ...             },
    ...             default_media_type='application/json',
    ...             **kwargs)
    ...     def get(self, **kwargs):
    ...         return {"title": "Test"}

To finish, we need to create a blueprint that defines an endpoint (here
`/records`) and that registers our class:

    >>> from flask import Blueprint
    >>> blueprint = Blueprint(
    ...     'mymodule',
    ...     'myapp',
    ...     url_prefix='/records',
    ...     template_folder='templates',
    ...     static_folder='static',
    ... )
    >>> records_view = RecordsListResource.as_view('records')
    >>> blueprint.add_url_rule('/', view_func=records_view)
    >>> app.register_blueprint(blueprint)

Now you can launch your server and request it on the `/records` endpoint, as
described in :any:`examplesapp`.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioREST
from .version import __version__
from .views import ContentNegotiatedMethodView

__all__ = ('__version__', 'InvenioREST', 'ContentNegotiatedMethodView')
