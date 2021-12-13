# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Know Your Customer",
    "version": "14.0.1.1.0",
    "summary": "Know Your Customer (KYC).",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/know-your-customer",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "category": "KYC",
    "depends": ["webservice", "base_setup", "contacts"],
    "data": [
        "security/kyc_security.xml",
        "security/ir.model.access.csv",
        "data/cron.xml",
        "data/sequence.xml",
        "wizard/kyc_file_upload_view.xml",
        "views/res_partner_view.xml",
        "views/kyc_log_view.xml",
        "views/res_config_settings_views.xml",
        "wizard/kyc_partner_scan_view.xml",
    ],
    "installable": True,
}
