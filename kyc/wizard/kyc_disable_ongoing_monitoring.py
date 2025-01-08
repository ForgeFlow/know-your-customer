# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class KYCDisableOngoingMonitoring(models.TransientModel):
    _name = "kyc.disable.ongoing.monitoring"
    _description = "KYC Disable Ongoing Monitoring"

    partner_id = fields.Many2one("res.partner")

    def action_kyc_disable_ongoing_monitoring(self):
        self.ensure_one()
        backend = self.partner_id._get_kyc_webservice_backend()
        if not backend:
            raise UserError(
                _("KYC provider not configured. Contact your system administrator.")
            )
        kyc_status, response = backend.sudo().call(
            "disable_ongoing_monitoring",
            self.partner_id,
            self.partner_id.kyc_last_scan_id,
        )
        self.env["kyc.process.log"].sudo().create(
            {
                "req_data": self.partner_id._get_request_dict("disable_om"),
                "res_data": response,
                "author_id": self.env.user.id,
                "partner_id": self.partner_id.id,
                "kyc_result": kyc_status,
                "type": "disable_om",
                "scan_id": self.partner_id.kyc_last_scan_id,
            }
        )
        if kyc_status == "ok":
            self.partner_id.write(
                {
                    "kyc_ongoing_monitoring_period": "no",
                    "kyc_ongoing_monitoring": False,
                }
            )
