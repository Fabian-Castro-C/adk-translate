"""Tests básicos para validar segmentación y protección."""

from adk_traductor.md.segmenter import split_markdown, join_segments
from adk_traductor.md.protect import protect_markdown_inline, unprotect


def test_segmenter_preserves_structure():
    md = """# Title

Some text with `inline code` here.

```python
def foo():
    pass
```

More text.
"""
    segments = split_markdown(md)
    reconstructed = join_segments(segments)
    assert reconstructed == md, "Segmentation should preserve exact structure"


def test_protect_inline_code():
    text = "Use `pip install google-adk` to install."
    protected = protect_markdown_inline(text)
    
    # Should have placeholder
    assert "<<ADK_P" in protected.text
    assert "`pip install google-adk`" not in protected.text
    
    # Should restore perfectly
    restored = unprotect(protected.text, protected.mapping)
    assert restored == text


def test_protect_urls():
    text = "Visit https://example.com or [link](https://google.com) for info."
    protected = protect_markdown_inline(text)
    
    # URLs should be protected
    assert "https://example.com" not in protected.text
    assert "https://google.com" not in protected.text
    
    # Should restore
    restored = unprotect(protected.text, protected.mapping)
    assert restored == text


if __name__ == "__main__":
    test_segmenter_preserves_structure()
    print("✓ test_segmenter_preserves_structure")
    
    test_protect_inline_code()
    print("✓ test_protect_inline_code")
    
    test_protect_urls()
    print("✓ test_protect_urls")
    
    print("\nAll tests passed!")
