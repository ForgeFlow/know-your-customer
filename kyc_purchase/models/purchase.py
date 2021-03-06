# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_id._kyc_accept_transaction(self)
        return super().onchange_partner_id()

    def button_confirm(self):
        for rec in self:
            rec.partner_id._kyc_accept_transaction(rec)
        return super().button_confirm()
