# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API module for Invenio."""

import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

docs_require = [
    'Sphinx==4.2.0',
]

tests_require = [
    'xmltodict>=0.11.0',
    'pytest-invenio>=1.4.0',
]

extras_require = {
    # `cors` moved to `install_requires`, but kept for backward compatibility
    'cors': [],
    'docs': docs_require,
    'tests': tests_require + docs_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)


install_requires = [
    'Flask-CORS>=2.1.0',
    'invenio-base>=1.2.5',
    'marshmallow>=2.15.2',
    'webargs>=5.5.0,<6.0.0',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_rest', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-rest',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio rest api module',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-rest',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'invenio_rest = invenio_rest.csrf:CSRFTokenMiddleware',
        ],
        'invenio_base.api_apps': [
            'invenio_rest = invenio_rest:InvenioREST',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 5 - Production/Stable',
    ],
)
