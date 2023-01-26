# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import mock

from odoo.tests.common import TransactionCase


class TestKycCommon(TransactionCase):
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

        self.webservice = self.webservice_model.create(
            {
                "name": "Test backend KYC",
            }
        )
        self.env.company.kyc_webservice_backend_id = self.webservice
