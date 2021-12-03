# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class KYCFileUpload(models.TransientModel):
    _name = "kyc.file.upload"
    _description = "KYC File Upload"

    file = fields.Binary()
    filename = fields.Char()
    partner_id = fields.Many2one("res.partner")

    def upload_file(self):
        attachment = self.env["ir.attachment"].create(
            {"name": self.filename, "datas": self.file}
        )
        self.partner_id.attachment_ids += attachment
