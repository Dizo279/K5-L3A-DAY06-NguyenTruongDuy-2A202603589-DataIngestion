import unittest

from src.evaluation import evaluate_query, summarize


class EvaluationTests(unittest.TestCase):
    question = {
        "id": "q01",
        "split": "dev",
        "gold_source_id": "doc-1",
        "gold_page": 3,
        "evidence_quote": "target evidence",
    }

    def test_evaluate_query_marks_top1_and_top3_evidence_hits(self):
        hits = [
            {"chunk_id": "c1", "document_id": "doc-1", "page": 3, "text": "target evidence here", "score": 0.9},
            {"chunk_id": "c2", "document_id": "doc-2", "page": 1, "text": "other", "score": 0.8},
        ]

        trace = evaluate_query(self.question, hits)

        self.assertTrue(trace["hit_at_1"])
        self.assertTrue(trace["evidence_hit_at_3"])
        self.assertEqual(trace["retrieved_chunk_ids"], ["c1", "c2"])

    def test_evaluate_query_accepts_evidence_found_only_at_top3(self):
        hits = [
            {"chunk_id": "c1", "document_id": "doc-2", "page": 1, "text": "other", "score": 0.9},
            {"chunk_id": "c2", "document_id": "doc-1", "page": 3, "text": "target evidence here", "score": 0.8},
        ]

        trace = evaluate_query(self.question, hits)

        self.assertFalse(trace["hit_at_1"])
        self.assertTrue(trace["evidence_hit_at_3"])

    def test_summarize_groups_by_strategy_and_split(self):
        traces = [
            {"strategy": "A", "split": "dev", "hit_at_1": True, "evidence_hit_at_3": True},
            {"strategy": "A", "split": "dev", "hit_at_1": False, "evidence_hit_at_3": True},
            {"strategy": "B", "split": "test", "hit_at_1": True, "evidence_hit_at_3": True},
        ]

        result = summarize(traces)

        self.assertEqual(result["A"]["dev"], {"count": 2, "hit_at_1": 1, "evidence_hit_at_3": 2})
        self.assertEqual(result["B"]["test"], {"count": 1, "hit_at_1": 1, "evidence_hit_at_3": 1})


if __name__ == "__main__":
    unittest.main()
