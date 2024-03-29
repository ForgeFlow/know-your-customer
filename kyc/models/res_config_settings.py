# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    kyc_webservice_backend_id = fields.Many2one(
        comodel_name="webservice.backend",
        domain="[('is_kyc', '=', True)]",
        related="company_id.kyc_webservice_backend_id",
        readonly=False,
        string="KYC Webservice",
        help="Choose KYC webservice for scan contacts.",
    )

    kyc_auto_ongoing_monitoring = fields.Selection(
        related="company_id.kyc_auto_ongoing_monitoring",
        readonly=False,
        string="KYC Auto Ongoing Monitoring",
        help="When a scan is done, it will enable automatically "
        "ongoing monitoring based on this .",
    )
