"""Tests for chunk.py."""

from anamul_ai.chunk import MAX_WORDS, pack, split_front_matter, split_sections


def test_front_matter_is_separated_from_the_body():
    text = "---\ntitle: My title\ntype: article\nurl: https://example.com\n---\n\n# My title\n\nHello"
    meta, body = split_front_matter(text)
    assert meta == {"title": "My title", "type": "article", "url": "https://example.com"}
    assert body.strip() == "# My title\n\nHello"


def test_sections_keep_the_headings_above_them():
    body = "# Page\n\nIntro\n\n## Work\n\n### OATI\n\nBuilt pipelines\n\n## Skills\n\nPython"
    assert split_sections(body) == [
        ("", "Intro"),  # Text under the page title has no heading path
        ("Work > OATI", "Built pipelines"),  # "## Work" has no text of its own, so it's skipped
        ("Skills", "Python"),  # A new ## heading replaces "Work > OATI"
    ]


def test_pack_never_goes_over_the_word_limit():
    paragraphs = ["word " * 100] * 5  # Five paragraphs of 100 words each
    pieces = pack(paragraphs)
    assert all(len(piece.split()) <= MAX_WORDS for piece in pieces)
    assert len(pieces) == 3  # 200 + 200 + 100 words
