# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import threading
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

KYC_STATUSES = [
    ("pending", "To Scan"),
    ("ok", "Validated"),
    ("sanction", "Sanction"),
    ("error", "Error"),
]

ONGOING_PERIODS = [
    ("no", "No"),
    ("1", "Daily"),
    ("2", "Weekly"),
    ("3", "Monthly"),
    ("4", "Quarterly"),
    ("5", "Half Year"),
    ("6", "Yearly"),
]

PERIODS_TIMEDELTA = {
    "no": timedelta(days=0),
    "1": timedelta(days=1),
    "2": timedelta(days=7),
    "3": timedelta(days=30),
    "4": timedelta(days=90),
    "5": timedelta(days=180),
    "6": timedelta(days=365),
}


class Partner(models.Model):
    _inherit = "res.partner"

    def _compute_kyc_is_about_expire(self):
        for rec in self:
            if rec.kyc_status and rec.kyc_last_scan:
                start_warning_date = rec.kyc_expiration_date - relativedelta(months=1)
                rec.kyc_is_about_expire = (
                    start_warning_date < datetime.today() < rec.kyc_expiration_date
                )
                rec.kyc_is_about_to_expire_msg = (
                    _("KYC Scan will expire on %s.") % rec.kyc_expiration_date.date()
                )
            else:
                rec.kyc_is_about_expire = False
                rec.kyc_is_about_to_expire_msg = False

    def _search_kyc_is_about_expire(self, operator, value):
        from_date = datetime.now() - relativedelta(years=1)
        to_date = from_date + relativedelta(months=1)
        return [("kyc_last_scan", ">=", from_date), ("kyc_last_scan", "<=", to_date)]

    def _compute_kyc_is_expired(self):
        for rec in self:
            if rec.kyc_status and rec.kyc_last_scan:
                rec.kyc_is_expired = datetime.today() > rec.kyc_expiration_date
            else:
                rec.kyc_is_expired = False

    def _search_kyc_is_expired(self, operator, value):
        if operator != "=" or not isinstance(value, bool):
            raise UserError(_("Unsupported search operation"))
        expiring_date = datetime.now() - relativedelta(years=1)
        operator = "<" if value else ">="
        return [("kyc_status", "!=", False), ("kyc_last_scan", operator, expiring_date)]

    ultimate_beneficial_owner_ids = fields.One2many(
        "kyc.ubo", "partner_id", "Ultimate beneficial owner"
    )
    birthdate_date = fields.Date(string="Date of Birth")
    nationality_id = fields.Many2one("res.country", "Nationality")
    kyc_status = fields.Selection(
        selection=KYC_STATUSES,
        default="pending",
    )
    kyc_auto_scan = fields.Boolean(
        default=False, help="When enabled, it will auto-scan the partner"
    )
    kyc_last_scan = fields.Datetime()
    kyc_last_auto_scan = fields.Datetime()
    kyc_document_ids = fields.One2many(
        "kyc.document",
        "partner_id",
        string="Compliance documents",
    )
    kyc_expiration_date = fields.Datetime(compute="_compute_kyc_expiration_date")
    kyc_is_about_expire = fields.Boolean(
        compute="_compute_kyc_is_about_expire",
        search="_search_kyc_is_about_expire",
        compute_sudo=True,
    )
    kyc_is_about_to_expire_msg = fields.Char(
        compute="_compute_kyc_is_about_expire", compute_sudo=True
    )
    kyc_is_expired = fields.Boolean(
        compute="_compute_kyc_is_expired",
        search="_search_kyc_is_expired",
    )
    kyc_ongoing_monitoring = fields.Boolean(
        default=False,
        help="When enabled, it will activate the ongoing monitoring service",
    )
    kyc_ongoing_monitoring_period = fields.Selection(
        selection=ONGOING_PERIODS,
        default="no",
        help="When enabled, it will activate the ongoing monitoring service",
    )
    kyc_last_scan_id = fields.Char(string="Last Scan ID")
    kyc_last_ongoing_monitoring = fields.Datetime()
    kyc_last_auto_ongoing_monitoring = fields.Datetime()
    kyc_next_ongoing_monitoring = fields.Datetime()
    is_government = fields.Boolean(string="Is Government?")
    kyc_scan_required = fields.Boolean(
        compute="_compute_kyc_scan_required",
        help="Indicates that a contact need to be considered for KYC scans and"
        "therefore KYC options need to be displayed",
    )

    def _compute_kyc_expiration_date(self):
        for rec in self:
            rec.kyc_expiration_date = (
                rec.kyc_last_scan + relativedelta(years=1)
                if rec.kyc_last_scan
                else False
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

    def action_kyc_enable_ongoing_monitoring(self):
        if not self.env["webservice.backend"].sudo().search([("is_kyc", "=", True)]):
            raise NotImplementedError()
        if self.kyc_ongoing_monitoring:
            raise UserError(_("KYC Ongoing Monitoring already enabled."))
        action = (
            self.env.ref("kyc.action_kyc_enable_ongoing_monitoring_wizard")
            .sudo()
            .read()[0]
        )
        action["context"] = {
            "default_partner_id": self.id,
        }
        return action

    def action_kyc_disable_ongoing_monitoring(self):
        if not self.env["webservice.backend"].sudo().search([("is_kyc", "=", True)]):
            raise NotImplementedError()
        if not self.kyc_ongoing_monitoring:
            raise UserError(_("KYC Ongoing Monitoring not enabled."))
        action = (
            self.env.ref("kyc.action_kyc_disable_ongoing_monitoring_wizard")
            .sudo()
            .read()[0]
        )
        action["context"] = {
            "default_partner_id": self.id,
        }
        return action

    def _get_scan_id_from_response(self, response):
        return []

    def _get_scan_id_from_text(self, text):
        return []

    def _get_request_dict(self, log_type):
        """summary of the request to be recorded in logs"""
        res = {}
        if log_type == "scan":
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
        elif log_type == "ongoing":
            res = {
                "scan_id": self.kyc_last_scan_id,
            }
        elif log_type == "enable_om":
            res = {
                "scan_id": self.kyc_last_scan_id,
                "period_id": self.kyc_ongoing_monitoring_period,
            }
        elif log_type == "disable_om":
            res = {
                "scan_id": self.kyc_last_scan_id,
            }
        return res

    def _action_kyc_scan(self, is_auto_call=False):
        self.ensure_one()
        backend = self._get_kyc_webservice_backend()
        if not backend:
            raise UserError(
                _("KYC provider not configured. Contact your system administrator.")
            )
        # If the scan status was active and also the ongoing monitoring,
        # it will disable the ongoing monitoring to avoid errors
        if self.kyc_status in ["sanction", "ok"] and self.kyc_ongoing_monitoring:
            self.env["kyc.disable.ongoing.monitoring"].create(
                {"partner_id": self.id}
            ).action_kyc_disable_ongoing_monitoring()
        kyc_status, response = backend.sudo().call("scan", self)
        self.env["kyc.process.log"].sudo().create(
            {
                "req_data": self._get_request_dict("scan"),
                "res_data": response,
                "author_id": self.env.user.id,
                "partner_id": self.id,
                "kyc_result": kyc_status,
                "type": "scan",
            }
        )
        vals = {"kyc_status": kyc_status}
        if len(response) > 0:
            if not self.is_company:
                vals["kyc_last_scan_id"] = self._get_scan_id_from_response(response)
            else:
                vals["kyc_last_scan_id"] = self._get_scan_id_from_response(response[0])
                for i in range(0, len(response[1:])):
                    self.ultimate_beneficial_owner_ids[
                        i
                    ].kyc_last_scan_id = self._get_scan_id_from_response(
                        response[i + 1]
                    )
        if not is_auto_call:
            vals.update({"kyc_last_scan": datetime.now()})
        else:
            vals.update({"kyc_last_auto_scan": datetime.now()})
        self.write(vals)
        self.update_kyc_ongoing_monitoring()

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
            ("kyc_auto_scan", "=", True),
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
                ("kyc_last_auto_scan", "<", cut_date),
                "&",
                ("kyc_last_auto_scan", "=", False),
                ("kyc_last_scan", "<", cut_date),
            ]
        )
        partners = self.env["res.partner"].search(domain)
        for partner in partners:
            partner._action_kyc_scan(is_auto_call=True)
            if auto_commit:
                self._cr.commit()  # pylint: disable=E8102

    def _get_next_ongoing_monitoring_from_response(self, response):
        return False

    @api.model
    def _get_domain_auto_ongoing_monitoring(self):
        return [
            ("kyc_ongoing_monitoring", "=", True),
            ("kyc_ongoing_monitoring_period", "!=", "no"),
        ]

    @api.model
    def auto_ongoing_monitoring(self, domain=False):
        auto_commit = not getattr(threading.currentThread(), "testing", False)
        if not domain:
            domain = self._get_domain_auto_ongoing_monitoring()
        partners = (
            self.env["res.partner"]
            .search(domain)
            .filtered(
                lambda x: (
                    (x.kyc_last_ongoing_monitoring or datetime(2000, 1, 1, 8, 0, 0))
                    <= fields.Datetime.today()
                    - PERIODS_TIMEDELTA[x.kyc_ongoing_monitoring_period]
                    or not x.kyc_last_ongoing_monitoring
                )
                and (
                    (
                        x.kyc_last_auto_ongoing_monitoring
                        or datetime(2000, 1, 1, 8, 0, 0)
                    )
                    <= fields.Datetime.today()
                    - PERIODS_TIMEDELTA[x.kyc_ongoing_monitoring_period]
                    or not x.kyc_last_auto_ongoing_monitoring
                )
            )
        )
        for partner in partners:
            partner.action_kyc_ongoing_monitoring(is_auto_call=True)
            if auto_commit:
                self._cr.commit()  # pylint: disable=E8102

    @api.model
    def cron_kyc_reset_expired(self):
        partners = self.env["res.partner"].search([("kyc_is_expired", "=", True)])
        partners.write({"kyc_status": "pending"})

    def action_kyc_ongoing_monitoring(self, is_auto_call=False):
        self.ensure_one()
        backend = self._get_kyc_webservice_backend()
        if not backend:
            raise UserError(
                _("KYC provider not configured. Contact your system administrator.")
            )
        kyc_status, response = backend.sudo().call(
            "ongoing_monitoring", self, self.kyc_last_scan_id
        )
        self.env["kyc.process.log"].sudo().create(
            {
                "req_data": self._get_request_dict("ongoing"),
                "res_data": response,
                "author_id": self.env.user.id,
                "partner_id": self.id,
                "kyc_result": kyc_status,
                "type": "ongoing",
            }
        )
        vals = {
            "kyc_status": kyc_status,
            "kyc_next_ongoing_monitoring": self._get_next_ongoing_monitoring_from_response(
                response
            ),
        }
        if not is_auto_call:
            vals["kyc_last_ongoing_monitoring"] = datetime.now()
        else:
            vals["kyc_last_auto_ongoing_monitoring"] = datetime.now()
        self.write(vals)
        self.update_kyc_ongoing_monitoring()

    def update_kyc_ongoing_monitoring(self):
        if (
            self.env.company.kyc_auto_ongoing_monitoring != "no"
            and self.kyc_status == "ok"
            and not self.is_government
            and not self.kyc_ongoing_monitoring
            and not self.kyc_is_expired
        ):
            self.env["kyc.enable.ongoing.monitoring"].create(
                {
                    "period_id": self.env.company.kyc_auto_ongoing_monitoring,
                    "partner_id": self.id,
                }
            ).action_kyc_enable_ongoing_monitoring()
        elif (
            self.kyc_status != "ok" and self.kyc_ongoing_monitoring
        ) or self.kyc_is_expired:
            self.env["kyc.disable.ongoing.monitoring"].create(
                {"partner_id": self.id}
            ).action_kyc_disable_ongoing_monitoring()

    @api.model
    def action_update_last_scan_ids(self):
        for res in self.search(
            [
                ("kyc_status", "!=", "pending"),
                "|",
                ("kyc_last_scan", "!=", False),
                ("kyc_last_auto_scan", "!=", False),
            ]
        ):
            last_log = self.env["kyc.process.log"].search(
                [("partner_id", "=", res.id), ("type", "in", ["scan", False])],
                order="create_date DESC",
                limit=1,
            )
            response = self._get_scan_id_from_text(last_log.res_data)
            if len(response) > 0:
                res.kyc_last_scan_id = response[0]
                if res.is_company:
                    for i in range(0, len(response[1:])):
                        res.ultimate_beneficial_owner_ids[
                            i
                        ].kyc_last_scan_id = response[i + 1]
