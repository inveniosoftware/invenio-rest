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

Please also see
`Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_ and
`Flask-CORS <https://flask-cors.readthedocs.io/en/latest/>`_ for many more
configuration options.
