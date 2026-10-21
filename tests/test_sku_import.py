"""Jalankan: python -m unittest discover -s tests -v   (tanpa perlu database)."""
import io
import unittest

import pandas as pd

from services.exceptions import ValidationError
from services.sku_excel import parse_sku_file
from services.sku_validation import validate_sku_fields


class FakeUpload:
    """Meniru werkzeug FileStorage dari DataFrame."""

    def __init__(self, frame: pd.DataFrame, filename: str = "master.xlsx"):
        buffer = io.BytesIO()
        frame.to_excel(buffer, index=False)
        buffer.seek(0)
        self.stream, self.filename = buffer, filename


def make_file(rows, columns=("Item Number", "Description", "CPP"), filename="master.xlsx"):
    return FakeUpload(pd.DataFrame(rows, columns=list(columns)), filename)


class ValidationTests(unittest.TestCase):
    def test_valid(self):
        clean, errors = validate_sku_fields(" ITEM001 ", " Matcha ", "72")
        self.assertEqual(clean, {"item_id": "ITEM001", "description": "Matcha", "cpp": 72})
        self.assertEqual(errors, [])

    def test_invalid_cpp_values(self):
        for bad in (0, -5, "abc", "12.5", None, "", True):
            clean, errors = validate_sku_fields("A1", "Desc", bad)
            self.assertIsNone(clean, msg=f"cpp={bad!r}")
            self.assertEqual(errors[0]["field"], "cpp")

    def test_float_like_cpp_and_item_id_from_excel(self):
        clean, _ = validate_sku_fields("1001.0", "Desc", "24.0")
        self.assertEqual((clean["item_id"], clean["cpp"]), ("1001", 24))


class ExcelParsingTests(unittest.TestCase):
    def test_valid_file_with_messy_headers(self):
        upload = make_file([["ITEM001", "Matcha", 72], ["ITEM002", "Honey", 36]],
                           columns=(" item number ", "DESCRIPTION", "Cpp"))
        rows = parse_sku_file(upload)
        self.assertEqual([r["item_id"] for r in rows], ["ITEM001", "ITEM002"])
        self.assertEqual(rows[0]["cpp"], 72)

    def test_wrong_columns(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_sku_file(make_file([["A", "B", 1]], columns=("Item Number", "Desc", "Qty")))
        self.assertIn("Description", ctx.exception.message)
        self.assertIn("CPP", ctx.exception.message)

    def test_invalid_rows_report_excel_row_numbers(self):
        upload = make_file([["ITEM001", "Ok", 10], ["ITEM002", "Bad", 0], ["", "NoId", 5]])
        with self.assertRaises(ValidationError) as ctx:
            parse_sku_file(upload)
        rows = {(e["row"], e["field"]) for e in ctx.exception.errors}
        self.assertEqual(rows, {(3, "cpp"), (4, "item_id")})

    def test_duplicate_item_number(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_sku_file(make_file([["A1", "X", 1], ["A1", "Y", 2]]))
        self.assertEqual(ctx.exception.errors[0]["row"], 3)

    def test_blank_rows_ignored_and_empty_file_rejected(self):
        rows = parse_sku_file(make_file([["A1", "X", 1], [None, None, None]]))
        self.assertEqual(len(rows), 1)
        with self.assertRaises(ValidationError):
            parse_sku_file(make_file([[None, None, None]]))

    def test_wrong_extension_and_corrupt_file(self):
        with self.assertRaises(ValidationError):
            parse_sku_file(make_file([["A", "B", 1]], filename="data.csv"))
        fake = type("F", (), {"filename": "x.xlsx", "stream": io.BytesIO(b"not excel")})()
        with self.assertRaises(ValidationError):
            parse_sku_file(fake)


if __name__ == "__main__":
    unittest.main()
