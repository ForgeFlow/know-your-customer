# Copyright 2021-23 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    kyc_is_about_expire = fields.Boolean(related="partner_id.kyc_is_about_expire")
    kyc_is_expired = fields.Boolean(related="partner_id.kyc_is_expired")
    kyc_is_about_to_expire_msg = fields.Char(
        related="partner_id.kyc_is_about_to_expire_msg"
    )

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_id._kyc_accept_transaction(self)
        return super(SaleOrder, self).onchange_partner_id()

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.partner_id._kyc_accept_transaction(self)
        return super().copy(default=default)

    def action_confirm(self):
        for rec in self:
            rec.partner_id._kyc_accept_transaction(rec)
        return super().action_confirm()
