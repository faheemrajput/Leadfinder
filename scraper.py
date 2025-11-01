"""
Web Scraper Agent
Scrapes URLs for a given keyword and extracts emails and phone numbers using Firecrawl.
"""

import os
import re
import json
import time
from typing import List, Dict, Set
from dataclasses import dataclass, asdict
import requests
from firecrawl import FirecrawlApp


@dataclass
class ScrapedData:
    """Data structure for scraped information."""
    url: str
    emails: List[str]
    phone_numbers: List[str]
    success: bool
    error: str = None


class WebScraperAgent:
    """Agent for scraping websites and extracting contact information."""

    def __init__(self, firecrawl_api_key: str, search_api_key: str = None, search_engine_id: str = None):
        """
        Initialize the web scraper agent.

        Args:
            firecrawl_api_key: API key for Firecrawl
            search_api_key: Google Custom Search API key (optional)
            search_engine_id: Google Custom Search Engine ID (optional)
        """
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
        self.search_api_key = search_api_key
        self.search_engine_id = search_engine_id

    def search_urls(self, keyword: str, num_results: int = 200) -> List[str]:
        """
        Search for URLs based on keyword using Google Custom Search API.

        Args:
            keyword: Search keyword
            num_results: Number of results to retrieve (max 200)

        Returns:
            List of URLs
        """
        if not self.search_api_key or not self.search_engine_id:
            raise ValueError("Search API key and Search Engine ID are required for URL search")

        urls = []
        queries_needed = min((num_results + 9) // 10, 20)  # Max 10 results per query, max 20 queries

        print(f"🔍 Searching for '{keyword}'...")

        for i in range(queries_needed):
            start_index = i * 10 + 1

            try:
                search_url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.search_api_key,
                    'cx': self.search_engine_id,
                    'q': keyword,
                    'start': start_index,
                    'num': 10
                }

                response = requests.get(search_url, params=params, timeout=10)
                response.raise_for_status()

                results = response.json()

                if 'items' in results:
                    for item in results['items']:
                        urls.append(item['link'])
                        if len(urls) >= num_results:
                            break

                if len(urls) >= num_results:
                    break

                # Respect rate limits
                time.sleep(1)

            except Exception as e:
                print(f"⚠️  Error fetching search results (page {i+1}): {str(e)}")
                continue

        print(f"✅ Found {len(urls)} URLs")
        return urls[:num_results]

    def search_urls_duckduckgo(self, keyword: str, num_results: int = 200) -> List[str]:
        """
        Alternative search method using DuckDuckGo (no API key needed).
        Note: This is a fallback method and may have limitations.

        Args:
            keyword: Search keyword
            num_results: Number of results to retrieve

        Returns:
            List of URLs
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            raise ImportError("Please install duckduckgo-search: pip install duckduckgo-search")

        urls = []
        print(f"🔍 Searching DuckDuckGo for '{keyword}'...")

        try:
            with DDGS() as ddgs:
                results = ddgs.text(keyword, max_results=num_results)
                for result in results:
                    if 'href' in result:
                        urls.append(result['href'])
                    elif 'link' in result:
                        urls.append(result['link'])
        except Exception as e:
            print(f"⚠️  Error with DuckDuckGo search: {str(e)}")

        print(f"✅ Found {len(urls)} URLs")
        return urls[:num_results]

    def extract_emails_and_phones(self, url: str) -> ScrapedData:
        """
        Extract emails and phone numbers from a URL using Firecrawl.

        Args:
            url: URL to scrape

        Returns:
            ScrapedData object with extracted information
        """
        try:
            # Use Firecrawl to scrape the page
            result = self.firecrawl.scrape_url(url, params={
                'formats': ['markdown', 'html'],
                'onlyMainContent': True
            })

            if not result or 'markdown' not in result:
                return ScrapedData(url=url, emails=[], phone_numbers=[], success=False, error="No content retrieved")

            content = result.get('markdown', '') + ' ' + result.get('html', '')

            # Extract emails using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = list(set(re.findall(email_pattern, content)))

            # Extract phone numbers using regex (multiple formats)
            phone_patterns = [
                r'\+?1?\s*\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US format
                r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}',  # International
                r'\([0-9]{3}\)\s*[0-9]{3}[-.\s]?[0-9]{4}',  # (555) 123-4567
            ]

            phone_numbers = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        phone_numbers.add(''.join(match))
                    else:
                        phone_numbers.add(match)

            # Filter out invalid phone numbers (too short or too long)
            phone_numbers = [p for p in phone_numbers if 10 <= len(re.sub(r'\D', '', p)) <= 15]

            return ScrapedData(
                url=url,
                emails=emails,
                phone_numbers=phone_numbers,
                success=True
            )

        except Exception as e:
            return ScrapedData(
                url=url,
                emails=[],
                phone_numbers=[],
                success=False,
                error=str(e)
            )

    def scrape_keyword(self, keyword: str, num_websites: int = 200, use_duckduckgo: bool = False) -> List[ScrapedData]:
        """
        Main method to scrape websites for a keyword and extract contact info.

        Args:
            keyword: Keyword to search for
            num_websites: Number of websites to scrape (default 200)
            use_duckduckgo: Use DuckDuckGo instead of Google (default False)

        Returns:
            List of ScrapedData objects
        """
        # Step 1: Get URLs
        if use_duckduckgo:
            urls = self.search_urls_duckduckgo(keyword, num_websites)
        else:
            urls = self.search_urls(keyword, num_websites)

        if not urls:
            print("❌ No URLs found")
            return []

        # Step 2: Scrape each URL
        results = []
        total = len(urls)

        print(f"\n🚀 Starting to scrape {total} websites...")

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{total}] Scraping: {url}")

            scraped_data = self.extract_emails_and_phones(url)
            results.append(scraped_data)

            if scraped_data.success:
                print(f"  ✅ Found {len(scraped_data.emails)} emails, {len(scraped_data.phone_numbers)} phones")
            else:
                print(f"  ❌ Error: {scraped_data.error}")

            # Rate limiting to avoid overwhelming servers
            time.sleep(0.5)

        # Summary
        successful = sum(1 for r in results if r.success)
        total_emails = sum(len(r.emails) for r in results)
        total_phones = sum(len(r.phone_numbers) for r in results)

        print(f"\n📊 Summary:")
        print(f"  • Websites scraped: {successful}/{total}")
        print(f"  • Total emails found: {total_emails}")
        print(f"  • Total phone numbers found: {total_phones}")

        return results

    def save_results(self, results: List[ScrapedData], output_file: str = "scraped_data.json"):
        """
        Save scraped results to a JSON file.

        Args:
            results: List of ScrapedData objects
            output_file: Output file path
        """
        data = [asdict(r) for r in results]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to {output_file}")

    def save_results_csv(self, results: List[ScrapedData], output_file: str = "scraped_data.csv"):
        """
        Save scraped results to a CSV file.

        Args:
            results: List of ScrapedData objects
            output_file: Output file path
        """
        import csv

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Emails', 'Phone Numbers', 'Success', 'Error'])

            for result in results:
                writer.writerow([
                    result.url,
                    '; '.join(result.emails),
                    '; '.join(result.phone_numbers),
                    result.success,
                    result.error or ''
                ])

        print(f"💾 Results saved to {output_file}")


if __name__ == "__main__":
    # Example usage
    import sys

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
    google_search_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

    if not firecrawl_key:
        print("❌ Error: FIRECRAWL_API_KEY not found in environment variables")
        sys.exit(1)

    # Get keyword from command line or use default
    keyword = sys.argv[1] if len(sys.argv) > 1 else "software development companies"
    num_websites = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    # Create agent
    agent = WebScraperAgent(
        firecrawl_api_key=firecrawl_key,
        search_api_key=google_search_key,
        search_engine_id=google_search_engine_id
    )

    # Use DuckDuckGo if Google API credentials are not available
    use_ddg = not (google_search_key and google_search_engine_id)

    # Scrape websites
    results = agent.scrape_keyword(keyword, num_websites, use_duckduckgo=use_ddg)

    # Save results
    agent.save_results(results, f"results_{keyword.replace(' ', '_')}.json")
    agent.save_results_csv(results, f"results_{keyword.replace(' ', '_')}.csv")
