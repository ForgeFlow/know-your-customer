# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import mock

from odoo.tests.common import SavepointCase


class TestKycCommon(SavepointCase):
    def setUp(self):
        super().setUp()
        self.partner_model = self.env["res.partner"]
        self.webservice_model = self.env["webservice.backend"]
        self.scan_log_model = self.env["kyc.process.log"]
        self.wiz_model = self.env["kyc.partner.scan"]

        self.test_contact = self.partner_model.create(
            {
                "name": "Test Partner",
            }
        )
        self.test_company = self.partner_model.create(
            {
                "name": "Test company",
                "is_company": True,
                "ultimate_beneficial_owner_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Owner 1",
                            "birthdate": "1990-06-15",
                        },
                    )
                ],
            }
        )

        self.webservice = self.webservice_model.create(
            {
                "name": "Test backend KYC",
                "auth_type": "none",
            }
        )
        self.env.company.kyc_webservice_backend_id = self.webservice

    def _simulate_scan_partner(self, partner=None, result="ok"):
        if not partner:
            partner = self.test_contact
        mock_ws_call = mock.patch.object(type(self.webservice_model), "call")
        with mock_ws_call as mock_func:
            mock_func.return_value = (result, {})
            partner._action_kyc_scan()

    def _simulate_auto_scan_cron(self, result="ok"):
        mock_ws_call = mock.patch.object(type(self.webservice_model), "call")
        with mock_ws_call as mock_func:
            mock_func.return_value = (result, {})
            self.partner_model.auto_scan_partners()
