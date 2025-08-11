import unittest
from unittest.mock import Mock, patch

from common.email.recipients_service import EmailRecipientsService


class TestEmailRecipientsService(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.config = Mock()
        self.logger = Mock()
        self.service = EmailRecipientsService(self.db, self.config, self.logger)

    @patch(
        "common.email.recipients_service._utils.get_admin_emails_string",
        return_value="a@b;c@d",
    )
    def test_get_admin_emails(self, _mock):
        self.assertEqual(self.service.get_admin_emails(), ["a@b", "c@d"])
        self.assertEqual(self.service.get_admin_emails_string(), "a@b;c@d")

    @patch(
        "common.email.recipients_service._utils.get_technical_emails_string",
        return_value="tec1@test;tec2@test",
    )
    def test_get_technical_emails(self, _mock):
        self.assertEqual(
            self.service.get_technical_emails(), ["tec1@test", "tec2@test"]
        )

    def test_get_quality_emails_without_app_id(self):
        self.assertEqual(self.service.get_quality_emails(), [])

    @patch(
        "common.email.recipients_service._utils.get_quality_emails_string",
        return_value="q1@test;q2@test",
    )
    def test_get_quality_emails_with_app_id(self, _mock):
        self.assertEqual(self.service.get_quality_emails("APP"), ["q1@test", "q2@test"])


if __name__ == "__main__":
    unittest.main()
