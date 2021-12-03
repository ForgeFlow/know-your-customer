# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = "res.partner"

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
    kyc_last_scan = fields.Datetime()
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "res_partner_attachment_rel",
        "partner_id",
        "attachment_id",
        "Compliance documents",
    )

    # TODO: whitelist

    def _get_kyc_webservice_backend(self):
        return self.env.company.kyc_webservice_backend_id

    def action_kyc_scan(self):
        if not self.env["webservice.backend"].search([("is_kyc", "=", True)]):
            raise NotImplementedError()
        # for rec in self:
        #     rec._action_kyc_scan()
        action = self.env.ref("kyc.kyc_partner_scan_action").read()[0]
        action["context"] = {
            "default_partner_id": self.id,
            "default_ultimate_beneficial_owner": self.ultimate_beneficial_owner,
            "default_birthdate_date": self.birthdate_date,
            "default_nationality": self.nationality,
            "scan_kyc_status": True,
            "required_company_fields": True if self.is_company else False,
            "required_individual_fields": False if self.is_company else True,
        }
        return action

    def _action_kyc_scan(self, is_auto_call=False):
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
        vals = {"kyc_status": kyc_status}
        if not is_auto_call:
            vals.update({"kyc_last_scan": datetime.now()})
        self.write(vals)

    def action_override_kyc_status(self):
        action = self.env.ref("kyc.kyc_partner_scan_action").read()[0]
        action["name"] = "Override KYC Status"
        action["context"] = {
            "default_partner_id": self.id,
            "default_nationality": self.nationality,
            "override_status": True,
        }
        return action

    @api.model
    def auto_scan_partners(self):
        partners = self.env["res.partner"].search([("is_company", "=", True)])
        for partner in partners:
            partner._action_kyc_scan(is_auto_call=True)
