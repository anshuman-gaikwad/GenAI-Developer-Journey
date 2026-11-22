"""Tests for GrahakNyay retrieval configuration."""

from unittest.mock import patch

import pytest

from app.rag import retrieve_legal_chunks


def test_tfidf_retrieval(monkeypatch):
    """TF-IDF mode converts legal records into RAG chunks."""
    monkeypatch.setenv("GRAHAKNYAY_RETRIEVAL", "tfidf")

    fake_records = [
        {
            "provision_title": "Unfair Trade Practice",
            "document_name": "Consumer Protection Act, 2019",
            "section_or_rule": "Section 2(47)",
            "plain_summary": "An unfair or deceptive trade practice.",
        }
    ]

    with patch("app.rag.rank_records", return_value=fake_records) as mock_search:
        chunks = retrieve_legal_chunks("unfair trade practice", top_k=3)

    mock_search.assert_called_once_with("unfair trade practice", top_k=3)

    assert len(chunks) == 1
    assert chunks[0]["title"] == "Unfair Trade Practice"
    assert chunks[0]["source"] == "Consumer Protection Act, 2019"
    assert chunks[0]["page"] == "Section 2(47)"


def test_semantic_retrieval(monkeypatch):
    """Semantic mode continues using the original vector search."""
    monkeypatch.setenv("GRAHAKNYAY_RETRIEVAL", "semantic")

    fake_chunks = [
        {
            "title": "Consumer Protection Act",
            "source": "consumer_protection_act_2019.pdf",
            "page": 7,
            "text": "Sample legal text.",
        }
    ]

    with patch("app.rag.semantic_search", return_value=fake_chunks) as mock_search:
        chunks = retrieve_legal_chunks("consumer rights", top_k=3)

    mock_search.assert_called_once_with("consumer rights", top_k=3)
    assert chunks == fake_chunks


def test_invalid_retrieval_mode(monkeypatch):
    """Invalid retrieval configuration produces a clear error."""
    monkeypatch.setenv("GRAHAKNYAY_RETRIEVAL", "invalid")

    with pytest.raises(ValueError, match="Invalid GRAHAKNYAY_RETRIEVAL"):
        retrieve_legal_chunks("consumer rights")