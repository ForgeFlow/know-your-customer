# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.company"

    kyc_webservice_backend_id = fields.Many2one(
        comodel_name="webservice.backend", domain="[('is_kyc', '=', True)]"
    )
    # TODO: make this configurable in settings wizard.
