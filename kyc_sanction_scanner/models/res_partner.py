# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re
from datetime import datetime

from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_scan_id_from_response(self, response):
        res = super()._get_scan_id_from_response(response)
        backend = self._get_kyc_webservice_backend()
        if backend.tech_name == "kyc_sanction_scanner":
            if len(response) != 1 and type(response) is not dict:
                response = response[0]
            if response.get("Result", {}).get("ReferenceNumber", False):
                res = response["Result"]["ReferenceNumber"]
        return res

    def _get_scan_id_from_text(self, text):
        res = super()._get_scan_id_from_response(text)
        backend = self._get_kyc_webservice_backend()
        if backend.tech_name == "kyc_sanction_scanner":
            res = re.findall("'ReferenceNumber': '([^']+)'", text)
        return res

    def _get_next_ongoing_monitoring_from_response(self, response):
        res = super()._get_next_ongoing_monitoring_from_response(response)
        backend = self._get_kyc_webservice_backend()
        if backend.tech_name == "kyc_sanction_scanner":
            if len(response) != 1 and type(response) is not dict:
                response = response[0]
            if response.get("Result", {}).get("NextMonitoringDate", False):
                date = (response["Result"]["NextMonitoringDate"]).split(".")[0]
                res = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
        return res
