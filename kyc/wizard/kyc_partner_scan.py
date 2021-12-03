# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class KYCPartnerScan(models.TransientModel):
    _name = "kyc.partner.scan"
    _description = "KYC Partner Scan"

    partner_id = fields.Many2one("res.partner", "Partner")
    ultimate_beneficial_owner = fields.Char()
    birthdate_date = fields.Date(string="Date of Birth")
    nationality = fields.Char()
    kyc_status = fields.Selection(
        selection=[
            ("pending", "To Scan"),
            ("ok", "Validated"),
            ("sanction", "Sanction"),
            ("error", "Error"),
        ],
        default="pending",
    )
    status_override_reason = fields.Char()

    def scan(self):
        self.partner_id._action_kyc_scan()

    def override_kyc_status(self):
        self.partner_id.message_post(
            body=_(
                "<b>KYC Status Update from %s to %s</b><br/><b>Reason:</b>%s"
                % (
                    dict(self._fields["kyc_status"].selection).get(
                        self.partner_id.kyc_status
                    ),
                    dict(self._fields["kyc_status"].selection).get(self.kyc_status),
                    self.status_override_reason,
                )
            )
        )
        self.partner_id.write({"kyc_status": self.kyc_status})
