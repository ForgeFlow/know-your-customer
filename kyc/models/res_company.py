# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

ONGOING_PERIODS = [
    ("no", "No"),
    ("1", "Daily"),
    ("2", "Weekly"),
    ("3", "Monthly"),
    ("4", "Quarterly"),
    ("5", "Half Year"),
    ("6", "Yearly"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    kyc_webservice_backend_id = fields.Many2one(
        comodel_name="webservice.backend", domain="[('is_kyc', '=', True)]"
    )

    kyc_auto_ongoing_monitoring = fields.Selection(
        selection=ONGOING_PERIODS,
        default="no",
        readonly=False,
        string="KYC Auto Ongoing Monitoring",
        help="When a scan is done, it will enable automatically "
        "ongoing monitoring based on this .",
    )
    # TODO: make this configurable in settings wizard.
