import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from security import hash_pin, validate_pin, verify_pin  # noqa: E402


class SecurityTests(unittest.TestCase):
    def test_pin_policy_accepts_expected_values(self):
        self.assertTrue(validate_pin("Abc1"))
        self.assertTrue(validate_pin("Abc@1234"))
        self.assertTrue(validate_pin("A1!@#$%^&*()_+-"))

    def test_pin_policy_rejects_invalid_values(self):
        self.assertFalse(validate_pin("abc"))
        self.assertFalse(validate_pin("a" * 17))
        self.assertFalse(validate_pin("中文1234"))
        self.assertFalse(validate_pin("abc 1234"))

    def test_pin_hash_roundtrip(self):
        salt, digest = hash_pin("Abc@1234")
        self.assertTrue(verify_pin("Abc@1234", salt, digest))
        self.assertFalse(verify_pin("Wrong@123", salt, digest))


if __name__ == "__main__":
    unittest.main()
