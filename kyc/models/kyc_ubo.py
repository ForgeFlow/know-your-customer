# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class KYCUBO(models.Model):
    _name = "kyc.ubo"

    name = fields.Char(required=1)
    birthdate = fields.Date(required=1)
    partner_id = fields.Many2one("res.partner", string="Contact")
