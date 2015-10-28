Installation
============

Invenio-REST is on PyPI so all you need is:

.. code-block:: console

   $ pip install invenio-rest

If you want Cross-Origin Resource Sharing (CORS) support you need to either
install Flask-CORS manually or simply use the extra requires directive like
this:

.. code-block:: console

   $ pip install invenio-rest[cors]

Configuration
-------------

===================== =================================================
`REST_ENABLE_CORS`    Set to ``True`` to enable Cross-Origin Resource
                      Sharing. Defaults to ``False``.
`REST_CORS_RESOURCES` Dictionary for configuring CORS for endpoints.
                      See Flask-CORS for further details.
===================== =================================================

Please also see
`Flask-Limiter <http://flask-limiter.readthedocs.org/en/stable/>`_ and
`Flask-CORS <https://flask-cors.readthedocs.org/en/latest/>`_ for many more
configuration options.
