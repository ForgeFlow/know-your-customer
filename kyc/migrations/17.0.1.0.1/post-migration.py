from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """
    Force attachemnts to be related to linked kyc document
    See https://github.com/odoo/odoo/issues/203580
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    documents = env["kyc.document"].search([])
    for document in documents:
        document.attachment_id.write(
            {"res_id": document.id, "res_model": "kyc.document"}
        )
