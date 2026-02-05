"""Test de integración end-to-end (requiere GOOGLE_API_KEY)."""

import asyncio
import os
from pathlib import Path

from adk_traductor.pipeline import TranslateOptions, translate_markdown


async def test_translate_sample():
    """Test con un archivo de ejemplo pequeño."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Skipping test: GOOGLE_API_KEY no configurada")
        return
    
    sample_md = """# Hello World

This is a **sample document** with some text.

## Code Example

```python
# This comment should be translated
def greet(name: str):
    return f"Hello, {name}!"
```

Visit https://example.com for more info.
"""
    
    options = TranslateOptions(translate_code_comments=True)
    translated = await translate_markdown(sample_md, options=options)
    
    # Validaciones básicas
    assert "# Hello World" not in translated  # título traducido
    assert "def greet(name: str):" in translated  # código preservado
    assert "https://example.com" in translated  # URL preservada
    assert "```python" in translated  # fence preservado
    
    print("✓ test_translate_sample")
    print("\n--- Original ---")
    print(sample_md[:200])
    print("\n--- Traducido ---")
    print(translated[:200])


if __name__ == "__main__":
    asyncio.run(test_translate_sample())
