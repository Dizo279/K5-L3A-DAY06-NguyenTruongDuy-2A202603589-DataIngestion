import unittest

from src.chunking import by_paragraph, fixed_size
from src.models import DocumentPage


class ChunkingTests(unittest.TestCase):
    def setUp(self):
        self.page = DocumentPage(
            document_id="doc-1",
            source="source.pdf",
            page=3,
            text="abcdefghij",
            metadata={"section": "Energy", "year": 2026},
        )

    def test_fixed_size_uses_overlap_and_retains_metadata(self):
        chunks = fixed_size(self.page, size=6, overlap=2)

        self.assertEqual([chunk.text for chunk in chunks], ["abcdef", "efghij"])
        self.assertEqual(chunks[0].chunk_id, "doc-1-p3-fixed-0000")
        self.assertEqual(chunks[0].metadata, self.page.metadata)
        self.assertEqual(chunks[0].page, 3)

    def test_by_paragraph_groups_small_paragraphs(self):
        page = DocumentPage(
            document_id="doc-1",
            source="source.pdf",
            page=3,
            text="First paragraph.\n\nSecond paragraph.",
            metadata={"section": "Energy"},
        )

        chunks = by_paragraph(page, max_size=40)

        self.assertEqual(len(chunks), 1)
        self.assertIn("First paragraph.", chunks[0].text)
        self.assertIn("Second paragraph.", chunks[0].text)
        self.assertEqual(chunks[0].chunk_id, "doc-1-p3-paragraph-0000")
        self.assertEqual(chunks[0].metadata, {"section": "Energy"})

    def test_rejects_invalid_fixed_size_arguments(self):
        with self.assertRaises(ValueError):
            fixed_size(self.page, size=0, overlap=0)
        with self.assertRaises(ValueError):
            fixed_size(self.page, size=5, overlap=5)


if __name__ == "__main__":
    unittest.main()
