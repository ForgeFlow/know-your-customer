# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WebserviceBackend(models.Model):
    _inherit = "webservice.backend"

    is_kyc = fields.Boolean()

    def _get_adapter(self):
        if self.is_kyc:
            with self.work_on(self._name) as work:
                return work.component(
                    usage="kyc.scan", webservice_protocol=self.protocol
                )
        return super()._get_adapter()
