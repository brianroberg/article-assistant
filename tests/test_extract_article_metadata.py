#!/usr/bin/env python3
"""
Unit tests for extract_article_metadata.py
"""

import pytest
from unittest.mock import patch, Mock

from extract_article_metadata import (
    extract_metadata,
    format_markdown_header,
    fetch_article_content,
)


class TestExtractMetadata:
    """Test cases for the extract_metadata function."""

    def test_extract_metadata_from_json_ld(self):
        """Test extracting metadata from JSON-LD structured data."""
        html_content = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Article",
                "headline": "The Tyranny of Now",
                "author": [{"name": "Nicholas  Carr"}],
                "datePublished": "2025-01-15"
            }
            </script>
        </head>
        <body></body>
        </html>
        """

        metadata = extract_metadata(html_content)

        assert metadata["title"] == "The Tyranny of Now"
        assert metadata["authors"] == ["Nicholas Carr"]  # Whitespace normalized
        assert metadata["date_published"] == "2025-01-15"
        assert metadata["publication"] == "The New Atlantis"

    def test_extract_metadata_single_author_dict(self):
        """Test extracting metadata when author is a single dict, not list."""
        html_content = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Article",
                "headline": "Test Article",
                "author": {"name": "John Doe"},
                "datePublished": "2025-01-15"
            }
            </script>
        </head>
        <body></body>
        </html>
        """

        metadata = extract_metadata(html_content)

        assert metadata["title"] == "Test Article"
        assert metadata["authors"] == ["John Doe"]

    def test_extract_metadata_fallback_to_html(self):
        """Test fallback to HTML parsing when JSON-LD is not available."""
        html_content = """
        <html>
        <head><title>HTML Title</title></head>
        <body>
            <h1>Article Title from H1</h1>
            <div class="author-byline">By Jane Smith</div>
        </body>
        </html>
        """

        metadata = extract_metadata(html_content)

        assert metadata["title"] == "Article Title from H1"
        assert metadata["authors"] == ["Jane Smith"]
        assert metadata["publication"] == "The New Atlantis"

    def test_extract_metadata_title_fallback_to_title_tag(self):
        """Test title extraction falls back to title tag when no h1."""
        html_content = """
        <html>
        <head><title>Title from Tag</title></head>
        <body>
            <div class="author">By Author Name</div>
        </body>
        </html>
        """

        metadata = extract_metadata(html_content)

        assert metadata["title"] == "Title from Tag"

    def test_extract_metadata_author_prefix_cleanup(self):
        """Test that author prefixes are cleaned up properly."""
        html_content = """
        <html>
        <body>
            <h1>Test Article</h1>
            <div class="byline">Author: John Doe</div>
        </body>
        </html>
        """

        metadata = extract_metadata(html_content)

        assert metadata["authors"] == ["John Doe"]

    def test_extract_metadata_issue_information(self):
        """Test extraction of issue number and season information."""
        html_content = """
        <html>
        <body>
            <h1>Test Article</h1>
            <p>From No. 79 (Winter 2025) issue</p>
        </body>
        </html>
        """

        metadata = extract_metadata(html_content)

        assert metadata["issue_number"] == "79"
        assert metadata["issue_season"] == "Winter 2025"

    def test_extract_metadata_whitespace_normalization(self):
        """Test that multiple spaces in author names are normalized."""
        html_content = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Article",
                "headline": "Test",
                "author": [{"name": "John    Multiple   Spaces"}]
            }
            </script>     
        </head>
        </html>
        """

        metadata = extract_metadata(html_content)

        assert metadata["authors"] == ["John Multiple Spaces"]

    def test_extract_metadata_empty_html(self):
        """Test behavior with minimal HTML content."""
        html_content = "<html><body></body></html>"

        metadata = extract_metadata(html_content)

        assert metadata["publication"] == "The New Atlantis"
        assert "title" not in metadata or not metadata["title"]


class TestFormatMarkdownHeader:
    """Test cases for the format_markdown_header function."""

    def test_format_markdown_header_basic(self):
        """Test basic markdown header formatting."""
        metadata = {
            "title": "The Tyranny of Now",
            "authors": ["Nicholas Carr"],
            "publication": "The New Atlantis",
        }

        result = format_markdown_header(metadata, "2025-06-19")

        expected = """---
title: The Tyranny of Now
author:
  - Nicholas Carr
format: journal article
creation-date: 2025-06-19
publication: The New Atlantis
---

## Notes"""

        assert result == expected

    def test_format_markdown_header_with_issue(self):
        """Test markdown header with issue information."""
        metadata = {
            "title": "Test Article",
            "authors": ["Author Name"],
            "publication": "The New Atlantis",
            "issue_number": "79",
            "issue_season": "Winter 2025",
        }

        result = format_markdown_header(metadata, "2025-06-19")

        assert "periodical-edition: No. 79 (Winter 2025)" in result

    def test_format_markdown_header_multiple_authors(self):
        """Test markdown header with multiple authors."""
        metadata = {
            "title": "Multi-Author Paper",
            "authors": ["First Author", "Second Author", "Third Author"],
            "publication": "The New Atlantis",
        }

        result = format_markdown_header(metadata)

        assert "  - First Author" in result
        assert "  - Second Author" in result
        assert "  - Third Author" in result

    def test_format_markdown_header_default_creation_date(self):
        """Test that default creation date is today when not specified."""
        metadata = {
            "title": "Test",
            "authors": ["Author"],
            "publication": "The New Atlantis",
        }

        with patch("extract_article_metadata.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-06-19"
            result = format_markdown_header(metadata)

        assert "creation-date: 2025-06-19" in result

    def test_format_markdown_header_defaults(self):
        """Test markdown header with default values for missing metadata."""
        metadata = {}

        result = format_markdown_header(metadata, "2025-06-19")

        assert "title: Unknown Title" in result
        assert "  - Unknown Author" in result
        assert "publication: The New Atlantis" in result


class TestFetchArticleContent:
    """Test cases for the fetch_article_content function."""

    @patch("extract_article_metadata.requests.get")
    def test_fetch_article_content_success(self, mock_get):
        """Test successful article content fetching."""
        mock_response = Mock()
        mock_response.text = "<html>Article content</html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_article_content("https://example.com/article")

        assert result == "<html>Article content</html>"
        mock_get.assert_called_once()

        # Check that proper headers were set
        call_args = mock_get.call_args
        assert "User-Agent" in call_args[1]["headers"]

    @patch("extract_article_metadata.requests.get")
    def test_fetch_article_content_request_error(self, mock_get):
        """Test handling of request errors."""
        from requests import RequestException

        mock_get.side_effect = RequestException("Network error")

        with pytest.raises(SystemExit) as exc_info:
            fetch_article_content("https://example.com/article")

        assert exc_info.value.code == 1

    @patch("extract_article_metadata.requests.get")
    def test_fetch_article_content_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        from requests import RequestException

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException("HTTP 404")
        mock_get.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            fetch_article_content("https://example.com/article")

        assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__])
