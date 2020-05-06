..
    This file is part of Invenio.
    Copyright (C) 2015-2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

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
