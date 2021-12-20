# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class KYCDocument(models.Model):
    _name = "kyc.document"

    name = fields.Char()
    partner_id = fields.Many2one("res.partner", string="Contact")
    document_type = fields.Selection(
        [
            ("passport", "Passport"),
            ("id_card", "ID Card"),
            ("ubo_own_certificate", "UBO ownership certificate"),
            ("ubo_passport", "UBO Passport"),
            ("scan_certificate", "Scan certificate"),
            ("other", "Other"),
        ]
    )
    attachment_id = fields.Many2one("ir.attachment", string="Attachment")
    kyc_ubo_id = fields.Many2one("kyc.ubo", string="UBO")

    def download_file(self):
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % (self.attachment_id.id),
            "target": "self",
            "nodestroy": False,
        }
