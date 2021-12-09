# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.is_expire:
            raise UserError(_("%s's KYC status is expired." % (self.partner_id.name)))
        return super(PurchaseOrder, self).onchange_partner_id()
