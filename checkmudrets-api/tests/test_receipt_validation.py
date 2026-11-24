import io
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from PIL import Image
from pydantic import ValidationError

from schemas.receipt_input import ReceiptInput
from services.receipt_validation import from_ocr, validate_receipt


def weighted():
    return {
        "raw_name": "ЯБЛОКО ГАЛА", "name": "Яблоко Гала", "quantity": "0,384", "unit": "кг",
        "price": "599", "total": "220,02", "discount": "10,00", "category": "Овощи/Фрукты",
    }


class ReceiptValidationTests(unittest.TestCase):
    def test_weighted_item_mixed_units_and_discounts(self):
        receipt, warnings = from_ocr({
            "date": date.today().isoformat(), "total": "305,02", "discount": "5.00", "items": [
                weighted(), {"raw_name": "НАПИТОК ТЕСТ 500МЛ", "name": "Напиток Тест 500 мл", "quantity": "2", "unit": "шт", "price": "45",
                             "total": "90", "category": "Напитки", "package_size": "500", "package_unit": "мл"},
            ],
        })
        self.assertEqual(warnings, [])
        self.assertEqual(receipt.items[0].quantity, Decimal("0.384"))
        self.assertEqual(receipt.items[0].price, Decimal("599"))
        self.assertEqual(receipt.items[0].total, Decimal("220.02"))
        self.assertEqual(receipt.items[1].package_size, Decimal("500"))

    def test_material_arithmetic_discrepancies_keep_printed_values(self):
        receipt, warnings = from_ocr({
            "date": date.today().isoformat(), "total": "600", "items": [weighted() | {"total": "599"}],
        })
        self.assertEqual(receipt.total, Decimal("600"))
        self.assertEqual(receipt.items[0].total, Decimal("599"))
        self.assertEqual(sum(warning.retry for warning in warnings), 2)

    def test_unknown_values_and_invalid_source_fields(self):
        receipt, warnings = from_ocr({
            "date": "2026-02-31", "total": None, "items": [
                {"name": None, "category": "Выдумка", "price": "NaN", "quantity": "-2", "total": "9"},
            ],
        })
        self.assertIsNone(receipt.date)
        self.assertIsNone(receipt.total)
        self.assertIsNone(receipt.items[0].name)
        self.assertIsNone(receipt.items[0].price)
        self.assertIsNone(receipt.items[0].quantity)
        self.assertTrue(any(warning.blocking and "категорию" in warning.message for warning in warnings))
        with self.assertRaises(ValidationError):
            ReceiptInput.model_validate({"date": 1, "items": []})

    def test_excludes_service_lines_but_keeps_a_real_product(self):
        receipt, warnings = from_ocr({
            "date": date.today().isoformat(), "total": "220.02", "items": [
                {"name": "НДС 20%", "total": "40"}, {"name": "ФН 123"}, {"name": "Скидка 10"},
                {"name": "Оплата картой"}, weighted(),
            ],
        })
        self.assertEqual(len(receipt.items), 1)
        self.assertEqual(warnings, [])
        manual = receipt.model_copy(update={"items": [receipt.items[0].model_copy(update={"name": "НДС 20%"})]})
        self.assertTrue(any(warning.blocking for warning in validate_receipt(manual)))

    def test_model_name_cannot_remove_pack_size_or_add_words(self):
        raw = {"raw_name": "2. НАПИТОК ТЕСТ 500МЛ", "name": "Напиток Тест вкусный", "brand": "Тест"}
        receipt, _ = from_ocr({"items": [raw, raw | {"raw_name": None}]})
        self.assertEqual(receipt.items[0].name, "НАПИТОК ТЕСТ 500 мл")
        self.assertEqual(receipt.items[0].raw_name, raw["raw_name"])
        self.assertIsNone(receipt.items[1].name)
        self.assertIsNone(receipt.items[1].brand)


class OCRTests(unittest.IsolatedAsyncioTestCase):
    async def test_repeats_once_with_specific_feedback_and_keeps_values(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-only", "PYTHON_DOTENV_DISABLED": "1"}):
            from services.ocr import recognize_receipt
        image = io.BytesIO()
        Image.new("RGB", (32, 32), color="white").save(image, format="PNG")
        raw = {"success": True, "date": date.today().isoformat(), "total": "210.02", "items": [weighted()]}
        scan = AsyncMock(side_effect=[raw, raw])
        with patch("services.ocr._request_scan", scan):
            receipt, warnings, retried = await recognize_receipt(image.getvalue())
        self.assertTrue(retried)
        self.assertEqual(scan.await_count, 2)
        self.assertIn("210,02", scan.await_args.args[1][0])
        self.assertEqual(receipt.total, Decimal("210.02"))
        self.assertTrue(any(warning.retry for warning in warnings))

    async def test_unknown_fields_do_not_spend_a_retry(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-only", "PYTHON_DOTENV_DISABLED": "1"}):
            from services.ocr import recognize_receipt
        image = io.BytesIO()
        Image.new("RGB", (32, 32), color="white").save(image, format="PNG")
        raw = {"success": True, "date": None, "total": None,
               "items": [{"raw_name": "Яблоко", "name": "Яблоко", "category": "Овощи/Фрукты"}]}
        scan = AsyncMock(return_value=raw)
        with patch("services.ocr._request_scan", scan):
            _, warnings, retried = await recognize_receipt(image.getvalue())
        self.assertFalse(retried)
        self.assertEqual(scan.await_count, 1)
        self.assertTrue(any(warning.blocking for warning in warnings))
