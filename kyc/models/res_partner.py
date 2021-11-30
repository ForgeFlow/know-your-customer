# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = "res.partner"

    ultimate_beneficial_owner = fields.Char()
    birthdate_date = fields.Date(string="Date of Birth")
    kyc_status = fields.Selection(
        selection=[
            ("pending", "To Scan"),
            ("ok", "Validated"),
            ("sanction", "Sanction"),
            ("error", "Error"),
        ],
        default="pending",
    )
    # TODO: whitelist

    def _get_kyc_webservice_backend(self):
        return self.env.company.kyc_webservice_backend_id

    def action_kyc_scan(self):
        if not self.env["webservice.backend"].search([("is_kyc", "=", True)]):
            raise NotImplementedError()
        for rec in self:
            rec._action_kyc_scan()
        return True

    def _action_kyc_scan(self):
        self.ensure_one()
        backend = self._get_kyc_webservice_backend()
        if not backend:
            raise UserError(
                _("KYC provider not configured. Contact your system administrator.")
            )
        kyc_status, response = backend.call("scan", self)
        # TODO: generate log.
        # TODO: show a banner in the partner if the status is "error"
        # TODO: dates...
        self.write({"kyc_status": kyc_status})

    def action_override_kyc_status(self):
        # TODO: use wizard with restricted access to request a reason.
        raise NotImplementedError()
