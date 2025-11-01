# Lead Finder - Web Scraper Agent

A Python agent that scrapes URLs of websites for a specific keyword and extracts emails and phone numbers using [Firecrawl](https://firecrawl.dev).

## Features

- 🔍 Search for up to 200 websites based on any keyword
- 📧 Extract email addresses from websites
- 📞 Extract phone numbers in multiple formats
- 🌐 Support for Google Custom Search or DuckDuckGo (no API key needed)
- 💾 Export results to JSON and CSV formats
- 🚀 Rate-limited scraping to respect server resources
- 📊 Progress tracking and detailed summaries

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Leadfinder
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Required
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Optional (for Google Search, otherwise DuckDuckGo will be used)
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

### Getting API Keys

**Firecrawl API Key (Required):**
- Visit [https://firecrawl.dev](https://firecrawl.dev)
- Sign up for an account
- Get your API key from the dashboard

**Google Custom Search (Optional):**
- API Key: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Search Engine ID: [Programmable Search Engine](https://programmablesearchengine.google.com/)

If you don't provide Google API credentials, the agent will automatically use DuckDuckGo search (no API key required).

## Usage

### Basic Usage

Search for 200 websites about a keyword:
```bash
python main.py "software development companies"
```

### Advanced Usage

**Specify number of websites:**
```bash
python main.py "dentists in New York" --num 50
```

**Use DuckDuckGo search (no API key needed):**
```bash
python main.py "real estate agents" --use-duckduckgo
```

**Custom output files:**
```bash
python main.py "law firms" --output results.json --output-csv results.csv
```

**JSON output only:**
```bash
python main.py "restaurants" --no-csv
```

**CSV output only:**
```bash
python main.py "plumbers" --no-json
```

### Command Line Options

```
positional arguments:
  keyword               Search keyword to find relevant websites

optional arguments:
  -h, --help            Show help message
  -n NUM, --num NUM     Number of websites to scrape (default: 200)
  --use-duckduckgo      Use DuckDuckGo search instead of Google
  -o OUTPUT, --output OUTPUT
                        Output JSON file path
  --output-csv OUTPUT_CSV
                        Output CSV file path
  --no-csv              Do not create CSV output file
  --no-json             Do not create JSON output file
```

## Output Format

### JSON Output

```json
[
  {
    "url": "https://example.com",
    "emails": ["contact@example.com", "info@example.com"],
    "phone_numbers": ["555-123-4567", "555-987-6543"],
    "success": true,
    "error": null
  }
]
```

### CSV Output

| URL | Emails | Phone Numbers | Success | Error |
|-----|--------|---------------|---------|-------|
| https://example.com | contact@example.com; info@example.com | 555-123-4567; 555-987-6543 | True | |

## Using as a Library

You can also import and use the scraper in your own Python code:

```python
from scraper import WebScraperAgent
import os

# Initialize the agent
agent = WebScraperAgent(
    firecrawl_api_key=os.getenv('FIRECRAWL_API_KEY'),
    search_api_key=os.getenv('GOOGLE_SEARCH_API_KEY'),
    search_engine_id=os.getenv('GOOGLE_SEARCH_ENGINE_ID')
)

# Scrape websites
results = agent.scrape_keyword("software companies", num_websites=50)

# Save results
agent.save_results(results, "output.json")
agent.save_results_csv(results, "output.csv")
```

## How It Works

1. **URL Collection**: Searches for websites using Google Custom Search API or DuckDuckGo
2. **Web Scraping**: Uses Firecrawl to scrape each website's content
3. **Data Extraction**: Extracts emails and phone numbers using regex patterns
4. **Results Export**: Saves findings to JSON and CSV files

## Rate Limiting

The agent includes built-in rate limiting:
- 1 second delay between search API requests
- 0.5 second delay between website scrapes

This ensures respectful scraping and prevents overwhelming target servers.

## Limitations

- Google Custom Search API: Limited to 100 free queries per day
- Firecrawl API: Subject to your plan's rate limits and quotas
- DuckDuckGo: May have rate limiting for excessive requests

## Troubleshooting

**"FIRECRAWL_API_KEY not found" error:**
- Make sure you've created a `.env` file with your API key
- Or export the environment variable: `export FIRECRAWL_API_KEY=your_key`

**No results found:**
- Try a different keyword
- Check your internet connection
- Verify your API keys are valid

**Rate limit errors:**
- Reduce the number of websites with `--num`
- Wait before running the script again
- Check your API quota limits

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
