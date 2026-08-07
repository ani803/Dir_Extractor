from bs4 import BeautifulSoup

from models import Page
from models import PersonCard


class DOMParser:

    CONTAINERS = [

        "article",

        "section",

        "div",

        "li",

        "tr"
    ]

    def parse(self, page: Page):

        soup = BeautifulSoup(
            page.html,
            "html.parser"
        )

        cards = []

        for tag in self.CONTAINERS:

            for node in soup.find_all(tag):

                text = node.get_text(
                    " ",
                    strip=True
                )

                if len(text) < 25:
                    continue

                cards.append(

                    PersonCard(

                        text=text,

                        html=str(node),

                        source_url=page.url
                    )

                )

        return cards