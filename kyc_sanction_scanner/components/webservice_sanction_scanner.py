# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import http.client
import json
from urllib.parse import quote

from odoo.addons.component.core import Component


class SanctionScannerApi(Component):
    _name = "kyc.webservice.sanctionscanner"
    _webservice_protocol = "http"
    _usage = "kyc.scan"
    _inherit = "base.webservice.adapter"

    @classmethod
    def _component_match(cls, work, usage=None, model_name=None, **kw):
        res = super()._component_match(work, usage=usage, model_name=model_name, **kw)
        return res and work.collection.tech_name == "kyc_sanction_scanner"

    def _get_connection_and_header(self):
        conn = http.client.HTTPConnection(self.collection.url)
        username = self.collection.username
        password = self.collection.password
        auth_token = base64.b64encode(bytes(username + ":" + password, "utf-8")).decode(
            "utf-8"
        )
        headers = {
            "Authorization": "Basic %s" % auth_token,
        }
        return conn, headers

    def scan(self, partner):
        # ref: http://developer.sanctionscanner.com/en/search-methods
        conn, headers = self._get_connection_and_header()
        payload = ""
        search_type = 2 if partner.is_company else 1
        # TODO: country code? birth date? ultimate beneficial owner?
        conn.request(
            "GET",
            "/api/Search/SearchByName?name=%s&searchType=%s"
            % (quote(partner.name), search_type),
            payload,
            headers,
        )
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))
        self.env["kyc.process.log"].sudo().create(
            {
                "req_data": payload,
                "res_data": response,
                "author_id": self.env.user.id,
                "partner_id": partner.id,
            }
        )
        match_status = response.get("Result", {}).get("MatchStatusId", 0)
        # 0:Unknown
        # 1:No Match
        # 2:Potential Match
        # 3:False Positive
        # 4:True Positive
        # 5:True Positive Approve
        # 6:True Positive Reject
        if response.get("HttpStatusCode") != 200 or match_status == 0:
            return "error", response
        if match_status == 1:
            return "ok", response
        # TODO: more cases.
        return "sanction", response
