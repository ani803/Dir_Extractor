from crawler.crawler import Crawler


def main():

    crawler = Crawler()

    pages = crawler.crawl(
        "https://www.infosys.com"
    )

    print()

    print("=" * 60)

    print(f"Downloaded {len(pages)} pages")

    print("=" * 60)

    for page in pages:

        print(page.title)

        print(page.url)

        print("-" * 60)


if __name__ == "__main__":
    main()