from odoo import models


class KYCProcessLog(models.Model):
    _inherit = "kyc.process.log"

    def create(self, vals):
        res = vals.get("res_data", {})
        call_type = vals.get("type")
        if len(res) != 1 and type(res) is not dict:
            res = res[0]
        if call_type == "ongoing":
            if res.get("Result", {}).get("ReferenceNumber", False):
                vals["scan_id"] = res["Result"]["ReferenceNumber"]
        return super().create(vals)
