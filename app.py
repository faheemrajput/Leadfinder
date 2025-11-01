#!/usr/bin/env python3
"""
Lead Finder - Streamlit Web Application
Web-based interface for scraping websites and extracting contact information.
"""

import streamlit as st
import json
import io
import pandas as pd
from datetime import datetime
from scraper import WebScraperAgent, ScrapedData
import time


# Page configuration
st.set_page_config(
    page_title="Lead Finder - Web Scraper",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'scraping_complete' not in st.session_state:
        st.session_state.scraping_complete = False
    if 'last_keyword' not in st.session_state:
        st.session_state.last_keyword = ""


def create_csv_download(results):
    """Create CSV data for download."""
    data = []
    for result in results:
        data.append({
            'URL': result.url,
            'Emails': '; '.join(result.emails),
            'Phone Numbers': '; '.join(result.phone_numbers),
            'Success': result.success,
            'Error': result.error or ''
        })

    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')


def create_json_download(results):
    """Create JSON data for download."""
    from dataclasses import asdict
    data = [asdict(r) for r in results]
    return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')


def display_results(results):
    """Display scraped results in a nice format."""
    if not results:
        st.warning("No results to display")
        return

    # Summary metrics
    successful = sum(1 for r in results if r.success)
    total_emails = sum(len(r.emails) for r in results)
    total_phones = sum(len(r.phone_numbers) for r in results)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Websites", len(results))
    with col2:
        st.metric("Successful Scrapes", successful)
    with col3:
        st.metric("Emails Found", total_emails)
    with col4:
        st.metric("Phone Numbers Found", total_phones)

    st.divider()

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_successful_only = st.checkbox("Show only successful scrapes", value=False)
    with col2:
        show_with_contacts_only = st.checkbox("Show only results with emails or phones", value=False)

    # Filter results
    filtered_results = results
    if show_successful_only:
        filtered_results = [r for r in filtered_results if r.success]
    if show_with_contacts_only:
        filtered_results = [r for r in filtered_results if r.emails or r.phone_numbers]

    st.write(f"Showing {len(filtered_results)} of {len(results)} results")

    # Display results
    for i, result in enumerate(filtered_results, 1):
        with st.expander(f"{'✅' if result.success else '❌'} {result.url}", expanded=False):
            if result.success:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📧 Emails")
                    if result.emails:
                        for email in result.emails:
                            st.code(email, language=None)
                    else:
                        st.info("No emails found")

                with col2:
                    st.subheader("📞 Phone Numbers")
                    if result.phone_numbers:
                        for phone in result.phone_numbers:
                            st.code(phone, language=None)
                    else:
                        st.info("No phone numbers found")
            else:
                st.error(f"Error: {result.error}")


def main():
    """Main Streamlit application."""
    init_session_state()

    # Header
    st.title("🎯 Lead Finder - Web Scraper Agent")
    st.markdown("Extract emails and phone numbers from websites based on keywords")

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Keys Section
        st.subheader("🔑 API Keys")

        with st.expander("Firecrawl API (Required)", expanded=True):
            firecrawl_key = st.text_input(
                "Firecrawl API Key",
                type="password",
                help="Get your API key from https://firecrawl.dev",
                key="firecrawl_key"
            )
            st.markdown("[Get Firecrawl API Key →](https://firecrawl.dev)")

        with st.expander("Google Search API (Optional)", expanded=False):
            st.info("If not provided, DuckDuckGo will be used (no API key needed)")
            google_api_key = st.text_input(
                "Google API Key",
                type="password",
                help="Optional: Google Custom Search API key",
                key="google_key"
            )
            google_engine_id = st.text_input(
                "Search Engine ID",
                type="password",
                help="Optional: Google Custom Search Engine ID",
                key="google_engine"
            )
            st.markdown("[Get Google API Key →](https://console.cloud.google.com/apis/credentials)")
            st.markdown("[Create Search Engine →](https://programmablesearchengine.google.com/)")

        st.divider()

        # Search Options
        st.subheader("🔍 Search Options")

        use_duckduckgo = st.checkbox(
            "Force DuckDuckGo Search",
            value=False,
            help="Use DuckDuckGo even if Google API keys are provided"
        )

        num_websites = st.slider(
            "Number of Websites",
            min_value=1,
            max_value=200,
            value=50,
            step=1,
            help="Number of websites to scrape (1-200)"
        )

        st.divider()

        # Export Options
        st.subheader("💾 Export Options")

        export_json = st.checkbox("Enable JSON Export", value=True)
        export_csv = st.checkbox("Enable CSV Export", value=True)

        st.divider()

        # About
        st.subheader("ℹ️ About")
        st.markdown("""
        **Lead Finder** helps you find contact information from websites.

        Features:
        - Search up to 200 websites
        - Extract emails & phone numbers
        - Export to JSON/CSV
        - Real-time progress tracking
        """)

    # Main content area
    tab1, tab2, tab3 = st.tabs(["🚀 Scraper", "📊 Results", "📖 Guide"])

    with tab1:
        st.header("Start Scraping")

        # Keyword input
        keyword = st.text_input(
            "Enter Search Keyword",
            placeholder="e.g., software development companies, dentists in New York",
            help="The keyword to search for relevant websites",
            key="keyword_input"
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            start_button = st.button("🚀 Start Scraping", type="primary", use_container_width=True)
        with col2:
            if st.session_state.results:
                st.button("🔄 Clear Results", on_click=lambda: setattr(st.session_state, 'results', None), use_container_width=True)

        # Validation and scraping
        if start_button:
            # Validate inputs
            if not keyword:
                st.error("❌ Please enter a search keyword")
            elif not firecrawl_key:
                st.error("❌ Firecrawl API key is required")
            else:
                # Determine search method
                use_ddg = use_duckduckgo or not (google_api_key and google_engine_id)
                search_method = "DuckDuckGo" if use_ddg else "Google Custom Search"

                st.info(f"🔍 Using {search_method} to find websites")

                try:
                    # Create agent
                    agent = WebScraperAgent(
                        firecrawl_api_key=firecrawl_key,
                        search_api_key=google_api_key if not use_ddg else None,
                        search_engine_id=google_engine_id if not use_ddg else None
                    )

                    # Progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Get URLs
                    status_text.text(f"🔍 Searching for {num_websites} websites...")
                    if use_ddg:
                        urls = agent.search_urls_duckduckgo(keyword, num_websites)
                    else:
                        urls = agent.search_urls(keyword, num_websites)

                    if not urls:
                        st.error("❌ No URLs found for the given keyword")
                    else:
                        st.success(f"✅ Found {len(urls)} URLs")

                        # Scrape each URL
                        results = []
                        total = len(urls)

                        status_text.text(f"🕷️ Scraping {total} websites...")

                        # Create a container for live results
                        results_container = st.container()

                        for i, url in enumerate(urls):
                            # Update progress
                            progress = (i + 1) / total
                            progress_bar.progress(progress)
                            status_text.text(f"Scraping {i+1}/{total}: {url[:50]}...")

                            # Scrape
                            scraped_data = agent.extract_emails_and_phones(url)
                            results.append(scraped_data)

                            # Show live update
                            if scraped_data.success and (scraped_data.emails or scraped_data.phone_numbers):
                                with results_container:
                                    st.success(f"✅ [{i+1}/{total}] {url[:50]}... - {len(scraped_data.emails)} emails, {len(scraped_data.phone_numbers)} phones")

                            # Rate limiting
                            time.sleep(0.5)

                        # Save results
                        st.session_state.results = results
                        st.session_state.last_keyword = keyword
                        st.session_state.scraping_complete = True

                        # Clear progress
                        progress_bar.empty()
                        status_text.empty()

                        # Show summary
                        successful = sum(1 for r in results if r.success)
                        total_emails = sum(len(r.emails) for r in results)
                        total_phones = sum(len(r.phone_numbers) for r in results)

                        st.success(f"""
                        ✨ **Scraping Complete!**
                        - Websites scraped: {successful}/{total}
                        - Emails found: {total_emails}
                        - Phone numbers found: {total_phones}
                        """)

                        st.info("👉 Switch to the 'Results' tab to view and download the data")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Show error details"):
                        st.code(traceback.format_exc())

        # Show current status
        if st.session_state.scraping_complete and st.session_state.results:
            st.divider()
            st.info(f"💡 Last scrape: '{st.session_state.last_keyword}' - {len(st.session_state.results)} results available")

    with tab2:
        st.header("Scraped Results")

        if st.session_state.results:
            # Download buttons
            st.subheader("📥 Download Results")

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if export_json:
                    json_data = create_json_download(st.session_state.results)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="📄 Download JSON",
                        data=json_data,
                        file_name=f"leadfinder_{st.session_state.last_keyword.replace(' ', '_')}_{timestamp}.json",
                        mime="application/json",
                        use_container_width=True
                    )

            with col2:
                if export_csv:
                    csv_data = create_csv_download(st.session_state.results)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv_data,
                        file_name=f"leadfinder_{st.session_state.last_keyword.replace(' ', '_')}_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            st.divider()

            # Display results
            display_results(st.session_state.results)
        else:
            st.info("👈 No results yet. Start scraping from the 'Scraper' tab!")

    with tab3:
        st.header("📖 User Guide")

        st.markdown("""
        ## Getting Started

        ### 1. Setup API Keys

        **Firecrawl API (Required):**
        - Visit [firecrawl.dev](https://firecrawl.dev)
        - Sign up and get your API key
        - Enter it in the sidebar

        **Google Search API (Optional):**
        - If not provided, DuckDuckGo will be used automatically
        - [Get Google API Key](https://console.cloud.google.com/apis/credentials)
        - [Create Search Engine](https://programmablesearchengine.google.com/)

        ### 2. Configure Search Options

        - **Number of Websites**: Choose how many websites to scrape (1-200)
        - **Search Method**: Use Google or DuckDuckGo
        - **Export Options**: Enable JSON and/or CSV downloads

        ### 3. Start Scraping

        1. Enter your search keyword (e.g., "software companies", "dentists in NYC")
        2. Click "Start Scraping"
        3. Wait for the scraping to complete
        4. View results in the "Results" tab

        ### 4. Download Results

        - Switch to the "Results" tab
        - Click "Download JSON" or "Download CSV"
        - Results include URLs, emails, phone numbers, and status

        ## Features

        - ✅ Search up to 200 websites
        - ✅ Extract emails and phone numbers
        - ✅ Real-time progress tracking
        - ✅ Filter and view results
        - ✅ Export to JSON/CSV
        - ✅ No coding required!

        ## Tips

        - Use specific keywords for better results (e.g., "dentists in New York" vs "dentists")
        - Start with fewer websites to test (10-20)
        - Check your API rate limits
        - Results are stored in session - refresh page to clear

        ## Limitations

        - Firecrawl API has rate limits based on your plan
        - Google Search API: 100 free queries/day
        - DuckDuckGo may rate limit excessive requests
        - Large scrapes (200 websites) may take 5-10 minutes

        ## Troubleshooting

        **No results found:**
        - Try a different keyword
        - Check your internet connection
        - Verify API keys are correct

        **Rate limit errors:**
        - Reduce number of websites
        - Wait before scraping again
        - Check your API quotas

        **Scraping is slow:**
        - This is normal - rate limiting protects servers
        - Average: 2-3 websites per minute
        - 200 websites ≈ 5-10 minutes
        """)


if __name__ == "__main__":
    main()
