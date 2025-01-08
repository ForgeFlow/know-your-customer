# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class KYCUBO(models.Model):
    _name = "kyc.ubo"
    _description = "KYC Ultimate Beneficial Owner"

    name = fields.Char(required=True)
    birthdate = fields.Date(required=True)
    partner_id = fields.Many2one("res.partner", string="Contact")
    kyc_last_scan_id = fields.Char(string="Last Scan ID")
