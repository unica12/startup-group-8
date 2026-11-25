import ssl
import unittest

from asyncpg import InvalidPasswordError, UniqueViolationError
from sqlalchemy.exc import DBAPIError

from database.startup import startup_failure


class StartupDiagnosticsTests(unittest.TestCase):
    def test_unwraps_asyncpg_error_without_printing_details(self):
        raw = UniqueViolationError("private-value")
        adapter = RuntimeError("private-adapter-detail")
        adapter.__cause__ = raw
        wrapped = DBAPIError("private-statement", {"data": "private-param"}, adapter)

        message = startup_failure("migration.users", wrapped)
        self.assertIn("stage=migration.users, category=migration", message)
        self.assertIn("driver=UniqueViolationError, sqlstate=23505", message)
        self.assertNotIn("private-", message)

    def test_recognizes_password_failure_during_connect(self):
        message = startup_failure("connect", InvalidPasswordError("private-password-detail"))
        self.assertIn("category=authentication", message)
        self.assertIn("driver=InvalidPasswordError, sqlstate=28P01", message)
        self.assertNotIn("private-", message)

    def test_recognizes_wrapped_tls_error_without_sqlstate(self):
        error = DBAPIError(None, None, ssl.SSLCertVerificationError("private-certificate-detail"))
        message = startup_failure("connect", error)
        self.assertIn("category=tls", message)
        self.assertIn("driver=SSLCertVerificationError, sqlstate=-", message)
        self.assertNotIn("private-", message)

    def test_select_one_has_its_own_stage_and_rejects_invalid_sqlstate(self):
        error = RuntimeError("private-query-detail")
        error.sqlstate = "private-non-code"
        message = startup_failure("select_1", error)
        self.assertIn("stage=select_1", message)
        self.assertIn("sqlstate=-", message)
        self.assertNotIn("private-", message)
