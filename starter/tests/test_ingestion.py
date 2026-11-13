import unittest
from pathlib import Path

from src.ingestion import load_pdf, normalize_text


class IngestionTests(unittest.TestCase):
    def test_normalize_text_keeps_content_and_collapses_whitespace(self):
        text = "  Energy\u00a0 prices\n\nare   forecasted.  "
        self.assertEqual(normalize_text(text), "Energy prices\nare forecasted.")

    def test_load_pdf_returns_pages_with_source_metadata(self):
        pdf = Path("data/raw/CMO-October-2026.pdf")
        pages = load_pdf(pdf, "cmo-october-2026", str(pdf))

        self.assertEqual(len(pages), 70)
        self.assertEqual(pages[8].document_id, "cmo-october-2026")
        self.assertEqual(pages[8].source, str(pdf))
        self.assertEqual(pages[8].page, 9)
        self.assertIn("EXECUTIVE SUMMARY", pages[8].text)


if __name__ == "__main__":
    unittest.main()
