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
        conn = http.client.HTTPSConnection(self.collection.url)
        username = self.collection.username
        password = self.collection.password
        auth_token = base64.b64encode(bytes(username + ":" + password, "utf-8")).decode(
            "utf-8"
        )
        headers = {
            "Authorization": "Basic %s" % auth_token,
        }
        return conn, headers

    def _scan(self, partner):
        # ref: http://developer.sanctionscanner.com/en/search-methods
        conn, headers = self._get_connection_and_header()
        payload = ""
        search_type = 2 if partner.is_company else 1
        request_params_str = "/api/Search/SearchByName?name=%s&searchType=%s" % (
            quote(partner.name),
            search_type,
        )
        if not partner.is_company:
            request_params_str += "&birthYear=%s" % partner.birthdate_date.year
            request_params_str += "&countryCodes=%s" % partner.nationality_id.code
        conn.request(
            "GET",
            request_params_str,
            payload,
            headers,
        )
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))
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

    def _scan_by_name(self, name, birthdate=None):
        # ref: http://developer.sanctionscanner.com/en/search-methods
        conn, headers = self._get_connection_and_header()
        payload = ""
        search_type = 1
        if name and birthdate:
            conn.request(
                "GET",
                "/api/Search/SearchByName?name=%s&birthYear=%s&searchType=%s"
                % (quote(name), birthdate, search_type),
                payload,
                headers,
            )
        else:
            conn.request(
                "GET",
                "/api/Search/SearchByName?name=%s&searchType=%s"
                % (quote(name), search_type),
                payload,
                headers,
            )
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))
        match_status = response.get("Result", {}).get("MatchStatusId", 0)
        if response.get("HttpStatusCode") != 200 or match_status == 0:
            return "error", response
        if match_status == 1:
            return "ok", response
        # TODO: more cases.
        return "sanction", response

    def scan(self, partner):
        kyc_status, response = self._scan(partner)
        scan_id = response.get("Result", {}).get("ReferenceNumber")
        self._get_pdf_detailed_report(scan_id, partner)
        if partner.is_company:
            statuses = [kyc_status]
            responses = [response]
            for ubo in partner.ultimate_beneficial_owner_ids:
                sub_status, sub_response = self._scan_by_name(
                    ubo.name, ubo.birthdate and ubo.birthdate.year or None
                )
                statuses.append(sub_status)
                responses.append(sub_response)
                scan_id = sub_response.get("Result", {}).get("ReferenceNumber")
                self._get_pdf_detailed_report(scan_id, partner)
            if any(s == "error" for s in statuses):
                kyc_status = "error"
            elif any(s == "sanction" for s in statuses):
                kyc_status = "sanction"
            elif any(s == "ok" for s in statuses):
                kyc_status = "ok"
            response = responses
        return kyc_status, response

    def _get_pdf_detailed_report(self, scan_id, partner):
        if not scan_id:
            return False
        conn, headers = self._get_connection_and_header()
        payload = ""
        conn.request(
            "GET",
            "/api/Retrieving/GetDetailPdfReportByScanId?scanId=%s" % quote(scan_id),
            payload,
            headers,
        )
        res = conn.getresponse()
        data = res.read()
        doc_name = "%s.pdf" % scan_id
        attachment = self.env["ir.attachment"].create(
            {"name": doc_name, "datas": base64.b64encode(data)}
        )
        kyc_doc = self.env["kyc.document"].create(
            {
                "attachment_id": attachment.id,
                "name": doc_name,
                "document_type": "scan_certificate",
            }
        )
        partner.kyc_document_ids += kyc_doc
        return True
