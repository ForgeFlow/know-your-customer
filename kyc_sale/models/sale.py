# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_id._kyc_accept_transaction()
        return super(SaleOrder, self).onchange_partner_id()

    def action_confirm(self):
        for rec in self:
            rec.partner_id._kyc_accept_transaction()
        return super().action_confirm()
