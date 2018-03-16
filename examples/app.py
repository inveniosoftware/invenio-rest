# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Minimal Flask application example.

SPHINX-START

First install Invenio-REST, setup the application and load
fixture data by running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

    $ export FLASK_APP=app.py FLASK_DEBUG=1
    $ flask run

and use cURL to explore the simplistic REST API:

.. code-block:: console

   $ curl -v -XGET http://0.0.0.0:5000/records/
   $ curl -v -XGET http://0.0.0.0:5000/records/ \\
       -H Accept:application/xml

The example app demonstrates:

* Use of ``Accept`` headers to change the serialization from JSON to XML via
  the :class:`invenio_rest.views.ContentNegotiatedMethodView`.
* CORS headers (``Access-Control-Allow-Origin`` and
  ``Access-Control-Expose-Headers``).

To reset the example application run:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

from __future__ import absolute_import, print_function

import xmltodict
from flask import Blueprint, Flask, jsonify, make_response

from invenio_rest import ContentNegotiatedMethodView, InvenioREST


def json_v1_search(search_result):
    """Serialize records."""
    return make_response(jsonify(search_result))


def xml_v1_search(search_result):
    """Serialize records as text."""
    return make_response(xmltodict.unparse(search_result))


class RecordsListResource(ContentNegotiatedMethodView):
    """Example REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        super(RecordsListResource, self).__init__(
            method_serializers={
                'GET': {
                    'application/json': json_v1_search,
                    'application/xml': xml_v1_search,
                },
            },
            default_method_media_type={
                'GET': 'application/json',
            },
            default_media_type='application/json',
            **kwargs)

    def get(self, **kwargs):
        """Implement the GET /records."""
        return {"title": "Test"}

# Create Flask application
app = Flask(__name__)
app.config.update({
    'REST_ENABLE_CORS': True,
})

InvenioREST(app)

blueprint = Blueprint(
    'mymodule',
    __name__,
    url_prefix='/records',
    template_folder='templates',
    static_folder='static',
)

records_view = RecordsListResource.as_view('records')
blueprint.add_url_rule('/', view_func=records_view)

app.register_blueprint(blueprint)
