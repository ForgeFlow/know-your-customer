# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class KYCFileUpload(models.TransientModel):
    _name = "kyc.file.upload"
    _description = "KYC File Upload"

    file = fields.Binary()
    filename = fields.Char()
    partner_id = fields.Many2one("res.partner")
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
    kyc_ubo_id = fields.Many2one("kyc.ubo", string="UBO")

    def upload_file(self):
        attachment = self.env["ir.attachment"].create(
            {"name": self.filename, "datas": self.file}
        )
        kyc_doc = self.env["kyc.document"].create(
            {
                "attachment_id": attachment.id,
                "name": self.filename,
                "document_type": self.document_type,
                "kyc_ubo_id": self.kyc_ubo_id and self.kyc_ubo_id.id or False,
            }
        )
        self.partner_id.kyc_document_ids += kyc_doc
