# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _kyc_accept_transaction(self, _record, raise_if_not=True):
        self.ensure_one()
        if self.env.context.get("_skip_kyc_check", False):
            return True
        return super(ResPartner, self)._kyc_accept_transaction(_record, raise_if_not)
