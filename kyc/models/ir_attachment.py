# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def download_file(self):
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % (self.id),
            "target": "self",
            "nodestroy": False,
        }
