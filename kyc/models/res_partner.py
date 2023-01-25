# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import threading
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

KYC_STATUSES = [
    ("pending", "To Scan"),
    ("ok", "Validated"),
    ("sanction", "Sanction"),
    ("error", "Error"),
]


class Partner(models.Model):
    _inherit = "res.partner"

    def _compute_kyc_is_about_expire(self):
        for rec in self:
            if rec.kyc_status and rec.kyc_last_scan:
                delta = datetime.today() - rec.kyc_last_scan
                if delta.days >= 335 and delta.days < 365:
                    rec.kyc_is_about_expire = True
                else:
                    rec.kyc_is_about_expire = False
            else:
                rec.kyc_is_about_expire = False

    def _search_kyc_is_about_expire(self, operator, value):
        from_date = datetime.now() - timedelta(days=365)
        to_date = datetime.now() - timedelta(days=335)
        return [("kyc_last_scan", ">=", from_date), ("kyc_last_scan", "<=", to_date)]

    def _compute_kyc_is_expired(self):
        for rec in self:
            if rec.kyc_status and rec.kyc_last_scan:
                delta = datetime.today() - rec.kyc_last_scan
                if delta.days >= 365:
                    rec.kyc_is_expired = True
                else:
                    rec.kyc_is_expired = False
            else:
                rec.kyc_is_expired = False

    def _search_kyc_is_expired(self, operator, value):
        if operator != "=" or not isinstance(value, bool):
            raise UserError(_("Unsupported search operation"))
        expiring_date = datetime.now() - timedelta(days=365)
        operator = "<" if value else ">="
        return [("kyc_status", "=", "ok"), ("kyc_last_scan", operator, expiring_date)]

    ultimate_beneficial_owner_ids = fields.One2many(
        "kyc.ubo", "partner_id", "Ultimate beneficial owner"
    )
    birthdate_date = fields.Date(string="Date of Birth")
    nationality_id = fields.Many2one("res.country", "Nationality")
    kyc_status = fields.Selection(
        selection=KYC_STATUSES,
        default="pending",
    )
    kyc_last_scan = fields.Datetime()
    kyc_last_auto_scan = fields.Datetime()
    kyc_document_ids = fields.One2many(
        "kyc.document",
        "partner_id",
        string="Compliance documents",
    )
    kyc_is_about_expire = fields.Boolean(
        compute=_compute_kyc_is_about_expire, search=_search_kyc_is_about_expire
    )
    kyc_is_expired = fields.Boolean(
        compute="_compute_kyc_is_expired",
        search="_search_kyc_is_expired",
    )
    is_government = fields.Boolean(string="Is Government?")
    kyc_scan_required = fields.Boolean(
        compute="_compute_kyc_scan_required",
        help="Indicates that a contact need to be considered for KYC scans and"
        "therefore KYC options need to be displayed",
    )

    def _compute_kyc_scan_required(self):
        for rec in self:
            rec.kyc_scan_required = rec._is_kyc_scan_required()

    def _is_kyc_scan_required(self):
        """Define custom logic to require KYC scan"""
        self.ensure_one()
        return True

    def _kyc_accept_transaction(self, _record, raise_if_not=True):
        self.ensure_one()
        accept = not self.kyc_is_expired and self.kyc_status == "ok"
        if not accept and raise_if_not:
            raise UserError(
                _("%s's KYC status ('%s') is not valid or it is expired.")
                % (self.name, self.kyc_status)
            )
        return accept

    def _get_kyc_webservice_backend(self):
        return self.env.company.kyc_webservice_backend_id

    def action_kyc_scan(self):
        if not self.env["webservice.backend"].sudo().search([("is_kyc", "=", True)]):
            raise NotImplementedError()
        action = self.env.ref("kyc.kyc_partner_scan_action").sudo().read()[0]
        action["context"] = {
            "default_partner_id": self.id,
            "default_ultimate_beneficial_owner_ids": [
                (
                    6,
                    0,
                    self.ultimate_beneficial_owner_ids
                    and self.ultimate_beneficial_owner_ids.ids
                    or [],
                )
            ],
            "default_birthdate_date": self.birthdate_date,
            "default_nationality_id": self.nationality_id
            and self.nationality_id.id
            or False,
            "scan_kyc_status": True,
            "required_company_fields": True if self.is_company else False,
            "required_individual_fields": False if self.is_company else True,
        }
        return action

    def _get_request_dict(self):
        """summary of the request to be recorded in logs"""
        res = {
            "name": self.name,
        }
        if self.is_company:
            res.update(
                {
                    "ultimate_beneficial_owner": ",".join(
                        [
                            uob.name + "-" + str(uob.birthdate.year)
                            for uob in self.ultimate_beneficial_owner_ids
                        ]
                    ),
                }
            )
        else:
            res.update(
                {
                    "birthdate_date": self.birthdate_date,
                    "country": self.nationality_id.code,
                }
            )
        return res

    def _action_kyc_scan(self, is_auto_call=False):
        self.ensure_one()
        backend = self._get_kyc_webservice_backend()
        if not backend:
            raise UserError(
                _("KYC provider not configured. Contact your system administrator.")
            )
        kyc_status, response = backend.sudo().call("scan", self)
        self.env["kyc.process.log"].sudo().create(
            {
                "req_data": self._get_request_dict(),
                "res_data": response,
                "author_id": self.env.user.id,
                "partner_id": self.id,
                "kyc_result": kyc_status,
            }
        )
        vals = {"kyc_status": kyc_status}
        if not is_auto_call:
            vals.update({"kyc_last_scan": datetime.now()})
        else:
            vals.update({"kyc_last_auto_scan": datetime.now()})
        self.write(vals)

    def action_override_kyc_status(self):
        if not self.env.user.has_group("kyc.group_override_kyc_status"):
            return False
        action = self.env.ref("kyc.kyc_partner_scan_action").sudo().read()[0]
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
    def _get_domain_auto_scan_partners(self):
        return [
            ("is_company", "=", True),
            ("ultimate_beneficial_owner_ids", "!=", False),
        ]

    @api.model
    def auto_scan_partners(self, domain=False, period=30):
        auto_commit = not getattr(threading.currentThread(), "testing", False)
        cut_date = fields.Datetime.today() - timedelta(days=period)
        if not domain:
            domain = self._get_domain_auto_scan_partners()
        domain.extend(
            [
                "|",
                ("kyc_last_auto_scan", "=", False),
                ("kyc_last_auto_scan", "<", cut_date),
            ]
        )
        partners = self.env["res.partner"].search(domain)
        for partner in partners:
            partner._action_kyc_scan(is_auto_call=True)
            if auto_commit:
                self._cr.commit()  # pylint: disable=E8102
