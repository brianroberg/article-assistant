---
date: 2025-09-29T00:00:00Z
researcher: robergb
git_commit: b9f31859ed39261b7c46b51c318c6b46254aeab7
branch: main
repository: brianroberg/article-assistant
topic: "Expanding article-assistant to support multiple sites with LLM-based extraction"
tags: [research, codebase, metadata-extraction, llm-integration, multi-site-support]
status: complete
last_updated: 2025-09-29
last_updated_by: robergb
---

# Research: Expanding article-assistant to support multiple sites with LLM-based extraction

**Date**: 2025-09-29T00:00:00Z
**Researcher**: robergb
**Git Commit**: b9f31859ed39261b7c46b51c318c6b46254aeab7
**Branch**: main
**Repository**: brianroberg/article-assistant

## Research Question

How should the article-assistant script be expanded to support metadata extraction from multiple sites (not just The New Atlantis) using the `llm` utility for generic article extraction, while preserving the existing specialized extraction for The New Atlantis?

## Summary

The current implementation (`extract_article_metadata.py`) uses a sophisticated two-phase extraction strategy specifically tailored for The New Atlantis. To expand support to other sites, the architecture should adopt an extractor pattern with site detection routing between a specialized `NewAtlantisExtractor` (preserving existing logic) and a generic `LLMExtractor` (using Simon Willison's `llm` utility). The `llm` tool's Python API with structured output (Pydantic schemas) provides reliable metadata extraction from arbitrary websites while maintaining the performance advantage of direct HTML parsing for known sites.

## Detailed Findings

### Current Implementation Architecture

#### Main Script Structure (`extract_article_metadata.py:1-231`)

The script currently implements a monolithic extraction pipeline with four core functions:

1. **`fetch_article_content(url)`** (`extract_article_metadata.py:17-29`)
   - HTTP fetch with custom User-Agent
   - Uses `requests` library with error handling
   - Returns raw HTML content

2. **`extract_metadata(html_content)`** (`extract_article_metadata.py:71-159`)
   - Two-phase extraction strategy:
     - **Primary**: JSON-LD structured data parsing (`extract_article_metadata.py:76-102`)
     - **Fallback**: HTML parsing with BeautifulSoup (`extract_article_metadata.py:104-154`)
   - Handles multiple author formats (dict vs list)
   - Whitespace normalization for author names
   - Issue information extraction with regex patterns
   - Calls `infer_edition_number()` when explicit numbers unavailable

3. **`infer_edition_number(season, year)`** (`extract_article_metadata.py:32-68`)
   - The New Atlantis-specific edition calculation
   - Base reference: Winter 2025 = No. 79
   - Quarterly publication schedule (4 issues/year)
   - Supports both past and future years
   - Case-insensitive season matching
   - Handles both "Season Year" and "Year Season" formats

4. **`format_markdown_header(metadata, creation_date)`** (`extract_article_metadata.py:162-197`)
   - Generates YAML frontmatter for note-taking apps
   - Handles single and multiple authors
   - Optional periodical edition information
   - Default creation date to current date

#### Test Coverage (`tests/test_extract_article_metadata.py:1-438`)

Comprehensive test suite with 438 lines covering:
- JSON-LD extraction with various author formats
- HTML fallback parsing
- Author prefix cleanup ("by", "author:")
- Whitespace normalization
- Issue information extraction (explicit and inferred)
- Edition number inference for all seasons across multiple years
- Error handling for network failures
- Edge cases and boundary conditions

### Simon Willison's llm Utility

#### Core Capabilities

**Documentation**: https://llm.datasette.io/

The `llm` utility is both a CLI tool and Python library that provides:

1. **Unified interface** for multiple LLM providers (OpenAI, Anthropic Claude, Google Gemini, etc.)
2. **Local and remote models** support
3. **SQLite logging** of all interactions
4. **Structured output** via Pydantic schemas
5. **Plugin ecosystem** with 50+ plugins
6. **Conversation management** for multi-turn interactions
7. **Tool integration** for function calling

#### Installation and Setup

```bash
# Installation
pip install llm

# API key configuration (stored securely)
llm keys set openai
llm keys set anthropic

# Set default model
llm models default gpt-4o-mini
```

Key storage locations:
- macOS: `~/Library/Application Support/io.datasette.llm/keys.json`
- Linux: `~/.config/io.datasette.llm/keys.json`

#### Python API Usage (Recommended Approach)

**Basic extraction pattern**:
```python
import llm

model = llm.get_model("gpt-4o-mini")
response = model.prompt("Extract metadata from this article")
print(response.text())
```

**Structured output with Pydantic schemas**:
```python
from pydantic import BaseModel

class ArticleMetadata(BaseModel):
    title: str
    authors: list[str]
    publication: str
    date_published: Optional[str]

model = llm.get_model("gpt-4o-mini")
response = model.prompt(
    "Extract metadata from this article text...",
    schema=ArticleMetadata
)
metadata = response.schema_obj()  # Returns ArticleMetadata instance
```

**Key advantages over subprocess calls**:
- Faster execution (no process overhead)
- Full programmatic control
- Native streaming support
- Rich response objects with metadata
- Better error handling through Python exceptions

#### Supported Models

**Built-in (OpenAI)**:
- `gpt-4o`, `gpt-4o-mini` (recommended for this use case)
- `gpt-4.1`, `gpt-4.1-mini`
- `o1` (reasoning models)

**Via plugins**:
- `llm-anthropic`: Claude models
- `llm-gemini`: Google Gemini
- `llm-ollama`: Local models via Ollama
- `llm-groq`: Fast inference API

**Recommendation**: `gpt-4o-mini` balances cost, speed, and accuracy for metadata extraction tasks.

#### Best Practices (from Simon Willison)

1. **"You have to test what it writes!"** - Always validate LLM output
2. Set realistic expectations - LLMs are "fancy autocomplete"
3. Provide clear, specific instructions with context
4. Use structured output for reliable data extraction
5. Account for training cutoff dates
6. Integrate following Unix philosophy (pipes, composition)

### Proposed Multi-Site Architecture

#### Design Pattern: Strategy Pattern with Site Detection

```
User provides URL
    ↓
fetch_article_content(url) - HTTP fetch
    ↓
get_extractor_for_url(url) - Route based on domain
    ↓
    ├─→ NewAtlantisExtractor (thenewatlantis.com)
    │   - Uses existing specialized logic
    │   - JSON-LD parsing + HTML fallback
    │   - Edition number inference
    │   - Fast, no LLM overhead
    │
    └─→ LLMExtractor (all other sites)
        - Uses llm utility with structured output
        - Converts HTML to text
        - Pydantic schema for validation
        - Handles arbitrary site structures
    ↓
format_markdown_header(metadata) - YAML generation
```

#### Component Architecture

**1. Abstract Base Class**
```python
from abc import ABC, abstractmethod

class MetadataExtractor(ABC):
    """Base interface for metadata extractors."""

    @abstractmethod
    def extract_metadata(self, html_content: str, url: str) -> dict:
        """Extract metadata from HTML content."""
        pass

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        """Check if this extractor supports the given URL."""
        pass
```

**2. NewAtlantisExtractor**
- Encapsulates existing `extract_metadata()` logic (`extract_article_metadata.py:71-159`)
- Includes `infer_edition_number()` functionality
- Preserves all existing behavior and test compatibility
- Returns standardized metadata dictionary
- Fast execution without external API calls

**3. LLMExtractor**
```python
class LLMExtractor(MetadataExtractor):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        if llm is None:
            raise ImportError("llm package not installed")
        self.model = llm.get_model(model_name)

    def extract_metadata(self, html_content: str, url: str) -> dict:
        # Convert HTML to text
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script/style tags
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text()[:4000]  # Limit token usage

        # Use structured output for reliable extraction
        response = self.model.prompt(
            f"Extract article metadata from this webpage:\n\n{text}",
            system="You are a metadata extraction assistant. Extract title, author(s), publication name, and publication date if available. Return structured data.",
            schema=ArticleMetadata
        )

        metadata_obj = response.schema_obj()

        # Convert Pydantic model to dict format
        return {
            "title": metadata_obj.title,
            "authors": metadata_obj.authors,
            "publication": metadata_obj.publication,
            "date_published": metadata_obj.date_published,
        }

    def supports_url(self, url: str) -> bool:
        return True  # Fallback for all URLs
```

**4. Site Detection Router**
```python
def get_extractor_for_url(url: str) -> MetadataExtractor:
    """Return appropriate extractor based on URL."""
    parsed_url = urlparse(url)

    if "thenewatlantis.com" in parsed_url.netloc:
        return NewAtlantisExtractor()
    else:
        return LLMExtractor()
```

**5. Pydantic Schema for Structured Output**
```python
from pydantic import BaseModel, Field

class ArticleMetadata(BaseModel):
    """Schema for article metadata extraction."""
    title: str = Field(description="Article title")
    authors: list[str] = Field(description="List of author names")
    publication: str = Field(description="Publication or website name")
    date_published: Optional[str] = Field(
        default=None,
        description="Publication date (ISO format if possible)"
    )
```

#### Refactored Main Function Flow

```python
def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata from articles for note-taking"
    )
    parser.add_argument("url", help="URL of the article")
    parser.add_argument("--creation-date", help="Override creation date (YYYY-MM-DD)")
    parser.add_argument("--model", default="gpt-4o-mini",
                       help="LLM model for generic extraction")

    args = parser.parse_args()

    # Fetch HTML
    html_content = fetch_article_content(args.url)

    # Get appropriate extractor
    extractor = get_extractor_for_url(args.url)

    # Extract metadata
    metadata = extractor.extract_metadata(html_content, args.url)

    # Generate and print Markdown
    markdown_header = format_markdown_header(metadata, args.creation_date)
    print(markdown_header)
```

### Key Design Decisions

1. **Preserve The New Atlantis Performance**
   - No LLM overhead for known sites
   - Existing logic remains unchanged
   - All 438 lines of tests remain valid
   - Fast execution path maintained

2. **Use Python API over Subprocess**
   - More efficient (no process spawning)
   - Better error handling
   - Access to structured output features
   - Richer response metadata

3. **Structured Output for Reliability**
   - Pydantic schemas enforce data structure
   - Validation built-in
   - Type safety
   - Easier to test

4. **Extensible Architecture**
   - Easy to add more site-specific extractors
   - Registry pattern possible for future expansion
   - Clear separation of concerns
   - Follows open/closed principle

5. **Model Selection**
   - `gpt-4o-mini` as default: fast, cost-effective
   - Configurable via CLI argument
   - Plugin support allows local models (llm-ollama)

6. **Error Handling Strategy**
   - Graceful fallback if llm not installed
   - Clear error messages for missing API keys
   - LLM failures don't crash script
   - Validation errors caught and reported

### Testing Strategy

#### Unit Tests for New Components

**Test NewAtlantisExtractor**:
- All existing tests from `test_extract_article_metadata.py` adapted
- Verify `supports_url()` returns True for thenewatlantis.com
- Ensure identical behavior to original implementation

**Test LLMExtractor**:
- Mock `llm.get_model()` and responses
- Test structured output parsing
- Verify text truncation (4000 chars)
- Test script/style tag removal
- Error handling for missing llm package
- Various HTML structures (basic, complex, malformed)

**Test site detection**:
- `get_extractor_for_url()` returns correct extractor
- Various domain patterns tested
- Edge cases (subdomains, paths, query params)

#### Integration Tests

**Functional tests** (`tests/test_functional.py`):
- End-to-end flow with mocked HTTP and LLM
- The New Atlantis articles (existing tests)
- Generic website articles (new tests)
- CLI argument handling
- YAML output validation

#### Test Organization

```python
# tests/test_extractors.py
class TestNewAtlantisExtractor:
    # Existing tests migrated here

class TestLLMExtractor:
    # New tests for LLM-based extraction

class TestSiteDetection:
    # Tests for get_extractor_for_url()

# tests/test_functional.py
# End-to-end tests with both extractor types
```

### Dependencies Update

**`requirements.txt` additions**:
```
llm>=0.15.0  # Python API for LLM interactions
pydantic>=2.0.0  # Structured output schemas
```

**Existing dependencies maintained**:
- `requests>=2.25.0` - HTTP fetching
- `beautifulsoup4>=4.9.0` - HTML parsing
- `pytest>=6.0.0` - Testing framework
- `pytest-mock>=3.0.0` - Mocking utilities

### Documentation Updates

#### README.md Changes Required

1. **Features section** - Add multi-site support
2. **Installation** - Include llm setup instructions:
   ```bash
   pip install -r requirements.txt
   llm keys set openai  # Or anthropic, etc.
   ```
3. **Usage examples** - Add generic site examples:
   ```bash
   # The New Atlantis (specialized, no LLM)
   python extract_article_metadata.py "https://www.thenewatlantis.com/..."

   # Generic site (LLM-based)
   python extract_article_metadata.py "https://example.com/article"

   # Specify LLM model
   python extract_article_metadata.py --model claude-3.5-sonnet "https://..."
   ```
4. **Technical Details** - Document architecture:
   - Extractor pattern explanation
   - Site detection logic
   - LLM integration approach
5. **Dependencies** - Explain llm utility purpose
6. **Troubleshooting** - Add LLM-specific issues:
   - Missing API keys
   - llm package not installed
   - Model availability

## Code References

### Current Implementation
- `extract_article_metadata.py:17-29` - `fetch_article_content()` function
- `extract_article_metadata.py:32-68` - `infer_edition_number()` function
- `extract_article_metadata.py:71-159` - `extract_metadata()` function
- `extract_article_metadata.py:162-197` - `format_markdown_header()` function
- `extract_article_metadata.py:200-230` - `main()` function and CLI
- `tests/test_extract_article_metadata.py:1-438` - Comprehensive unit tests

### Key Files
- `extract_article_metadata.py` - Main script (231 lines)
- `tests/test_extract_article_metadata.py` - Unit tests (438 lines)
- `tests/test_functional.py` - Functional tests
- `requirements.txt` - Python dependencies (4 entries)
- `README.md` - Project documentation
- `CLAUDE.md` - Development guidelines

## Architecture Documentation

### Current Design Pattern

**Monolithic procedural architecture**:
- Single module with standalone functions
- No abstraction for different site types
- Direct HTML parsing with site-specific logic
- Hardcoded for The New Atlantis

### Proposed Design Pattern

**Strategy pattern with polymorphic extractors**:
- Abstract `MetadataExtractor` interface
- Concrete implementations for different sites
- Factory function for site detection/routing
- Dependency injection for testability
- Open for extension, closed for modification

### Data Flow

```
URL Input
    ↓
HTTP Fetch (requests) → HTML Content
    ↓
Site Detection (urlparse) → Domain Analysis
    ↓
    ├─→ The New Atlantis Domain
    │   ├─→ JSON-LD Extraction
    │   ├─→ HTML Fallback Parsing
    │   ├─→ Edition Number Inference
    │   └─→ Standardized Metadata Dict
    │
    └─→ Other Domains
        ├─→ HTML → Text Conversion
        ├─→ LLM API Call (llm library)
        ├─→ Structured Output (Pydantic)
        └─→ Standardized Metadata Dict
    ↓
YAML Frontmatter Generation
    ↓
Console Output
```

### Extension Points

Future extractors can be added for:
- Academic publishers (JSTOR, arXiv)
- News sites (NYT, Washington Post)
- Blogs (Medium, Substack)
- Technical docs (MDN, Read the Docs)

Pattern for adding new extractors:
```python
class JSSTORExtractor(MetadataExtractor):
    def supports_url(self, url: str) -> bool:
        return "jstor.org" in urlparse(url).netloc

    def extract_metadata(self, html_content: str, url: str) -> dict:
        # JSTOR-specific extraction logic
        pass

# Update router
def get_extractor_for_url(url: str) -> MetadataExtractor:
    for extractor_class in [NewAtlantisExtractor, JSSTORExtractor]:
        extractor = extractor_class()
        if extractor.supports_url(url):
            return extractor
    return LLMExtractor()  # Fallback
```

## Related Resources

### llm Utility Documentation
- **Main Documentation**: https://llm.datasette.io/
- **Setup Guide**: https://llm.datasette.io/en/stable/setup.html
- **Python API Reference**: https://llm.datasette.io/en/stable/python-api.html
- **CLI Reference**: https://llm.datasette.io/en/stable/help.html
- **Plugin Directory**: https://llm.datasette.io/en/stable/plugins/directory.html
- **GitHub Repository**: https://github.com/simonw/llm

### Simon Willison's Articles
- **Using LLMs for Code**: https://simonwillison.net/2025/Mar/11/using-llms-for-code/
- **LLM Tools Feature**: https://simonwillison.net/2025/May/27/llm-tools/
- **All LLM Posts**: https://simonwillison.net/tags/llm/

### Tutorials
- **Quick Guide by Daniel Kossmann**: https://www.danielkossmann.com/quick-guide-using-llm-cli-utility-python-library-simon-willison/
- **LLMs on Command Line (Parlance Labs)**: https://parlance-labs.com/education/applications/simon_llm_cli/

## Implementation Checklist

### Code Changes
- [ ] Add imports: `abc`, `typing`, `pydantic`, `llm`
- [ ] Create `MetadataExtractor` abstract base class
- [ ] Create `ArticleMetadata` Pydantic schema
- [ ] Implement `NewAtlantisExtractor` (migrate existing logic)
- [ ] Implement `LLMExtractor` with structured output
- [ ] Create `get_extractor_for_url()` factory function
- [ ] Refactor `main()` to use extractor pattern
- [ ] Add `--model` CLI argument
- [ ] Handle llm import errors gracefully

### Testing
- [ ] Migrate existing tests to `TestNewAtlantisExtractor`
- [ ] Create `TestLLMExtractor` with mocked llm calls
- [ ] Create `TestSiteDetection` for router logic
- [ ] Add integration tests for both extractor types
- [ ] Test error conditions (missing llm, bad API keys)
- [ ] Verify all 438 lines of existing tests pass
- [ ] Add tests for new CLI arguments

### Documentation
- [ ] Update README features section
- [ ] Add llm installation instructions
- [ ] Document multi-site usage examples
- [ ] Explain architecture in Technical Details
- [ ] Add troubleshooting for LLM issues
- [ ] Update requirements.txt with llm and pydantic

### Quality Assurance
- [ ] Run `ruff check .` and fix all issues
- [ ] Run `ruff format .` for consistent style
- [ ] Run `python -m pytest` - all tests pass
- [ ] Run `python -m pytest -v` - verbose verification
- [ ] Manual testing with The New Atlantis URLs
- [ ] Manual testing with generic site URLs
- [ ] Verify YAML output format unchanged

## Open Questions

1. **Cost management**: Should there be token usage tracking/logging for LLM calls?
2. **Caching**: Should LLM responses be cached to avoid duplicate API calls?
3. **Rate limiting**: Should there be built-in rate limiting for batch processing?
4. **Local models**: Should we recommend/document local model usage (llm-ollama)?
5. **Timeout handling**: What timeout should be used for LLM API calls?
6. **Fallback chain**: If LLM extraction fails, should there be a basic HTML fallback?
7. **User feedback**: Should the CLI indicate which extractor is being used?
8. **Validation**: Should extracted metadata be validated before output?