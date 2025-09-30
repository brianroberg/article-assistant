# Multi-Site Article Metadata Extraction Implementation Plan

## Overview

Expand the article-assistant script to support metadata extraction from multiple websites (not just The New Atlantis) using Simon Willison's `llm` utility for generic article extraction, while preserving the existing specialized extraction logic and performance for The New Atlantis.

## Current State Analysis

The current implementation (`extract_article_metadata.py:1-231`) is a monolithic script specifically designed for The New Atlantis:

### Existing Components:
- `fetch_article_content(url)` (`extract_article_metadata.py:17-29`) - HTTP fetching with custom User-Agent
- `infer_edition_number(season, year)` (`extract_article_metadata.py:32-68`) - The New Atlantis-specific edition calculation
- `extract_metadata(html_content)` (`extract_article_metadata.py:71-159`) - Two-phase extraction (JSON-LD + HTML fallback)
- `format_markdown_header(metadata, creation_date)` (`extract_article_metadata.py:162-197`) - YAML frontmatter generation
- `main()` (`extract_article_metadata.py:200-230`) - CLI entry point with argument parsing

### Test Coverage:
- Comprehensive unit tests: `tests/test_extract_article_metadata.py:1-438`
- Functional/integration tests: `tests/test_functional.py:1-264`
- All tests currently passing with 100% coverage of existing functionality

### Key Constraints:
- The New Atlantis URL validation warning (`extract_article_metadata.py:215-218`)
- Edition inference depends on quarterly publication schedule
- All existing tests must continue to pass unchanged
- Fast execution path for The New Atlantis (no LLM overhead)

## Desired End State

A refactored script using the Strategy pattern with:

1. **Abstract base class** (`MetadataExtractor`) defining the interface
2. **NewAtlantisExtractor** - preserves existing logic, no LLM overhead
3. **LLMExtractor** - uses `llm` Python API with structured output for generic sites
4. **Site detection router** - `get_extractor_for_url()` factory function
5. **CLI enhancement** - `--model` argument for LLM model selection
6. **Updated dependencies** - `llm>=0.15.0` and `pydantic>=2.0.0`
7. **Comprehensive tests** - for new components while maintaining existing tests

### Verification Criteria:

#### Automated Verification:
- [ ] All existing tests pass: `python -m pytest tests/test_extract_article_metadata.py`
- [ ] All functional tests pass: `python -m pytest tests/test_functional.py`
- [ ] New extractor tests pass: `python -m pytest tests/test_extractors.py`
- [ ] Linting passes: `ruff check .`
- [ ] Code formatting passes: `ruff format --check .`
- [ ] No import errors when llm is not installed (graceful degradation)

#### Manual Verification:
- [ ] The New Atlantis URL extraction works identically to before (performance unchanged)
- [ ] Generic site URL extraction works with LLM (e.g., Medium, Substack articles)
- [ ] CLI help message reflects new `--model` argument
- [ ] Error messages for missing API keys are clear and actionable
- [ ] YAML output format remains unchanged for both extractors

## What We're NOT Doing

- Not adding batch processing or concurrent article extraction
- Not implementing caching of LLM responses (future enhancement)
- Not adding rate limiting for API calls
- Not creating extractors for specific sites beyond The New Atlantis (extensible for future)
- Not modifying the YAML output format
- Not adding authentication or credential management (relies on llm utility's key storage)
- Not implementing token usage tracking or cost monitoring
- Not changing the command-line interface for existing arguments

## Implementation Approach

Use the Strategy pattern with polymorphic extractors to achieve clean separation between site-specific and generic extraction logic. The `llm` utility's Python API with Pydantic schemas provides structured output validation and type safety, while the factory pattern enables easy extension for future site-specific extractors.

## Phase 1: Add Dependencies and Imports

### Overview
Set up the new dependencies and imports required for the multi-site architecture.

### Changes Required:

#### 1. Update `requirements.txt`
**File**: `requirements.txt`
**Changes**: Add new dependencies for LLM integration

```txt
requests>=2.25.0
beautifulsoup4>=4.9.0
pytest>=6.0.0
pytest-mock>=3.0.0
llm>=0.15.0
pydantic>=2.0.0
```

#### 2. Update imports in `extract_article_metadata.py`
**File**: `extract_article_metadata.py:1-14`
**Changes**: Add imports for new components

```python
#!/usr/bin/env python3
"""
Extract metadata from articles and generate Markdown headers for note-taking.
Supports The New Atlantis (specialized extraction) and generic sites (LLM-based extraction).
"""

import argparse
import json
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

# Optional llm import - gracefully handle if not installed
try:
    import llm
except ImportError:
    llm = None
```

### Success Criteria:

#### Automated Verification:
- [x] Dependencies install successfully: `pip install -r requirements.txt`
- [x] No import errors: `python -c "import extract_article_metadata"`
- [x] Script runs with --help: `python extract_article_metadata.py --help`
- [x] Linting passes: `ruff check .`

#### Manual Verification:
- [ ] llm utility is installed and accessible: `llm --version`
- [ ] All existing functionality still works (imports don't break existing code)

---

## Phase 2: Create Pydantic Schema and Abstract Base Class

### Overview
Define the data structures and interfaces for the extractor pattern.

### Changes Required:

#### 1. Add Pydantic Schema for Structured Output
**File**: `extract_article_metadata.py` (after imports, before `fetch_article_content`)
**Changes**: Create schema for LLM structured output

```python
class ArticleMetadata(BaseModel):
    """Pydantic schema for article metadata extraction with structured output."""
    title: str = Field(description="Article title or headline")
    authors: list[str] = Field(
        description="List of author names (full names, normalized)"
    )
    publication: str = Field(
        description="Publication name or website (e.g., 'The New Atlantis', 'Medium')"
    )
    date_published: Optional[str] = Field(
        default=None,
        description="Publication date in ISO format (YYYY-MM-DD) if available"
    )
```

#### 2. Create Abstract Base Class
**File**: `extract_article_metadata.py` (after ArticleMetadata)
**Changes**: Define extractor interface

```python
class MetadataExtractor(ABC):
    """Abstract base class for metadata extractors."""

    @abstractmethod
    def extract_metadata(self, html_content: str, url: str) -> dict:
        """
        Extract metadata from HTML content.

        Args:
            html_content: Raw HTML content from the article page
            url: Original URL of the article (for context)

        Returns:
            Dictionary with keys: title, authors, publication,
            and optionally: date_published, issue_number, issue_season
        """
        pass

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        """
        Check if this extractor supports the given URL.

        Args:
            url: The URL to check

        Returns:
            True if this extractor can handle the URL, False otherwise
        """
        pass
```

### Success Criteria:

#### Automated Verification:
- [x] No syntax errors: `python -c "from extract_article_metadata import ArticleMetadata, MetadataExtractor"`
- [x] Pydantic validation works: Test instantiation with valid/invalid data
- [x] Linting passes: `ruff check .`

#### Manual Verification:
- [ ] Schema fields match expected metadata structure
- [ ] Abstract methods are properly defined (cannot instantiate directly)

---

## Phase 3: Implement NewAtlantisExtractor

### Overview
Encapsulate existing The New Atlantis extraction logic into a concrete extractor class, preserving all existing functionality.

### Changes Required:

#### 1. Create NewAtlantisExtractor Class
**File**: `extract_article_metadata.py` (after `infer_edition_number` function)
**Changes**: Wrap existing extraction logic in a class

```python
class NewAtlantisExtractor(MetadataExtractor):
    """
    Specialized extractor for The New Atlantis articles.

    Uses JSON-LD structured data with HTML fallback, and infers
    edition numbers from season/year information.
    """

    def supports_url(self, url: str) -> bool:
        """Check if URL is from The New Atlantis."""
        parsed = urlparse(url)
        return "thenewatlantis.com" in parsed.netloc

    def extract_metadata(self, html_content: str, url: str) -> dict:
        """
        Extract metadata using The New Atlantis-specific logic.

        This is the existing extract_metadata() function logic,
        moved into the class.
        """
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
```

#### 2. Keep Original extract_metadata() as Wrapper (for backward compatibility)
**File**: `extract_article_metadata.py` (replace existing `extract_metadata` function)
**Changes**: Convert to wrapper function

```python
def extract_metadata(html_content):
    """
    Extract metadata from The New Atlantis article HTML.

    DEPRECATED: This function is kept for backward compatibility with existing tests.
    New code should use NewAtlantisExtractor directly.
    """
    extractor = NewAtlantisExtractor()
    return extractor.extract_metadata(html_content, "")
```

### Success Criteria:

#### Automated Verification:
- [x] All existing unit tests pass: `python -m pytest tests/test_extract_article_metadata.py -v`
- [x] Extractor instantiation works: `python -c "from extract_article_metadata import NewAtlantisExtractor; e = NewAtlantisExtractor()"`
- [x] supports_url() works correctly: Test with thenewatlantis.com and other URLs
- [x] Linting passes: `ruff check .`

#### Manual Verification:
- [ ] Extraction behavior is identical to original implementation
- [ ] Edition number inference still works correctly

---

## Phase 4: Implement LLMExtractor

### Overview
Create a generic extractor using the `llm` utility's Python API with structured output for sites that don't have specialized extractors.

### Changes Required:

#### 1. Create LLMExtractor Class
**File**: `extract_article_metadata.py` (after NewAtlantisExtractor)
**Changes**: Implement LLM-based extraction

```python
class LLMExtractor(MetadataExtractor):
    """
    Generic extractor using LLM for metadata extraction.

    Uses Simon Willison's llm utility with structured output (Pydantic schemas)
    to extract metadata from arbitrary websites.
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize LLM extractor.

        Args:
            model_name: Name of the LLM model to use (default: gpt-4o-mini)

        Raises:
            ImportError: If llm package is not installed
            RuntimeError: If llm model is not available or API key not configured
        """
        if llm is None:
            raise ImportError(
                "llm package not installed. Install with: pip install llm\n"
                "Then configure API keys with: llm keys set openai"
            )

        try:
            self.model = llm.get_model(model_name)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize LLM model '{model_name}': {e}\n"
                f"Ensure you have configured API keys: llm keys set openai"
            ) from e

        self.model_name = model_name

    def supports_url(self, url: str) -> bool:
        """LLMExtractor supports all URLs (fallback extractor)."""
        return True

    def extract_metadata(self, html_content: str, url: str) -> dict:
        """
        Extract metadata using LLM with structured output.

        Args:
            html_content: Raw HTML content
            url: Original URL (included in context for LLM)

        Returns:
            Dictionary with extracted metadata
        """
        # Convert HTML to text
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Extract text and limit length for token efficiency
        text = soup.get_text(separator="\n", strip=True)
        # Limit to ~4000 characters (roughly 1000 tokens)
        text = text[:4000]

        # Create prompt with context
        prompt = f"""Extract metadata from this article webpage.

URL: {url}

Article content:
{text}

Extract the following information:
- title: The article title or headline
- authors: List of author names (if available, otherwise empty list)
- publication: Name of the website or publication
- date_published: Publication date in YYYY-MM-DD format if available

Be accurate and only extract information that is clearly present."""

        try:
            # Use structured output for reliable extraction
            response = self.model.prompt(
                prompt,
                system="You are a metadata extraction assistant. Extract article metadata accurately and return structured data. If information is not available, use empty strings or empty lists as appropriate.",
                schema=ArticleMetadata
            )

            metadata_obj = response.schema_obj()

            # Convert Pydantic model to dict format matching NewAtlantisExtractor
            return {
                "title": metadata_obj.title,
                "authors": metadata_obj.authors,
                "publication": metadata_obj.publication,
                "date_published": metadata_obj.date_published,
            }

        except Exception as e:
            print(f"Error during LLM extraction: {e}", file=sys.stderr)
            # Return minimal metadata on failure
            return {
                "title": soup.find("title").get_text() if soup.find("title") else "Unknown Title",
                "authors": [],
                "publication": urlparse(url).netloc,
            }
```

### Success Criteria:

#### Automated Verification:
- [x] LLMExtractor instantiates with llm installed: `python -c "from extract_article_metadata import LLMExtractor; e = LLMExtractor()"`
- [x] ImportError raised when llm not installed (test with mocked import)
- [x] supports_url() returns True for any URL
- [x] Linting passes: `ruff check .`

#### Manual Verification:
- [ ] LLM extraction works with a test article (requires API key)
- [ ] Error messages are clear when API key is missing
- [ ] Text extraction properly removes script/style tags
- [ ] Token limit (4000 chars) is respected

---

## Phase 5: Implement Site Detection Router

### Overview
Create a factory function that routes URLs to the appropriate extractor.

### Changes Required:

#### 1. Create get_extractor_for_url() Function
**File**: `extract_article_metadata.py` (after LLMExtractor)
**Changes**: Add factory function

```python
def get_extractor_for_url(url: str, model_name: str = "gpt-4o-mini") -> MetadataExtractor:
    """
    Return appropriate metadata extractor based on URL.

    Args:
        url: The article URL to extract from
        model_name: LLM model name for generic extraction (default: gpt-4o-mini)

    Returns:
        MetadataExtractor instance (NewAtlantisExtractor or LLMExtractor)

    Raises:
        ImportError: If LLMExtractor is needed but llm is not installed
    """
    parsed_url = urlparse(url)

    # Check specialized extractors first
    if "thenewatlantis.com" in parsed_url.netloc:
        return NewAtlantisExtractor()

    # Fall back to LLM for generic sites
    return LLMExtractor(model_name=model_name)
```

### Success Criteria:

#### Automated Verification:
- [x] Returns NewAtlantisExtractor for thenewatlantis.com URLs
- [x] Returns LLMExtractor for other URLs
- [x] Handles subdomains correctly (www.thenewatlantis.com)
- [x] Passes model_name to LLMExtractor
- [x] Linting passes: `ruff check .`

#### Manual Verification:
- [ ] Router logic is clear and extensible for future extractors
- [ ] Error handling works when llm is not installed

---

## Phase 6: Refactor main() Function

### Overview
Update the CLI entry point to use the new extractor pattern and add `--model` argument.

### Changes Required:

#### 1. Update main() Function
**File**: `extract_article_metadata.py:200-230`
**Changes**: Refactor to use extractor pattern

```python
def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata from articles for note-taking. "
                    "Supports The New Atlantis (specialized) and generic sites (LLM-based)."
    )
    parser.add_argument("url", help="URL of the article")
    parser.add_argument(
        "--creation-date",
        help="Override creation date (YYYY-MM-DD format)",
        default=None,
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model for generic extraction (default: gpt-4o-mini). "
             "Only used for non-specialized sites.",
    )

    args = parser.parse_args()

    # Fetch HTML
    html_content = fetch_article_content(args.url)

    # Get appropriate extractor
    try:
        extractor = get_extractor_for_url(args.url, model_name=args.model)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            "\nFor generic site extraction, install: pip install llm",
            file=sys.stderr
        )
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract metadata using appropriate extractor
    metadata = extractor.extract_metadata(html_content, args.url)

    # Optional: Show which extractor was used (for user feedback)
    extractor_name = extractor.__class__.__name__
    if extractor_name != "NewAtlantisExtractor":
        print(f"# Using {extractor_name} with model: {args.model}", file=sys.stderr)

    # Warn if URL doesn't match common patterns (updated check)
    parsed_url = urlparse(args.url)
    if "thenewatlantis.com" not in parsed_url.netloc:
        print(
            "Info: Using LLM-based extraction for this site",
            file=sys.stderr
        )

    # Generate and print Markdown header
    markdown_header = format_markdown_header(metadata, args.creation_date)
    print(markdown_header)


if __name__ == "__main__":
    main()
```

### Success Criteria:

#### Automated Verification:
- [x] Script runs with --help: `python extract_article_metadata.py --help`
- [x] --model argument appears in help text
- [x] Old tests still pass (backward compatibility maintained)
- [x] Linting passes: `ruff check .`

#### Manual Verification:
- [ ] The New Atlantis URLs work without requiring LLM
- [ ] Generic URLs trigger LLM extraction
- [ ] User feedback messages are clear
- [ ] Error handling provides helpful guidance

---

## Phase 7: Create Tests for New Components

### Overview
Add comprehensive tests for the new extractor classes and routing logic while preserving all existing tests.

### Changes Required:

#### 1. Create tests/test_extractors.py
**File**: `tests/test_extractors.py` (NEW FILE)
**Changes**: Add tests for extractor classes

```python
#!/usr/bin/env python3
"""
Unit tests for metadata extractors (NewAtlantisExtractor and LLMExtractor).
"""

import pytest
from unittest.mock import Mock, patch

from extract_article_metadata import (
    NewAtlantisExtractor,
    LLMExtractor,
    get_extractor_for_url,
    ArticleMetadata,
)


class TestNewAtlantisExtractor:
    """Test cases for NewAtlantisExtractor."""

    def test_supports_url_thenewatlantis(self):
        """Test that NewAtlantisExtractor supports thenewatlantis.com URLs."""
        extractor = NewAtlantisExtractor()

        assert extractor.supports_url("https://www.thenewatlantis.com/article")
        assert extractor.supports_url("https://thenewatlantis.com/publications/test")
        assert not extractor.supports_url("https://example.com/article")

    def test_extract_metadata_json_ld(self):
        """Test extraction using JSON-LD (primary method)."""
        extractor = NewAtlantisExtractor()

        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Article",
                "headline": "Test Article",
                "author": [{"name": "Author Name"}]
            }
            </script>
        </head>
        </html>
        """

        metadata = extractor.extract_metadata(html, "https://thenewatlantis.com/test")

        assert metadata["title"] == "Test Article"
        assert metadata["authors"] == ["Author Name"]
        assert metadata["publication"] == "The New Atlantis"

    def test_extract_metadata_with_issue_inference(self):
        """Test that edition number inference works."""
        extractor = NewAtlantisExtractor()

        html = """
        <html>
        <body>
            <h1>Test Article</h1>
            <p>Published in Winter 2025</p>
        </body>
        </html>
        """

        metadata = extractor.extract_metadata(html, "https://thenewatlantis.com/test")

        assert metadata["issue_number"] == "79"
        assert metadata["issue_season"] == "Winter 2025"


class TestLLMExtractor:
    """Test cases for LLMExtractor."""

    def test_llm_extractor_import_error(self):
        """Test that LLMExtractor raises ImportError when llm not installed."""
        with patch("extract_article_metadata.llm", None):
            with pytest.raises(ImportError, match="llm package not installed"):
                LLMExtractor()

    @patch("extract_article_metadata.llm")
    def test_llm_extractor_initialization(self, mock_llm):
        """Test LLMExtractor initialization with mocked llm."""
        mock_model = Mock()
        mock_llm.get_model.return_value = mock_model

        extractor = LLMExtractor(model_name="gpt-4o-mini")

        assert extractor.model == mock_model
        assert extractor.model_name == "gpt-4o-mini"
        mock_llm.get_model.assert_called_once_with("gpt-4o-mini")

    @patch("extract_article_metadata.llm")
    def test_llm_extractor_supports_all_urls(self, mock_llm):
        """Test that LLMExtractor supports all URLs (fallback)."""
        mock_llm.get_model.return_value = Mock()
        extractor = LLMExtractor()

        assert extractor.supports_url("https://example.com/article")
        assert extractor.supports_url("https://medium.com/@user/post")
        assert extractor.supports_url("https://thenewatlantis.com/test")

    @patch("extract_article_metadata.llm")
    def test_llm_extractor_extraction(self, mock_llm):
        """Test LLM extraction with mocked response."""
        # Mock LLM response
        mock_metadata = ArticleMetadata(
            title="Test Article",
            authors=["John Doe"],
            publication="Example Site",
            date_published="2025-01-15"
        )

        mock_response = Mock()
        mock_response.schema_obj.return_value = mock_metadata

        mock_model = Mock()
        mock_model.prompt.return_value = mock_response
        mock_llm.get_model.return_value = mock_model

        extractor = LLMExtractor()

        html = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <h1>Test Article</h1>
            <p>By John Doe</p>
            <p>Published on Example Site</p>
        </body>
        </html>
        """

        metadata = extractor.extract_metadata(html, "https://example.com/test")

        assert metadata["title"] == "Test Article"
        assert metadata["authors"] == ["John Doe"]
        assert metadata["publication"] == "Example Site"
        assert metadata["date_published"] == "2025-01-15"

    @patch("extract_article_metadata.llm")
    def test_llm_extractor_removes_script_tags(self, mock_llm):
        """Test that script and style tags are removed before LLM processing."""
        mock_metadata = ArticleMetadata(
            title="Clean Article",
            authors=[],
            publication="Test"
        )

        mock_response = Mock()
        mock_response.schema_obj.return_value = mock_metadata

        mock_model = Mock()
        mock_model.prompt.return_value = mock_response
        mock_llm.get_model.return_value = mock_model

        extractor = LLMExtractor()

        html = """
        <html>
        <head>
            <script>alert('test');</script>
            <style>.test { color: red; }</style>
        </head>
        <body>
            <h1>Clean Article</h1>
            <script>console.log('remove me');</script>
        </body>
        </html>
        """

        extractor.extract_metadata(html, "https://example.com/test")

        # Verify prompt doesn't contain script content
        call_args = mock_model.prompt.call_args[0][0]
        assert "alert('test')" not in call_args
        assert "console.log" not in call_args

    @patch("extract_article_metadata.llm")
    def test_llm_extractor_error_handling(self, mock_llm):
        """Test error handling when LLM extraction fails."""
        mock_model = Mock()
        mock_model.prompt.side_effect = Exception("API Error")
        mock_llm.get_model.return_value = mock_model

        extractor = LLMExtractor()

        html = """
        <html>
        <head><title>Fallback Title</title></head>
        <body><p>Content</p></body>
        </html>
        """

        metadata = extractor.extract_metadata(html, "https://example.com/test")

        # Should return fallback metadata
        assert metadata["title"] == "Fallback Title"
        assert metadata["authors"] == []
        assert metadata["publication"] == "example.com"


class TestSiteDetection:
    """Test cases for get_extractor_for_url() routing."""

    def test_get_extractor_for_thenewatlantis(self):
        """Test that The New Atlantis URLs get NewAtlantisExtractor."""
        extractor = get_extractor_for_url("https://www.thenewatlantis.com/article")
        assert isinstance(extractor, NewAtlantisExtractor)

    @patch("extract_article_metadata.llm")
    def test_get_extractor_for_generic_site(self, mock_llm):
        """Test that generic URLs get LLMExtractor."""
        mock_llm.get_model.return_value = Mock()

        extractor = get_extractor_for_url("https://example.com/article")
        assert isinstance(extractor, LLMExtractor)

    @patch("extract_article_metadata.llm")
    def test_get_extractor_passes_model_name(self, mock_llm):
        """Test that model_name is passed to LLMExtractor."""
        mock_model = Mock()
        mock_llm.get_model.return_value = mock_model

        extractor = get_extractor_for_url(
            "https://example.com/article",
            model_name="claude-3.5-sonnet"
        )

        assert isinstance(extractor, LLMExtractor)
        assert extractor.model_name == "claude-3.5-sonnet"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

#### 2. Update tests/test_functional.py
**File**: `tests/test_functional.py`
**Changes**: Add tests for multi-site functionality

Add to the end of the file (before `if __name__ == "__main__":`):

```python
class TestMultiSiteFunctional:
    """Functional tests for multi-site support."""

    @patch("extract_article_metadata.llm")
    @patch("extract_article_metadata.requests.get")
    @patch("sys.argv", ["script.py", "https://example.com/article"])
    def test_main_with_generic_site(self, mock_get, mock_llm, capsys):
        """Test main() function with a generic (non-New Atlantis) site."""
        # Mock HTML
        mock_html = """
        <html>
        <head><title>Generic Article</title></head>
        <body>
            <h1>Generic Article Title</h1>
            <p>By Generic Author</p>
        </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock LLM
        from extract_article_metadata import ArticleMetadata
        mock_metadata = ArticleMetadata(
            title="Generic Article Title",
            authors=["Generic Author"],
            publication="Example.com"
        )

        mock_llm_response = Mock()
        mock_llm_response.schema_obj.return_value = mock_metadata

        mock_model = Mock()
        mock_model.prompt.return_value = mock_llm_response
        mock_llm.get_model.return_value = mock_model

        main()

        captured = capsys.readouterr()
        assert "title: Generic Article Title" in captured.out
        assert "  - Generic Author" in captured.out
        assert "publication: Example.com" in captured.out

    @patch("extract_article_metadata.requests.get")
    @patch("sys.argv", ["script.py", "--model", "claude-3.5-sonnet", "https://www.thenewatlantis.com/article"])
    def test_main_with_model_argument_ignored_for_specialized(self, mock_get, capsys):
        """Test that --model argument is accepted but not used for The New Atlantis."""
        mock_html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Article",
                "headline": "TNA Article",
                "author": [{"name": "TNA Author"}]
            }
            </script>
        </head>
        </html>
        """

        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        main()

        captured = capsys.readouterr()
        assert "title: TNA Article" in captured.out
        # Should not have used LLM (no LLM info message)
```

### Success Criteria:

#### Automated Verification:
- [x] All new tests pass: `python -m pytest tests/test_extractors.py -v`
- [x] All existing tests still pass: `python -m pytest tests/test_extract_article_metadata.py -v`
- [x] All functional tests pass: `python -m pytest tests/test_functional.py -v`
- [x] Full test suite passes: `python -m pytest -v`
- [x] Linting passes: `ruff check .`
- [x] Code formatting passes: `ruff format --check .`

#### Manual Verification:
- [ ] Tests cover both happy path and error cases
- [ ] Mocking is used appropriately to avoid real API calls
- [ ] Test organization is clear and maintainable

---

## Phase 8: Update Documentation

### Overview
Update README.md and docstrings to reflect multi-site support.

### Changes Required:

#### 1. Update README.md Features Section
**File**: `README.md:5-13`
**Changes**: Add multi-site support to features

```markdown
## Features

- **Multi-site support**: Extract metadata from The New Atlantis and generic websites
- **Specialized extraction** for The New Atlantis with no LLM overhead
- **LLM-based extraction** for generic sites using Simon Willison's `llm` utility
- Extracts article metadata including title, author(s), and issue information
- Generates properly formatted YAML front matter for Markdown notes
- Supports both JSON-LD structured data and HTML fallback parsing
- **Automatically infers edition numbers** from season information when explicit numbers aren't available (The New Atlantis)
- Normalizes author names and handles multiple authors
- Command-line interface with customizable creation dates and LLM model selection
- Comprehensive error handling and validation
```

#### 2. Update README.md Installation Section
**File**: `README.md:15-32`
**Changes**: Add llm setup instructions

```markdown
## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd article-assistant
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure LLM API keys (for generic site extraction):
```bash
# For OpenAI (recommended)
llm keys set openai

# Or for Anthropic Claude
pip install llm-anthropic
llm keys set anthropic

# Verify installation
llm --version
```

**Note**: LLM configuration is only required for extracting metadata from generic websites. The New Atlantis extraction works without any API keys.
```

#### 3. Update README.md Usage Section
**File**: `README.md:34-72`
**Changes**: Add examples for both site types

```markdown
## Usage

### Basic Usage

**Extract metadata from a New Atlantis article** (specialized, fast, no LLM):

```bash
python extract_article_metadata.py "https://www.thenewatlantis.com/publications/the-tyranny-of-now"
```

**Extract metadata from a generic website** (LLM-based):

```bash
python extract_article_metadata.py "https://example.com/article-url"
```

**Output:**
```yaml
---
title: The Tyranny of Now
author:
  - Nicholas Carr
format: journal article
creation-date: 2025-06-19
publication: The New Atlantis
---

## Notes
```

### Specifying LLM Model

Choose a different LLM model for generic extraction:

```bash
# Use OpenAI GPT-4
python extract_article_metadata.py --model gpt-4o "https://example.com/article"

# Use Anthropic Claude (requires llm-anthropic plugin)
python extract_article_metadata.py --model claude-3.5-sonnet "https://example.com/article"
```

**Note**: The `--model` argument only affects generic site extraction. The New Atlantis uses specialized extraction logic.

### Custom Creation Date

Specify a custom creation date:

```bash
python extract_article_metadata.py --creation-date 2024-12-01 "https://example.com/article-url"
```

### Help

View all available options:

```bash
python extract_article_metadata.py --help
```
```

#### 4. Update README.md Technical Details Section
**File**: `README.md:142-174`
**Changes**: Document new architecture

```markdown
## Technical Details

### Architecture

The script uses the **Strategy pattern** with polymorphic extractors:

- **MetadataExtractor** (ABC): Abstract interface defining `extract_metadata()` and `supports_url()`
- **NewAtlantisExtractor**: Specialized extractor for The New Atlantis articles
  - JSON-LD structured data parsing (primary)
  - HTML fallback parsing (secondary)
  - Edition number inference from season/year
  - No external API calls - fast and free
- **LLMExtractor**: Generic extractor using `llm` utility
  - Structured output with Pydantic schemas
  - HTML-to-text conversion with cleanup
  - Token-efficient (4000 char limit)
  - Graceful error handling
- **get_extractor_for_url()**: Factory function for site detection routing

### Site Detection

The script automatically detects the site and uses the appropriate extractor:

1. **The New Atlantis** (`thenewatlantis.com`): Uses `NewAtlantisExtractor`
2. **All other sites**: Uses `LLMExtractor` with configured model

### Metadata Extraction

**For The New Atlantis:**
1. **Primary**: JSON-LD structured data parsing for reliable metadata extraction
2. **Fallback**: HTML parsing when structured data is unavailable or malformed
3. **Edition Inference**: Automatically calculates edition numbers from season/year information

**For Generic Sites:**
1. **HTML Cleaning**: Remove script, style, nav, header, footer tags
2. **Text Extraction**: Convert to plain text (limited to 4000 chars)
3. **LLM Extraction**: Use structured output (Pydantic schema) for validation
4. **Fallback**: Basic HTML parsing if LLM fails

### Supported Metadata Fields

- **Title**: Article headline
- **Author(s)**: Single or multiple authors with whitespace normalization
- **Publication**: Publication name or website
- **Issue Information**: Issue number and season (The New Atlantis only)
- **Date Published**: Publication date in ISO format (when available)
- **Creation Date**: Current date or user-specified date

### Edition Number Inference (The New Atlantis)

When articles only display season information (e.g., "Winter 2025") without explicit edition numbers, the script automatically calculates the correct edition number using The New Atlantis's quarterly publication schedule:

- **Publication Pattern**: Winter, Spring, Summer, Fall (4 issues per year)
- **Reference Points**: Winter 2025 = No. 79, Summer 2025 = No. 81
- **Calculation**: Supports past and future years with accurate numbering
- **Format Support**: Handles both "Season Year" and "Year Season" formats

### Error Handling

- Network request failures with informative error messages
- Graceful degradation when metadata is missing
- LLM API errors with fallback to basic HTML parsing
- Clear error messages for missing API keys
- Proper exit codes for scripting integration
```

#### 5. Update README.md Dependencies Section
**File**: `README.md:176-182`
**Changes**: Document new dependencies

```markdown
## Dependencies

### Core Dependencies
- **requests**: HTTP library for fetching article content
- **beautifulsoup4**: HTML parsing and DOM navigation

### Multi-Site Support Dependencies
- **llm**: Python library for LLM interactions (generic site extraction)
- **pydantic**: Data validation and structured output schemas

### Development Dependencies
- **pytest**: Testing framework
- **pytest-mock**: Mocking utilities for tests
```

#### 6. Add README.md Troubleshooting for LLM
**File**: `README.md:210-233` (after existing troubleshooting)
**Changes**: Add LLM-specific troubleshooting

```markdown
**LLM extraction errors:**

- **"llm package not installed"**:
  ```bash
  pip install llm
  ```

- **"Failed to initialize LLM model" / API key errors**:
  ```bash
  # Configure API key for your chosen provider
  llm keys set openai
  # Or
  llm keys set anthropic
  ```

- **"Model not available"**:
  ```bash
  # List available models
  llm models list

  # Install additional model plugins
  pip install llm-anthropic  # For Claude
  pip install llm-ollama     # For local models
  ```

- **Slow LLM extraction**:
  - LLM extraction is slower than specialized extraction due to API calls
  - Consider using local models via `llm-ollama` plugin for faster inference
  - The New Atlantis extraction remains fast (no LLM overhead)

- **LLM extraction accuracy**:
  - LLM extraction quality depends on the model used
  - `gpt-4o-mini` provides good balance of speed, cost, and accuracy
  - For higher accuracy, use `gpt-4o` or `claude-3.5-sonnet` with `--model` flag
  - Always verify extracted metadata manually
```

### Success Criteria:

#### Automated Verification:
- [x] README renders correctly in Markdown preview
- [x] All code examples have correct syntax
- [x] Links are valid (if any external links added)

#### Manual Verification:
- [ ] Documentation clearly explains multi-site support
- [ ] Installation instructions are complete and accurate
- [ ] Usage examples cover both The New Atlantis and generic sites
- [ ] Troubleshooting section addresses common issues
- [ ] Architecture explanation is clear and accurate

---

## Testing Strategy

### Unit Tests

**Existing tests** (`tests/test_extract_article_metadata.py`):
- All 438 lines of existing tests must pass unchanged
- Tests for `extract_metadata()` function (now a wrapper)
- Tests for `format_markdown_header()`, `fetch_article_content()`, `infer_edition_number()`

**New tests** (`tests/test_extractors.py`):
- `TestNewAtlantisExtractor`: Verify supports_url(), extract_metadata() with JSON-LD and HTML
- `TestLLMExtractor`: Test initialization, extraction, error handling, with mocked llm
- `TestSiteDetection`: Test get_extractor_for_url() routing logic

### Integration Tests

**Existing functional tests** (`tests/test_functional.py`):
- End-to-end CLI tests with mocked HTTP requests
- Tests for argument parsing, error handling, output formatting

**New functional tests**:
- Multi-site support with both extractor types
- --model argument handling
- User feedback messages

### Manual Testing Steps

1. **The New Atlantis extraction** (no API key required):
   ```bash
   python extract_article_metadata.py "https://www.thenewatlantis.com/publications/the-tyranny-of-now"
   ```
   Verify: Output matches previous behavior, no LLM overhead

2. **Generic site extraction** (requires API key):
   ```bash
   llm keys set openai  # Configure key first
   python extract_article_metadata.py "https://example.com/article"
   ```
   Verify: LLM extraction works, metadata is reasonable

3. **Model selection**:
   ```bash
   python extract_article_metadata.py --model gpt-4o "https://example.com/article"
   ```
   Verify: Different model is used, extraction quality may vary

4. **Error handling** (without API key):
   ```bash
   python extract_article_metadata.py "https://example.com/article"
   ```
   Verify: Clear error message about missing API key

5. **Help message**:
   ```bash
   python extract_article_metadata.py --help
   ```
   Verify: New --model argument is documented

## Performance Considerations

### The New Atlantis (NewAtlantisExtractor)
- **No performance impact**: Uses existing direct HTML parsing logic
- **No API calls**: No network overhead beyond initial article fetch
- **Fast execution**: Same speed as current implementation (~0.1-0.5 seconds)

### Generic Sites (LLMExtractor)
- **API latency**: 1-3 seconds for LLM API calls (varies by provider)
- **Token usage**: ~100-300 tokens per extraction (input limited to 4000 chars)
- **Cost**: Minimal ($0.0001-0.001 per article with gpt-4o-mini)
- **Rate limits**: Subject to API provider rate limits (typically 60-90 requests/minute)

### Optimization Opportunities (Future)
- Implement response caching to avoid duplicate API calls
- Add batch processing with concurrent requests
- Support local models via llm-ollama plugin for faster inference
- Implement retry logic with exponential backoff for rate limits

## Migration Notes

### Backward Compatibility

- **Existing `extract_metadata()` function preserved** as a wrapper for backward compatibility
- **All existing tests pass unchanged** - no modifications required
- **CLI interface backward compatible** - existing scripts using the tool continue to work
- **Output format unchanged** - YAML frontmatter format remains identical

### Breaking Changes

**None** - This is a fully backward-compatible enhancement.

### Deprecation Notices

- `extract_metadata(html_content)` function is now a wrapper around `NewAtlantisExtractor`
- New code should use `get_extractor_for_url()` and extractor classes directly
- The function will be maintained for backward compatibility but is not recommended for new code

## References

- Original research: `thoughts/shared/research/2025-09-29-multi-site-metadata-extraction.md`
- llm utility documentation: https://llm.datasette.io/
- llm Python API: https://llm.datasette.io/en/stable/python-api.html
- Simon Willison's articles: https://simonwillison.net/tags/llm/
- Pydantic documentation: https://docs.pydantic.dev/
- Current implementation: `extract_article_metadata.py:1-231`
- Unit tests: `tests/test_extract_article_metadata.py:1-438`
- Functional tests: `tests/test_functional.py:1-264`