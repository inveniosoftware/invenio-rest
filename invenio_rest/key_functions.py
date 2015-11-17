# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Key functions for rate limiters."""

from flask import request
from flask_security import current_user


def key(name, value):
    """Return a key namespaced by the module."""
    return 'invenio-rest:{0}:{1}'.format(name, value)


def key_per_user():
    """Return a key for the user.

    Authenticated user get per user key. Anonymous users get a per
    IP key.
    """
    if current_user.is_authenticated:
        return key('user_id', current_user.get_id())
    else:
        return key('user_id', request.remote_addr)
