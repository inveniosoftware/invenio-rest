# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API module for Invenio.

Invenio-REST takes care of installing basic error handling on a Flask API
application, as well as initializing Flask-Limiter for rate limiting and
Flask-CORS for Cross-Origin Resources Sharing (not enabled by default).
It also acts as orchestrator to take actions depending on the request headers,
such as dealing with ETag/If-Modified-Since cache header or Content-Type/Accept
header to resolve the right content serializer.

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

    >>> import xmltodict
    >>> from flask import jsonify, make_response
    >>> def json_v1_search(search_result):
    ...     return make_response(jsonify(search_result))
    >>> def xml_v1_search(search_result):
    ...     return make_response(xmltodict.unparse((search_result,)))

Views
-----
Now we create our view that will handle the requests and return the serialized
response based on the request's headers or using the default media type.
To do so, we need to create a class that inherits
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

Building REST APIs for Invenio
------------------------------
Following is a quick overview over which tools we are currently using for
building REST APIs. Before implementing your REST API, do take a look at some
of the existing REST APIs already implemented in Invenio to get some
inspiration.

In Invenio we have decided not to use some of the existing Flask extensions for
building REST APIs since mostly these extensions are not very flexible and
there are many existing Python libraries that do a much better job at the
individual tasks.

Flask application
~~~~~~~~~~~~~~~~~
Invenio's REST API is running in its own Flask application. This ensures that
the REST API can run on machines independently of the UI application and also
ensures that e.g. error handling, that it can be independently versioned, is
much simpler compared to having a mixed REST API/UI application.

Views
~~~~~
Views for REST APIs are built using standard Flask blueprints. We use
:class:`~flask.views.MethodView` for HTTP method based dispatching, and in
particular we use Invenio-REST's subclass
:class:`~.views.ContentNegotiatedMethodView` which takes care of selecting the
right serializer based on HTTP content negotiation.

Versioning
~~~~~~~~~~
Versioning of the REST API is primarily achieved through HTTP content
negotiation. I.e. you define a new MIME type that your clients explicitly
request (using :class:`~.views.ContentNegotiatedMethodView`).

Serialization/Deserialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Invenio-REST provides 2 ways to define how to serialize the response content:

    - `Query argument`: if the request query contains a well configured
      parameter, for example `format` (see the config
      `REST_MIMETYPE_QUERY_ARG_NAME`), then the serializer associated to the
      value of that argument will be used. With a request like::

          /api/record/<id>?format=custom_json

      and a defined mapping like::

          record_serializers_aliases={
              'custom_json': 'application/json',
              'marc21': 'application/marcxml+xml'
          }

      the output will be serialized using the serializer that is associated
      to the mimetype `application/json`.

    - `Headers`: if the query argument is missing or disabled, then the headers
      `Accept` or `Content-Type` are parsed to resolve the serializer to use.
      The expected value for the header is the mimetype::

          Accept: application/json

      again, the serializer associated to that mimetype will be used to format
      the output.


For serialization/deserialization we primarily use
`Marshmallow <http://marshmallow.readthedocs.io/>`_ which takes care
that REST API endpoints are supplied with proper argument types such as list of
strings or integers, or ensuring that e.g. timestamps are ISO8601 formatted in
UTC when serializing to JSON, and correctly deserialize timestamps into Python
datetime objects.

`Invenio-Records-REST <http://invenio-records-rest.readthedocs.io/>`_
is currently the most advanced example of using serializers with both JSON, XML
and text output.

Request parameters parsing
~~~~~~~~~~~~~~~~~~~~~~~~~~
Request parameters in the URL or JSON are most often handled with the library
`webargs <https://webargs.readthedocs.io/>`_.

Error handling
~~~~~~~~~~~~~~
Invenio-REST provides some default exceptions which you can subclass, which
when thrown, will render a proper REST API response for the error to the
client (see e.g. :class:`~invenio_rest.errors.RESTException`).

Headers (security, CORS and rate limiting)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`Invenio-App <https://invenio-app.readthedocs.io/>`_ is responsible
for installing
`Flask-Tailsman <https://github.com/GoogleCloudPlatform/flask-talisman>`_ which
sets many important security related headers as well as
`Flask-Limiter <https://flask-limiter.readthedocs.io/>`_ which
provides rate limiting.

Invenio-REST is responsible for installing
`Flask-CORS <https://flask-cors.readthedocs.io/>`_ which provides
support for Cross-Origin Resource Sharing.

`Invenio-OAuth2Server
<https://invenio-oauth2server.readthedocs.io/en/latest/>`_ along with
`Invenio-Accounts <https://invenio-accounts.readthedocs.io/en/latest/>`_ is
responsible for providing API authentication based on OAuth 2.0 as well as
protecting against CRSF-attacks in the REST API.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioREST
from .version import __version__
from .views import ContentNegotiatedMethodView

__all__ = ('__version__', 'InvenioREST', 'ContentNegotiatedMethodView')
