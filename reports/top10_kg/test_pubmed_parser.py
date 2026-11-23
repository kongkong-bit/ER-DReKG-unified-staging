import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT = Path(__file__).with_name("fetch_top10_pubmed_literature.py")
SPEC = importlib.util.spec_from_file_location("pubmed_literature", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
parse_records = MODULE.parse_records


def test_parse_pubmed_book_article_metadata():
    root = ET.fromstring(
        """<PubmedArticleSet>
        <PubmedBookArticle><BookDocument>
          <PMID>31643461</PMID>
          <Book><BookTitle>LiverTox</BookTitle><PubDate>2012</PubDate></Book>
          <ArticleTitle>Ponatinib</ArticleTitle>
          <PublicationType>Review</PublicationType>
          <Abstract><AbstractText>Ponatinib is a kinase inhibitor.</AbstractText></Abstract>
        </BookDocument></PubmedBookArticle>
        </PubmedArticleSet>"""
    )

    records = parse_records(root)

    assert len(records) == 1
    assert records[0]["pmid"] == "31643461"
    assert records[0]["title"] == "Ponatinib"
    assert records[0]["journal"] == "LiverTox"
    assert records[0]["year"] == "2012"
    assert records[0]["publication_types"] == "Book; Review"
    assert records[0]["abstract"] == "Ponatinib is a kinase inhibitor."


def test_parse_pubmed_article_and_book_article_together():
    root = ET.fromstring(
        """<PubmedArticleSet>
        <PubmedArticle><MedlineCitation><PMID>12345678</PMID><Article>
          <ArticleTitle>Study</ArticleTitle><Journal><Title>Journal</Title>
            <JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue>
          </Journal><Abstract><AbstractText>Abstract.</AbstractText></Abstract>
          <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
        </Article></MedlineCitation></PubmedArticle>
        <PubmedBookArticle><BookDocument><PMID>87654321</PMID><Book>
          <BookTitle>Reference</BookTitle></Book><ArticleTitle>Chapter</ArticleTitle>
          <Abstract><AbstractText>Chapter abstract.</AbstractText></Abstract>
        </BookDocument></PubmedBookArticle>
        </PubmedArticleSet>"""
    )

    records = parse_records(root)

    assert [record["pmid"] for record in records] == ["12345678", "87654321"]
