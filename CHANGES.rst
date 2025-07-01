..
    This file is part of Invenio.
    Copyright (C) 2015-2020 CERN.
    Copyright (C) 2022 Northwestern University.
    Copyright (C) 2024-2025 Graz University of Technology.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version v2.0.4 (released 2025-07-01)

- fix: pkg_resources DeprecationWarning

Version v2.0.3 (released 2025-04-17)

- installation: pin marshmallow to <4.0.0

Version v2.0.2 (released 2025-02-24)

- fix: copyright headers

Version v2.0.1 (released 2025-02-24)

- fix: flask changed from APP_ALLOWED_HOSTS to TRUSTED_HOSTS

Version 2.0.0 (released 2024-12-03)

- fix: set_cookie needs a str
- fix: cookie_jar not in FlaskClient
- tests: update api usage of set_cookie
- fix: set_cookie needs a str
- chore: remove unused imports
- global: remove try except for jws
- setup: bump major dependencies

Version v1.5.0 (released 2024-12-02)

- global: make sentry-sdk optional
    * Import-detects `sentry_sdk` so that we can remove the hard dependency.

Version 1.4.2 (release 2024-11-30)

- fix: no translation

Version 1.4.1 (release 2024-11-30)

- setup: change to reusable workflows
- setup: pin dependencies

Version 1.4.0 (released 2024-11-19)

- global: remove six usage
- global: use jws from invenio-base
- fix: forward compatibility with flask>=3.0

Version 1.3.1 (released 2024-07-17)

- csrf: improve token validation workflow

Version 1.3.0 (released 2023-10-17)

- Fixed sentry error id.

Version 1.2.8 (released 2022-01-13)

- Add support for ItsDangerous <2.1 (datetime aware/naive of date_signed)

Version 1.2.6 (released 2021-12-05)

- Add support for CSRF token rotation during a grace period to allow clients
  transparently rotate the CSRF token without being prompted with CSRF errors.

Version 1.2.5 (released 2021-12-04)

- Fix issue with CSRF token being reset on every request.

Version 1.2.4 (released 2021-10-18)

- Support for Flask v2.0

Version 1.2.3 (released 2020-12-07)

- Fixes a bug with CSRF checking when the endpoint did not exist.

Version 1.2.2 (released 2020-09-27)

- Adds Cache-Control:'no-cache' header to 304 responses to
  ensure that browsers will not cache responses client side

Version 1.2.1 (released 2020-05-08)

- The CSRF Middleware is now by default disabled.
- The ``CSRF_SECRET_SALT`` now defaults to ``invenio-csrf-token``.
- Added a new configuration variable: ``CSRF_FORCE_SECURE_REFERER``.

Version 1.2.0 (released 2020-03-10)

- Centralize dependency management via Invenio-Base.

Version 1.1.3 (released 2020-01-08)

- Set upper limit version of webargs, lower than 6.0.0.

Version 1.1.2 (released 2019-09-19)

- Bumps webargs to 5.5.0 (provides support for marshmallow 3).

Version 1.1.1 (released 2019-08-02)

- Bumps marshmallow to 2.15.2 (minimum required by webargs).

Version 1.1.0 (released 2019-07-31)

- Adds marshmallow 2 vs 3 compatibility functions.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
