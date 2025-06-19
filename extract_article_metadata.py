#!/usr/bin/env python3
"""
Extract metadata from The New Atlantis articles and generate Markdown headers for note-taking.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def fetch_article_content(url):
    """Fetch the HTML content of the article."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching article: {e}", file=sys.stderr)
        sys.exit(1)


def infer_edition_number(season, year):
    """
    Infer The New Atlantis edition number from season and year.
    
    Based on the quarterly publication schedule:
    - Winter 2025 = No. 79
    - Summer 2025 = No. 81
    """
    if not season or not year:
        return None
    
    try:
        year = int(year)
    except (ValueError, TypeError):
        return None
    
    season_lower = season.lower()
    
    # Base calculation: Winter 2025 = 79
    # Each year has 4 issues, so year difference * 4
    base_year = 2025
    base_winter_number = 79
    
    # Calculate base number for the given year's winter issue
    year_diff = year - base_year
    year_base_number = base_winter_number + (year_diff * 4)
    
    # Season offsets within a year (Winter = 0, Spring = 1, Summer = 2, Fall = 3)
    season_offset = {
        'winter': 0, 'spring': 1, 'summer': 2, 'fall': 3, 'autumn': 3
    }
    
    offset = season_offset.get(season_lower)
    if offset is None:
        return None
    
    return year_base_number + offset


def extract_metadata(html_content):
    """Extract metadata from The New Atlantis article HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    metadata = {}

    # Try to extract from JSON-LD structured data first
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get("@type") == "Article":
                metadata["title"] = data.get("headline", "").strip()

                # Handle author(s)
                authors = data.get("author", [])
                if isinstance(authors, dict):
                    authors = [authors]
                if authors:
                    metadata["authors"] = [
                        re.sub(r"\s+", " ", author.get("name", "").strip())
                        for author in authors
                        if author.get("name")
                    ]

                # Extract publication date
                date_published = data.get("datePublished", "")
                if date_published:
                    metadata["date_published"] = date_published

                break
        except (json.JSONDecodeError, KeyError):
            continue

    # Fallback to HTML parsing if JSON-LD doesn't work
    if not metadata.get("title"):
        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()

    # Extract author from byline if not found in JSON-LD
    if not metadata.get("authors"):
        byline = soup.find(class_=re.compile(r"author|byline", re.I))
        if byline:
            author_text = byline.get_text().strip()
            # Clean up common prefixes
            author_text = re.sub(r"^(by|author:?)\s*", "", author_text, flags=re.I)
            # Normalize whitespace
            author_text = re.sub(r"\s+", " ", author_text)
            metadata["authors"] = [author_text]

    # Extract issue information
    issue_info = soup.find(string=re.compile(r"No\.\s*\d+"))
    if issue_info:
        issue_match = re.search(r"No\.\s*(\d+)\s*\(([^)]+)\)", issue_info)
        if issue_match:
            metadata["issue_number"] = issue_match.group(1)
            metadata["issue_season"] = issue_match.group(2)
    
    # If no explicit issue number found, look for season-only patterns
    if not metadata.get("issue_number"):
        # Look for patterns like "Winter 2025", "Spring 2024", etc.
        season_patterns = [
            r"(Winter|Spring|Summer|Fall|Autumn)\s+(\d{4})",
            r"(\d{4})\s+(Winter|Spring|Summer|Fall|Autumn)"
        ]
        
        for pattern in season_patterns:
            season_match = soup.find(string=re.compile(pattern, re.IGNORECASE))
            if season_match:
                match = re.search(pattern, season_match, re.IGNORECASE)
                if match:
                    if match.group(1).isdigit():
                        # Pattern: "2025 Winter"
                        year, season = match.group(1), match.group(2)
                    else:
                        # Pattern: "Winter 2025"
                        season, year = match.group(1), match.group(2)
                    
                    # Infer the issue number
                    inferred_number = infer_edition_number(season, int(year))
                    if inferred_number:
                        metadata["issue_number"] = str(inferred_number)
                        metadata["issue_season"] = f"{season} {year}"
                    break

    # Set publication name
    metadata["publication"] = "The New Atlantis"

    return metadata


def format_markdown_header(metadata, creation_date=None):
    """Format the extracted metadata into the required Markdown header."""
    if creation_date is None:
        creation_date = datetime.now().strftime("%Y-%m-%d")

    title = metadata.get("title", "Unknown Title")
    authors = metadata.get("authors", ["Unknown Author"])
    publication = metadata.get("publication", "The New Atlantis")

    # Format periodical edition
    periodical_edition = ""
    if metadata.get("issue_number") and metadata.get("issue_season"):
        periodical_edition = (
            f"No. {metadata['issue_number']} ({metadata['issue_season']})"
        )

    # Build the YAML front matter
    yaml_lines = ["---", f"title: {title}", "author:"]

    for author in authors:
        yaml_lines.append(f"  - {author}")

    yaml_lines.extend(
        [
            "format: journal article",
            f"creation-date: {creation_date}",
            f"publication: {publication}",
        ]
    )

    if periodical_edition:
        yaml_lines.append(f"periodical-edition: {periodical_edition}")

    yaml_lines.extend(["---", "", "## Notes"])

    return "\n".join(yaml_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata from The New Atlantis articles for note-taking"
    )
    parser.add_argument("url", help="URL of The New Atlantis article")
    parser.add_argument(
        "--creation-date",
        help="Override creation date (YYYY-MM-DD format)",
        default=None,
    )

    args = parser.parse_args()

    # Validate URL
    parsed_url = urlparse(args.url)
    if not parsed_url.netloc or "thenewatlantis.com" not in parsed_url.netloc:
        print(
            "Warning: URL doesn't appear to be from The New Atlantis", file=sys.stderr
        )

    # Fetch and process article
    html_content = fetch_article_content(args.url)
    metadata = extract_metadata(html_content)

    # Generate and print Markdown header
    markdown_header = format_markdown_header(metadata, args.creation_date)
    print(markdown_header)


if __name__ == "__main__":
    main()
