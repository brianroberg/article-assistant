#!/usr/bin/env python3
"""
Tests for article content extraction (extract_content).
"""

import pytest
from unittest.mock import Mock, patch

from article_assistant import NewAtlantisExtractor, LLMExtractor, main


class TestNewAtlantisExtractorContent:
    """Test cases for NewAtlantisExtractor.extract_content."""

    def test_extract_content_from_gutenberg_content_div(self):
        """Test extracting content from the real div.gutenberg-content structure."""
        extractor = NewAtlantisExtractor()
        html = """
        <html><body>
            <nav>Navigation links</nav>
            <div class="flex">
              <div class="relative w-full">
                <div class="lg:-mx-8">
                  <div class="gutenberg-content article-entry print:w-full print:inline">
                    <div class="tooltip-container">
                      <div class="tooltip">Subscriber Only Sign in</div>
                    </div>
                    <p class="has-drop-cap">One day, Mrs. Pengelley came to London
                    seeking the assistance of Hercule Poirot.</p>
                    <p class="">After listening to her tale with great interest,
                    Poirot agrees to take up the case.</p>
                    <h2>Section Heading</h2>
                    <p class="">More article content with <em>emphasis</em> and a
                    <a href="https://example.com">link</a>.</p>
                    <div class="lazyblock-epigraph-2nCeXv alignwide wp-block-lazyblock-epigraph">
                      Keep reading our Winter 2026 issue
                    </div>
                    <style>.gutenberg-content .block-tna-editors-note p:last-child::after {}</style>
                  </div>
                </div>
              </div>
            </div>
            <footer>Footer content</footer>
        </body></html>
        """

        result = extractor.extract_content(html, "https://thenewatlantis.com/test")

        assert "Mrs. Pengelley" in result
        assert "Poirot agrees" in result
        assert "Section Heading" in result
        assert "emphasis" in result
        # Should not contain noise
        assert "Navigation links" not in result
        assert "Footer content" not in result
        assert "Subscriber Only" not in result
        assert "Keep reading our Winter 2026" not in result

    def test_extract_content_fallback_to_article_tag(self):
        """Test fallback to <article> when no div.article-content exists."""
        extractor = NewAtlantisExtractor()
        html = """
        <html><body>
            <nav>Nav</nav>
            <article>
                <h1>Article Title</h1>
                <p>Article body paragraph.</p>
            </article>
        </body></html>
        """

        result = extractor.extract_content(html, "https://thenewatlantis.com/test")

        assert "Article Title" in result
        assert "Article body paragraph." in result
        assert "Nav" not in result

    def test_extract_content_includes_images_by_default(self):
        """Test that images are included as Markdown by default."""
        extractor = NewAtlantisExtractor()
        html = """
        <html><body>
            <div class="gutenberg-content article-entry">
                <p>Before image.</p>
                <img src="https://example.com/photo.jpg" alt="A photo">
                <p>After image.</p>
            </div>
        </body></html>
        """

        result = extractor.extract_content(html, "https://thenewatlantis.com/test")

        assert "photo.jpg" in result
        assert "A photo" in result

    def test_extract_content_strips_images_when_disabled(self):
        """Test that images are stripped when include_images=False."""
        extractor = NewAtlantisExtractor()
        html = """
        <html><body>
            <div class="gutenberg-content article-entry">
                <p>Before image.</p>
                <img src="https://example.com/photo.jpg" alt="A photo">
                <p>After image.</p>
            </div>
        </body></html>
        """

        result = extractor.extract_content(
            html, "https://thenewatlantis.com/test", include_images=False
        )

        assert "photo.jpg" not in result
        assert "Before image." in result
        assert "After image." in result

    def test_extract_content_raises_when_no_body_found(self):
        """Test that ValueError is raised when no article body element exists."""
        extractor = NewAtlantisExtractor()
        html = "<html><head><title>Empty</title></head></html>"

        with pytest.raises(ValueError, match="Could not locate article body"):
            extractor.extract_content(html, "https://thenewatlantis.com/test")


class TestLLMExtractorContent:
    """Test cases for LLMExtractor.extract_content."""

    @patch("article_assistant.llm")
    def test_extract_content_uses_markdownify_for_substantial_html(self, mock_llm):
        """Test that markdownify is used when article body is substantial."""
        mock_llm.get_model.return_value = Mock()
        extractor = LLMExtractor()

        # Substantial HTML that markdownify can handle (>200 chars of content)
        paragraphs = "\n".join(
            f"<p>Paragraph {i} with enough text to be substantial content.</p>"
            for i in range(10)
        )
        html = f"""
        <html><body>
            <nav>Skip this</nav>
            <article>
                <h1>Main Article</h1>
                {paragraphs}
            </article>
            <footer>Skip this too</footer>
        </body></html>
        """

        result = extractor.extract_content(html, "https://example.com/article")

        assert "Main Article" in result
        assert "Paragraph" in result
        # LLM should NOT have been called since markdownify result is substantial
        mock_llm.get_model.return_value.prompt.assert_not_called()

    @patch("article_assistant.llm")
    def test_extract_content_falls_back_to_llm_for_thin_content(self, mock_llm):
        """Test that LLM is used when markdownify produces thin results."""
        mock_response = Mock()
        mock_response.text.return_value = "# Article\n\nRich LLM-rendered content."
        mock_model = Mock()
        mock_model.prompt.return_value = mock_response
        mock_llm.get_model.return_value = mock_model

        extractor = LLMExtractor()

        # Thin HTML — markdownify result will be under 200 chars
        html = "<html><body><article><p>Short.</p></article></body></html>"

        result = extractor.extract_content(html, "https://example.com/article")

        assert result == "# Article\n\nRich LLM-rendered content."
        mock_model.prompt.assert_called_once()

    @patch("article_assistant.llm")
    def test_extract_content_returns_thin_markdownify_on_llm_error(self, mock_llm):
        """Test that thin markdownify result is returned if LLM also fails."""
        mock_model = Mock()
        mock_model.prompt.side_effect = Exception("API Error")
        mock_llm.get_model.return_value = mock_model

        extractor = LLMExtractor()

        html = "<html><body><article><p>Short but valid.</p></article></body></html>"

        result = extractor.extract_content(html, "https://example.com/article")

        assert "Short but valid." in result

    @patch("article_assistant.llm")
    def test_extract_content_raises_when_both_fail(self, mock_llm):
        """Test ValueError when no body found and LLM fails."""
        mock_model = Mock()
        mock_model.prompt.side_effect = Exception("API Error")
        mock_llm.get_model.return_value = mock_model

        extractor = LLMExtractor()

        html = "<html><head><title>Empty</title></head></html>"

        with pytest.raises(ValueError, match="Could not extract article content"):
            extractor.extract_content(html, "https://example.com/article")


class TestContentSubcommand:
    """Functional tests for the content subcommand."""

    @patch("article_assistant.requests.get")
    @patch(
        "sys.argv",
        ["script.py", "content", "https://www.thenewatlantis.com/test"],
    )
    def test_content_subcommand_outputs_markdown(self, mock_get, capsys):
        """Test that the content subcommand outputs article body as Markdown."""
        mock_html = """
        <html><body>
            <div class="gutenberg-content article-entry">
                <h2>Introduction</h2>
                <p>This is a test article with enough content to be substantial.
                It needs to be over two hundred characters so the markdownify
                result is considered sufficient and the LLM fallback is not
                triggered during this test.</p>
                <p>Another paragraph for good measure with more text.</p>
            </div>
        </body></html>
        """
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        main()

        captured = capsys.readouterr()
        # Should contain article content as Markdown
        assert "Introduction" in captured.out
        assert "test article" in captured.out
        # Should NOT contain YAML front matter or notes
        assert "---" not in captured.out
        assert "## Notes" not in captured.out
        assert "title:" not in captured.out

    @patch("article_assistant.requests.get")
    @patch(
        "sys.argv",
        [
            "script.py",
            "content",
            "--no-images",
            "https://www.thenewatlantis.com/test",
        ],
    )
    def test_content_subcommand_no_images_flag(self, mock_get, capsys):
        """Test that --no-images strips images from output."""
        mock_html = """
        <html><body>
            <div class="gutenberg-content article-entry">
                <p>Text before image with enough content to be substantial
                for the markdownify check and avoid LLM fallback path.</p>
                <img src="https://example.com/photo.jpg" alt="A photo">
                <p>Text after image with more padding content here.</p>
                <p>Even more text to ensure we pass the two hundred character
                threshold that triggers the direct return path.</p>
            </div>
        </body></html>
        """
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        main()

        captured = capsys.readouterr()
        assert "photo.jpg" not in captured.out
        assert "Text before image" in captured.out
