# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = "res.partner"

    def name_get(self):
        res = []
        for partner in self:
            if partner.is_about_expire:
                res.append(
                    (
                        partner.id,
                        "%s %s" % (partner.name, (" (Contact about to expire)")),
                    )
                )
            else:
                res.append((partner.id, partner.name))
        return res

    def _compute_is_about_expire(self):
        for rec in self:
            if rec.kyc_status and rec.kyc_last_scan:
                delta = datetime.today() - rec.kyc_last_scan
                if delta.days >= 335 and delta.days <= 365:
                    rec.is_about_expire = True
                else:
                    rec.is_about_expire = False
            else:
                rec.is_about_expire = False

    def _search_is_about_expire(self, operator, value):
        from_date = datetime.now() - timedelta(days=365)
        to_date = datetime.now() - timedelta(days=335)
        return [("kyc_last_scan", ">=", from_date), ("kyc_last_scan", "<=", to_date)]

    def _compute_is_expire(self):
        for rec in self:
            if rec.kyc_status and rec.kyc_last_scan:
                delta = datetime.today() - rec.kyc_last_scan
                if delta.days > 365:
                    rec.is_expire = True
                else:
                    rec.is_expire = False
            else:
                rec.is_expire = False

    ultimate_beneficial_owner = fields.Char()
    birthdate_date = fields.Date(string="Date of Birth")
    nationality_id = fields.Many2one("res.country", "Nationality")
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
    is_about_expire = fields.Boolean(
        compute=_compute_is_about_expire, search=_search_is_about_expire
    )
    is_expire = fields.Boolean(compute=_compute_is_expire)

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
            "default_nationality_id": self.nationality_id
            and self.nationality_id.id
            or False,
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
            "default_nationality": self.nationality_id
            and self.nationality_id.id
            or False,
            "override_status": True,
        }
        return action

    @api.model
    def auto_scan_partners(self):
        partners = self.env["res.partner"].search([("is_company", "=", True)])
        for partner in partners:
            partner._action_kyc_scan(is_auto_call=True)
