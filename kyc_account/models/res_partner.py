# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _kyc_accept_transaction(self, _record, raise_if_not=True):
        self.ensure_one()
        if _record and _record._name == "account.move" and _record.move_type == "entry":
            return True
        return super(ResPartner, self)._kyc_accept_transaction(_record, raise_if_not)
