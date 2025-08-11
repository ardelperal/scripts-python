import unittest
from unittest.mock import Mock, patch

from common.email.registration_service import register_standard_report


class TestRegistrationService(unittest.TestCase):
    @patch("email_services.email_manager.EmailManager.register_email", return_value=True)
    def test_register_standard_report_success(self, mock_reg):
        logger = Mock()
        ok = register_standard_report(
            Mock(),
            application="EXPEDIENTES",
            subject="Subj",
            body_html="<html></html>",
            recipients="user@test",
            logger=logger,
        )
        self.assertTrue(ok)
        mock_reg.assert_called_once()
        logger.info.assert_called()

    @patch(
        "email_services.email_manager.EmailManager.register_email",
        side_effect=Exception("db fail"),
    )
    def test_register_standard_report_exception(self, _mock_reg):
        logger = Mock()
        ok = register_standard_report(
            Mock(),
            application="EXPEDIENTES",
            subject="Subj",
            body_html="<html></html>",
            recipients="user@test",
            logger=logger,
        )
        self.assertFalse(ok)
        logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()
