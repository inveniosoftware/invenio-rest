# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

"""Module tests."""

from __future__ import absolute_import, print_function

import json

from invenio_rest import InvenioREST
from invenio_rest.decorators import require_content_types


def test_require_content_types(app):
    """Error handlers view."""
    InvenioREST(app)

    @app.route("/", methods=["POST"])
    @require_content_types("application/json", "text/plain")
    def test_view():
        return "OK"

    with app.test_client() as client:
        res = client.post("/", content_type="application/json", data="{}")
        assert res.status_code == 200
        res = client.post("/", content_type="text/plain", data="test")
        assert res.status_code == 200
        res = client.post("/", content_type="application/json;charset=utf-8", data="{}")
        assert res.status_code == 200
        res = client.post("/", content_type="application/xml", data="<d></d>")
        assert res.status_code == 415
        data = json.loads(res.get_data(as_text=True))
        assert data["status"] == 415
        assert "application/json" in data["message"]
        assert "text/plain" in data["message"]
