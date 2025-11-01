#!/usr/bin/env python3
"""
Lead Finder - Web Scraper Agent
Main CLI script for scraping websites and extracting contact information.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from scraper import WebScraperAgent


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Lead Finder - Scrape websites for emails and phone numbers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for 200 websites about "software development companies"
  python main.py "software development companies"

  # Search for 50 websites about "dentists in New York"
  python main.py "dentists in New York" --num 50

  # Use DuckDuckGo instead of Google (no API key needed)
  python main.py "real estate agents" --use-duckduckgo

  # Specify custom output files
  python main.py "law firms" --output results.json --output-csv results.csv
        """
    )

    parser.add_argument(
        'keyword',
        type=str,
        help='Search keyword to find relevant websites'
    )

    parser.add_argument(
        '-n', '--num',
        type=int,
        default=200,
        help='Number of websites to scrape (default: 200)'
    )

    parser.add_argument(
        '--use-duckduckgo',
        action='store_true',
        help='Use DuckDuckGo search instead of Google (no API key required)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output JSON file path (default: results_<keyword>.json)'
    )

    parser.add_argument(
        '--output-csv',
        type=str,
        default=None,
        help='Output CSV file path (default: results_<keyword>.csv)'
    )

    parser.add_argument(
        '--no-csv',
        action='store_true',
        help='Do not create CSV output file'
    )

    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Do not create JSON output file'
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Get API keys from environment
    firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
    google_search_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

    # Validate Firecrawl API key
    if not firecrawl_key:
        print("❌ Error: FIRECRAWL_API_KEY not found in environment variables")
        print("\nPlease create a .env file with your API key:")
        print("  FIRECRAWL_API_KEY=your_api_key_here")
        print("\nOr export it as an environment variable:")
        print("  export FIRECRAWL_API_KEY=your_api_key_here")
        sys.exit(1)

    # Check if using DuckDuckGo or Google
    use_ddg = args.use_duckduckgo or not (google_search_key and google_search_engine_id)

    if use_ddg:
        print("🦆 Using DuckDuckGo for search")
    else:
        print("🔍 Using Google Custom Search")

    # Create agent
    try:
        agent = WebScraperAgent(
            firecrawl_api_key=firecrawl_key,
            search_api_key=google_search_key,
            search_engine_id=google_search_engine_id
        )
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        sys.exit(1)

    # Run the scraper
    print(f"\n🚀 Starting Lead Finder Agent")
    print(f"📋 Keyword: {args.keyword}")
    print(f"🎯 Target websites: {args.num}\n")

    try:
        results = agent.scrape_keyword(args.keyword, args.num, use_duckduckgo=use_ddg)

        if not results:
            print("\n⚠️  No results found")
            sys.exit(0)

        # Determine output file names
        keyword_slug = args.keyword.replace(' ', '_').replace('/', '_')
        json_output = args.output or f"results_{keyword_slug}.json"
        csv_output = args.output_csv or f"results_{keyword_slug}.csv"

        # Save results
        if not args.no_json:
            agent.save_results(results, json_output)

        if not args.no_csv:
            agent.save_results_csv(results, csv_output)

        print("\n✨ Done! Happy lead hunting! 🎯")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
