# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from freezegun import freeze_time

from .common import TestKycCommon


class TestKyc(TestKycCommon):
    def setUp(self):
        super().setUp()

    def test_01_scan_ok_result(self):
        self.assertEqual(self.test_contact.kyc_status, "pending")
        self.assertFalse(self.test_contact.kyc_last_scan)
        logs_before = self.scan_log_model.search([])
        self._simulate_scan_partner()
        self.assertEqual(self.test_contact.kyc_status, "ok")
        logs_after = self.scan_log_model.search([])
        new_log = logs_after - logs_before
        self.assertEqual(len(new_log), 1)
        self.assertEqual(new_log.kyc_result, "ok")
        self.assertTrue(self.test_contact.kyc_last_scan)

    @freeze_time("2023-01-26 10:00:00")
    def test_02_expiring_warning(self):
        current_datetime = datetime.now()
        self._simulate_scan_partner()
        self.assertEqual(self.test_contact.kyc_status, "ok")
        self.assertEqual(self.test_contact.kyc_last_scan, current_datetime)
        self.assertFalse(self.test_contact.kyc_is_about_expire)
        self.assertFalse(self.test_contact.kyc_is_expired)
        # About to expire:
        self.test_contact.kyc_last_scan = datetime(2022, 1, 27, 9, 0)
        self.test_contact.invalidate_cache()
        self.assertTrue(self.test_contact.kyc_is_about_expire)
        self.assertFalse(self.test_contact.kyc_is_expired)
        search_res = self.partner_model.search([("kyc_is_about_expire", "=", True)])
        self.assertTrue(self.test_contact in search_res)
        search_res = self.partner_model.search([("kyc_is_expired", "=", True)])
        self.assertTrue(self.test_contact not in search_res)
        # Just expired:
        self.test_contact.kyc_last_scan = datetime(2022, 1, 26, 9, 0)
        self.test_contact.invalidate_cache()
        self.assertFalse(self.test_contact.kyc_is_about_expire)
        self.assertTrue(self.test_contact.kyc_is_expired)
        search_res = self.partner_model.search([("kyc_is_about_expire", "=", True)])
        self.assertTrue(self.test_contact not in search_res)
        search_res = self.partner_model.search([("kyc_is_expired", "=", True)])
        self.assertTrue(self.test_contact in search_res)

    def test_03_auto_scan_partners(self):
        self.assertFalse(self.test_company.kyc_last_scan)
        self.assertFalse(self.test_company.kyc_last_auto_scan)
        # Not auto-scan partners that haven't been scanned yet.
        self._simulate_auto_scan_cron()
        self.assertFalse(self.test_company.kyc_last_scan)
        self.assertFalse(self.test_company.kyc_last_auto_scan)
        # Not auto-scan partners just after the first scan.
        self._simulate_scan_partner(partner=self.test_company)
        self.assertTrue(self.test_company.kyc_last_scan)
        self._simulate_auto_scan_cron()
        self.assertFalse(self.test_company.kyc_last_auto_scan)
        # Auto-scan is valid one month after first manual scan:
        self.test_company.kyc_last_scan -= timedelta(days=31)
        self._simulate_auto_scan_cron()
        self.assertTrue(self.test_company.kyc_last_auto_scan)
