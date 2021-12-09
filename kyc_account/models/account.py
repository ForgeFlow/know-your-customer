# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id and self.partner_id.is_expire:
            raise UserError(_("%s's KYC status is expired." % (self.partner_id.name)))
        return super(AccountMove, self)._onchange_partner_id()


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id and self.partner_id.is_expire:
            raise UserError(_("%s's KYC status is expired." % (self.partner_id.name)))
