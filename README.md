# Article Assistant

A Python script to extract metadata from The New Atlantis articles and generate Markdown headers for note-taking.

## Features

- Extracts article metadata including title, author(s), and issue information
- Generates properly formatted YAML front matter for Markdown notes
- Supports both JSON-LD structured data and HTML fallback parsing
- **Automatically infers edition numbers** from season information when explicit numbers aren't available
- Normalizes author names and handles multiple authors
- Command-line interface with customizable creation dates
- Comprehensive error handling and validation

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

## Usage

### Basic Usage

Extract metadata from a New Atlantis article:

```bash
python extract_article_metadata.py "https://www.thenewatlantis.com/publications/the-tyranny-of-now"
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

### Custom Creation Date

Specify a custom creation date:

```bash
python extract_article_metadata.py --creation-date 2024-12-01 "https://www.thenewatlantis.com/publications/article-url"
```

### Help

View all available options:

```bash
python extract_article_metadata.py --help
```

## Output Format

The script generates YAML front matter compatible with common note-taking applications like Obsidian, Zettlr, and other Markdown-based tools:

```yaml
---
title: Article Title
author:
  - Author Name
  - Second Author (if applicable)
format: journal article
creation-date: YYYY-MM-DD
publication: The New Atlantis
periodical-edition: No. XX (Season YYYY)  # When available
---

## Notes
```

## Development

### Running Tests

The project includes comprehensive unit and functional tests:

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_extract_article_metadata.py
python -m pytest tests/test_functional.py
```

### Code Quality

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Check and fix issues
ruff check . --fix
```

### Project Structure

```
article-assistant/
├── extract_article_metadata.py    # Main script
├── tests/                         # Test directory
│   ├── __init__.py               # Test package marker
│   ├── test_extract_article_metadata.py  # Unit tests
│   └── test_functional.py        # Functional tests
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git exclusion rules
├── CLAUDE.md                      # Claude Code development guidelines
├── README.md                      # This file
└── venv/                         # Virtual environment (created during setup)
```

## Technical Details

### Metadata Extraction

The script uses a multi-phase approach to extract metadata:

1. **Primary**: JSON-LD structured data parsing for reliable metadata extraction
2. **Fallback**: HTML parsing when structured data is unavailable or malformed
3. **Edition Inference**: Automatically calculates edition numbers from season/year information when explicit numbers aren't provided

### Supported Metadata Fields

- **Title**: Article headline
- **Author(s)**: Single or multiple authors with whitespace normalization
- **Publication**: Always set to "The New Atlantis"
- **Issue Information**: Issue number and season when available, or automatically inferred from season/year
- **Creation Date**: Current date or user-specified date

### Edition Number Inference

When articles only display season information (e.g., "Winter 2025") without explicit edition numbers, the script automatically calculates the correct edition number using The New Atlantis's quarterly publication schedule:

- **Publication Pattern**: Winter, Spring, Summer, Fall (4 issues per year)
- **Reference Points**: Winter 2025 = No. 79, Summer 2025 = No. 81
- **Calculation**: Supports past and future years with accurate numbering
- **Format Support**: Handles both "Season Year" and "Year Season" formats

### Error Handling

- Network request failures with informative error messages
- Graceful degradation when metadata is missing
- URL validation with warnings for non-New Atlantis URLs
- Proper exit codes for scripting integration

## Dependencies

- **requests**: HTTP library for fetching article content
- **beautifulsoup4**: HTML parsing and DOM navigation
- **pytest**: Testing framework (development)
- **pytest-mock**: Mocking utilities for tests (development)

## Development Notes

This project was developed using [Claude Code](https://claude.ai/code), Anthropic's AI-powered development environment, which assisted with code generation, testing, and documentation.

## License

This project is provided as-is for educational and personal use.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`python -m pytest`)
5. Check code quality (`ruff check . && ruff format .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Future Enhancements

- Support for additional academic journals and publications
- Configuration file for customizable output formats
- Integration with popular note-taking applications
- Batch processing of multiple articles
- Enhanced metadata extraction (DOI, citation information, etc.)

## Troubleshooting

### Common Issues

**Import errors when running the script:**
- Ensure you've activated the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Network timeout errors:**
- Check your internet connection
- Some articles may require authentication or have access restrictions

**Metadata extraction issues:**
- The script prioritizes JSON-LD structured data but falls back to HTML parsing
- Some older articles may have different HTML structures
- Report issues with specific URLs for investigation

### Getting Help

- Check the [Issues](https://github.com/your-username/article-assistant/issues) page for known problems
- Create a new issue with:
  - The article URL you're trying to process
  - The error message or unexpected output
  - Your Python version and operating system