# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from .res_partner import KYC_STATUSES


class KYCProcessLog(models.Model):
    _name = "kyc.process.log"

    name = fields.Char(
        copy=False,
        default=lambda self: self.env["ir.sequence"].next_by_code("kyc.process.log"),
    )
    req_data = fields.Text("Request")
    res_data = fields.Text("Response")
    kyc_result = fields.Selection(selection=KYC_STATUSES)
    author_id = fields.Many2one("res.users")
    partner_id = fields.Many2one("res.partner", "Contact")


class KYCStatusOverrideLog(models.Model):
    _name = "kyc.status.override.log"

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
