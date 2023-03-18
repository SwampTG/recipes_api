"""
Test custom Django management and core commands.
"""
from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch("core.management.commands.wait_for_db.Command.check")
class CommandTest(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database until it's fully up."""
        patched_check.return_value = True

        call_command("wait_for_db")

        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delay(self, stub_sleep, mock_check):
        """Wait more if gets OperationalError"""
        mock_check.side_effect = (
            [Psycopg2Error] * 2 + [OperationalError] * 3 + [True]
        )  # 6 different calls, raising errors until the Last

        call_command("wait_for_db")
        self.assertEqual(mock_check.call_count, 6)
        mock_check.assert_called_with(databases=["default"])
