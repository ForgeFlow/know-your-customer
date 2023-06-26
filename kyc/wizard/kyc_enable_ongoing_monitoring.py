# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError

ONGOING_PERIODS = [
    ("1", "Daily"),
    ("2", "Weekly"),
    ("3", "Monthly"),
    ("4", "Quarterly"),
    ("5", "Half Year"),
    ("6", "Yearly"),
]


class KYCEnableOngoingMonitoring(models.TransientModel):
    _name = "kyc.enable.ongoing.monitoring"
    _description = "KYC Enable Ongoing Monitoring"

    period_id = fields.Selection(
        selection=ONGOING_PERIODS,
        default="3",
    )

    partner_id = fields.Many2one("res.partner")

    def action_kyc_enable_ongoing_monitoring(self):
        self.ensure_one()
        backend = self.partner_id._get_kyc_webservice_backend()
        if not backend:
            raise UserError(
                _("KYC provider not configured. Contact your system administrator.")
            )
        kyc_status, response = backend.sudo().call(
            "enable_ongoing_monitoring",
            self.partner_id,
            self.partner_id.kyc_last_scan_id,
            self.period_id,
        )
        self.env["kyc.process.log"].sudo().create(
            {
                "req_data": self.partner_id._get_request_dict("enable_om"),
                "res_data": response,
                "author_id": self.env.user.id,
                "partner_id": self.partner_id.id,
                "kyc_result": kyc_status,
                "type": "enable_om",
                "scan_id": self.partner_id.kyc_last_scan_id,
            }
        )
        if kyc_status == "ok":
            self.partner_id.write(
                {
                    "kyc_ongoing_monitoring_period": self.period_id,
                    "kyc_ongoing_monitoring": True,
                }
            )
