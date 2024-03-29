# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_id.commercial_partner_id._kyc_accept_transaction(self)
        return super()._onchange_partner_id()

    def _post(self, soft=True):
        for rec in self:
            if rec.partner_id:
                rec.partner_id.commercial_partner_id._kyc_accept_transaction(rec)
        return super()._post(soft=soft)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_id.commercial_partner_id._kyc_accept_transaction(self)
