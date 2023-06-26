# Copyright 2021-23 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from .res_partner import KYC_STATUSES


class KYCProcessLog(models.Model):
    _name = "kyc.process.log"
    _description = "KYC Process Log"
    _order = "id desc"

    name = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.sequence"].next_by_code("kyc.process.log"),
    )
    req_data = fields.Text("Request")
    res_data = fields.Text("Response")
    kyc_result = fields.Selection(selection=KYC_STATUSES)
    type = fields.Selection(
        selection=[
            ("scan", "Scan"),
            ("ongoing", "Ongoing Monitoring"),
            ("enable_om", "Enable Ongoing Monitoring"),
            ("disable_om", "Disable Ongoing Monitoring"),
        ],
        default=False,
    )
    author_id = fields.Many2one("res.users")
    scan_id = fields.Char(string="Scan ID")
    partner_id = fields.Many2one("res.partner", "Contact")


class KYCStatusOverrideLog(models.Model):
    _name = "kyc.status.override.log"
    _description = "KYC Status Override Log"
    _order = "id desc"

    name = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "kyc.status.override.log"
        ),
    )
    old_status = fields.Char("Old Status")
    new_status = fields.Char("New Status")
    override_reason = fields.Char()
    author_id = fields.Many2one("res.users")
    partner_id = fields.Many2one("res.partner", "Contact")
