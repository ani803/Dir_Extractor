from extractor.extractor import DirectorExtractor
from models import Page


def test_extractor_returns_unique_directors():

    page = Page(
        url="https://example.com/board",
        html="""
        <html>
            <body>
                <section>
                    <h2>Board of Directors</h2>
                    <p>Jane Sharma is the Managing Director.</p>
                    <p>Jane Sharma is the Managing Director.</p>
                </section>
            </body>
        </html>
        """,
        title="Board",
    )

    directors = DirectorExtractor().extract([page])

    assert len(directors) == 1
    assert directors[0].name == "Jane Sharma"
    assert directors[0].designation == "Managing Director"
    assert directors[0].source == "https://example.com/board"
