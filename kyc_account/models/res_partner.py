# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _kyc_accept_transaction(self, record, raise_if_not=True):
        self.ensure_one()
        if record and record._name == "account.move" and record.move_type == "entry":
            return True
        return super()._kyc_accept_transaction(record, raise_if_not=raise_if_not)
