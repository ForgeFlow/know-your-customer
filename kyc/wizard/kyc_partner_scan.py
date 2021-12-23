# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class KYCPartnerScan(models.TransientModel):
    _name = "kyc.partner.scan"
    _description = "KYC Partner Scan"

    partner_id = fields.Many2one("res.partner", "Partner")
    ultimate_beneficial_owner_ids = fields.Many2many(
        "kyc.ubo", string="Ultimate beneficial owner"
    )
    birthdate_date = fields.Date(string="Date of Birth")
    nationality_id = fields.Many2one("res.country", "Nationality")
    kyc_status = fields.Selection(
        selection=[
            ("pending", "To Scan"),
            ("ok", "Validated"),
            ("sanction", "Sanction"),
            ("error", "Error"),
        ],
        default="pending",
    )
    status_override_reason = fields.Char()
    is_government = fields.Boolean(related="partner_id.is_government")

    def check_documents(self, partner):
        if partner.is_company and self.is_government:
            return True
        KYCDocumentObj = self.env["kyc.document"]
        documents = partner.kyc_document_ids
        validation_message = ""
        validation_messages = {
            "company": "Certificate of UBO ownership max 3-month-old + "
            "passports for each one is required to scan",
            "individual": "Passport or ID card is required to scan",
        }
        if not documents:
            if partner.is_company:
                validation_message = validation_messages["company"]
            else:
                validation_message = validation_messages["individual"]
        if partner.is_company:
            message = ""
            for ubo in self.ultimate_beneficial_owner_ids:
                is_required_certificate = False
                is_required_passport = False
                if not KYCDocumentObj.search(
                    [
                        ("partner_id", "=", partner.id),
                        ("kyc_ubo_id", "=", ubo.id),
                        ("document_type", "=", "ubo_own_certificate"),
                    ]
                ):
                    is_required_certificate = True
                if not KYCDocumentObj.search(
                    [
                        ("partner_id", "=", partner.id),
                        ("kyc_ubo_id", "=", ubo.id),
                        ("document_type", "=", "ubo_passport"),
                    ]
                ):
                    is_required_passport = True
                if is_required_passport:
                    message += "Passport"
                if is_required_certificate:
                    if not is_required_passport:
                        message += "UBO Own Certificate"
                    else:
                        message += " And UBO Own Certificate"
                if message:
                    message += " is required for %s\n" % (ubo.name)
            if message:
                validation_message = validation_messages["company"] + "\n" + message
        else:
            passport = KYCDocumentObj.search(
                [("partner_id", "=", partner.id), ("document_type", "=", "passport")]
            )
            id_card = KYCDocumentObj.search(
                [("partner_id", "=", partner.id), ("document_type", "=", "id_card")]
            )
            if not passport and not id_card:
                validation_message = validation_messages["individual"]
        if validation_message:
            raise ValidationError(_(validation_message))

    def scan(self):
        partner = self.partner_id
        self.check_documents(partner)
        fields_to_update = [
            "birthdate_date",
            "nationality_id",
        ]
        vals = {}
        for f in fields_to_update:
            if self.__getattribute__(f) != partner.__getattribute__(f):
                vals[f] = self.__getattribute__(f)
        if vals:
            partner.write(vals)
        self.ultimate_beneficial_owner_ids.filtered(
            lambda l: l.partner_id.id != partner.id
        ).write({"partner_id": partner.id})
        partner._action_kyc_scan()

    def override_kyc_status(self):
        self.partner_id.message_post(
            body=_(
                "<b>KYC Status Update from %s to %s</b><br/><b>Reason:</b>%s"
                % (
                    dict(self._fields["kyc_status"].selection).get(
                        self.partner_id.kyc_status
                    ),
                    dict(self._fields["kyc_status"].selection).get(self.kyc_status),
                    self.status_override_reason,
                )
            )
        )
        self.env["kyc.status.override.log"].sudo().create(
            {
                "old_status": dict(self._fields["kyc_status"].selection).get(
                    self.partner_id.kyc_status
                ),
                "new_status": dict(self._fields["kyc_status"].selection).get(
                    self.kyc_status
                ),
                "override_reason": self.status_override_reason,
                "author_id": self.env.user.id,
                "partner_id": self.partner_id.id,
            }
        )
        self.partner_id.write({"kyc_status": self.kyc_status})
