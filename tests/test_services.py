from app.services.credibility import score_sources
from app.services.knowledge import chunk_text, cosine, embed


def test_source_scoring_deduplicates_and_counts_citations():
    text = (
        "See https://www.nih.gov/study and https://example.com/post. "
        "Again https://www.nih.gov/study."
    )
    sources = score_sources(text)
    assert len(sources) == 2
    assert sources[0]["domain"] == "nih.gov"
    assert sources[0]["citation_count"] == 2
    assert sources[0]["credibility_score"] > sources[1]["credibility_score"]


def test_local_embedding_prefers_related_text():
    query = embed("solar energy storage")
    related = cosine(query, embed("solar battery energy storage systems"))
    unrelated = cosine(query, embed("renaissance painting and sculpture"))
    assert related > unrelated


def test_chunking_preserves_content():
    text = "\n\n".join(f"Paragraph {index} with useful details." for index in range(20))
    chunks = chunk_text(text, size=140, overlap=20)
    assert len(chunks) > 1
    assert "Paragraph 0" in chunks[0]
