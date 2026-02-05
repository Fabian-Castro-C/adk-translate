# Traductor ADK (EN→ES)

Herramienta CLI para traducir documentación Markdown del inglés al español usando **Google ADK** (Agent Development Kit) con soporte multi-provider.

## ✨ Características

- ✅ Traduce documentación Markdown del inglés al español
- ✅ **Preserva código** (variables, funciones, imports, paths)
- ✅ **Traduce comentarios** dentro del código (#, //, /* */)
- ✅ **Preserva inline code** (`` `...` ``), URLs, HTML, YAML
- ✅ Procesamiento **paralelo** para múltiples archivos
- ✅ **Multi-provider**: Gemini, OpenAI, Anthropic, GitHub Models, Copilot SDK
- ✅ **Simple**: El LLM maneja todo automáticamente

## 🚀 Quick Start

### 1. Instalación (con uv)

```powershell
# Clonar o navegar al directorio
cd traductor

# uv maneja Python + deps automáticamente
uv sync

# Para soporte de providers externos (OpenAI, Anthropic, etc.)
uv sync --extra litellm
```

### 2. Configurar API Key

**Opción A: Usar Gemini (default)**

```powershell
# Variable de entorno
$env:GOOGLE_API_KEY="tu_clave_de_gemini"

# O usar .env
copy .env.example .env
# Edita .env y agrega: GOOGLE_API_KEY=...
```

Obtén tu API key en: [Google AI Studio - API Keys](https://aistudio.google.com/app/apikey)

**Opción B: Usar OpenAI**

```powershell
$env:OPENAI_API_KEY="sk-..."
```

**Opción C: Usar Anthropic**

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

**Opción D: Usar GitHub Models** (requiere GitHub Copilot)

```powershell
$env:GITHUB_TOKEN="ghp_..."
```

**Opción E: Usar GitHub Copilot SDK** (no requiere API keys, usa tu sesión de Copilot)

```powershell
# Requisito: tener GitHub Copilot CLI instalado y 'copilot' en PATH
# No necesita API keys adicionales - usa tu sesión activa de Copilot
```

### 3. Uso Básico

```powershell
# Traducir con Gemini (default) - comentarios incluidos automáticamente
uv run translate.py file --in examples/sample.md --out output/sample_es.md

# Traducir con OpenAI GPT-4
uv run translate.py file `
  --in examples/sample.md `
  --out output/sample_es.md `
  --provider openai `
  --model gpt-4o

# Traducir con Anthropic Claude
uv run translate.py file `
  --in examples/sample.md `
  --out output/sample_es.md `
  --provider anthropic `
  --model claude-sonnet-4-20250514

# Traducir con GitHub Copilot SDK (usa tu sesión de Copilot, sin API keys)
uv run translate.py file `
  --in examples/sample.md `
  --out output/sample_es.md `
  --provider copilot-sdk `
  --model gpt-4.1

# Batch paralelo (múltiples archivos)
uv run translate.py batch `
  --paths examples/sample.md examples/another.md `
  --root examples `
  --out-dir output `
  --jobs 4
```

## 📖 Comandos CLI

### `file` - Traducir un archivo

```powershell
uv run translate.py file --in INPUT.md --out OUTPUT.md [OPTIONS]
```

**Opciones**:
- `--overwrite`: Sobrescribe archivo de salida si existe
- `--provider {gemini,openai,anthropic,github,copilot-sdk}`: Provider del LLM (default: gemini)
- `--model MODEL_NAME`: Modelo específico (default: gemini-2.5-flash)

**Nota**: Los comentarios en código se traducen automáticamente. El LLM maneja la preservación de código y traducción de comentarios de forma inteligente.

### `batch` - Traducir múltiples archivos

```powershell
uv run translate.py batch `
  --paths FILE1.md FILE2.md ... `
  --root ROOT_DIR `
  --out-dir OUTPUT_DIR `
  [OPTIONS]
```

**Opciones**:
- `--jobs N`: Número de archivos a procesar en paralelo (default: 4)
- `--fail-fast`: Detiene ejecución al primer error
- `--overwrite`: Sobrescribe archivos existentes
- `--provider {gemini,openai,anthropic,github,copilot-sdk}`: Provider del LLM
- `--model MODEL_NAME`: Modelo específico

## 🌐 Providers Soportados

| Provider | Modelos Ejemplo | API Key Required | Install Extra | Notas |
|----------|-----------------|------------------|---------------|-------|
| **Gemini** (default) | `gemini-2.5-flash`, `gemini-2.5-pro` | `GOOGLE_API_KEY` | ❌ | Default, más rápido |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini` | `OPENAI_API_KEY` | ✅ `litellm` | Vía LiteLLM |
| **Anthropic** | `claude-sonnet-4-20250514`, `claude-opus-4-20250514` | `ANTHROPIC_API_KEY` | ✅ `litellm` | Vía LiteLLM |
| **GitHub Models** | `gpt-4o`, `claude-3-opus` | `GITHUB_TOKEN` | ✅ `litellm` | Vía LiteLLM |
| **Copilot SDK** | `gpt-4.1`, `gpt-4o` | ❌ (usa tu sesión) | ✅ `copilot` | Requiere Copilot CLI |

**Instalación de extras**:
```powershell
# Para OpenAI, Anthropic, GitHub Models
uv sync --extra litellm

# Para Copilot SDK
uv sync --extra copilot

# Para todos los providers
uv sync --extra all
```

**Nota sobre Copilot SDK**: 
- Requiere tener instalado y configurado el [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
- El comando `copilot` debe estar disponible en tu PATH
- No consume tu cuota de API keys de Google/OpenAI/Anthropic
- Usa tu suscripción existente de GitHub Copilot

## 🔬 Tests

```powershell
# Tests unitarios (no requiere API key)
uv run tests/test_basic.py

# Test de integración (requiere GOOGLE_API_KEY)
$env:GOOGLE_API_KEY="tu_clave"
uv run tests/test_integration.py
```

## 🛡️ Cómo Funciona

El traductor usa **instrucciones precisas al LLM** para manejar todo automáticamente:

**Traduce**:
- ✅ Títulos, párrafos, listas
- ✅ Comentarios en código (`#`, `//`, `/* */`)
- ✅ Texto en general

**Preserva exactamente**:
- ❌ Código Python, JavaScript, Go, etc.
- ❌ Inline code (`` `variable` ``)
- ❌ URLs y links
- ❌ HTML tags
- ❌ Frontmatter YAML
- ❌ Nombres de variables, funciones, imports

## 🛡️ Invariantes del Sistema

El LLM sigue estas reglas estrictas:

1. **Estructura**: Los paths relativos se preservan en output
2. **Code Fences**: Número y lenguaje de fences idéntico (`` ```python `` → `` ```python ``)
3. **Código**: Tokens no-comentario se preservan exactamente

### Qué se preserva

- ✅ Code fences completos (`` ```lang ... ``` ``)
- ✅ Inline code (`` `code` ``)
- ✅ URLs (markdown links, autolinks, bare URLs)
- ✅ Frontmatter YAML (`---`)
- ✅ Estructura Markdown (headers, listas, tablas)

### Qué se traduce

- ✅ Texto normal del Markdown
- ✅ Comentarios en code fences (solo si `--translate-code-comments`)
  - Python: `# ...`
  - JS/TS/Go/Java: `// ...` y `/* ... */`
  - Shell: `# ...`

## 📝 Ejemplo

**Input** (`examples/sample.md`):

```markdown
# Example Document

This is **sample text** with `inline code`.

## Code

```python
# This comment will be translated
def hello():
    return "Hello"
```

Visit https://example.com for more.
```

**Output** (con `--translate-code-comments`):

```markdown
# Documento de Ejemplo

Este es **texto de muestra** con `inline code`.

## Código

```python
# Este comentario será traducido
def hello():
    return "Hello"
```

Visita https://example.com para más información.
```

## ⚙️ Arquitectura

```
adk_traductor/
├── adk_translate.py    # Agente ADK + Runner (traducción vía Gemini)
├── pipeline.py         # Pipeline completo (orquestación)
├── cli.py              # CLI con argparse
└── md/                 # Procesamiento Markdown
    ├── segmenter.py    # Separación texto/código
    ├── protect.py      # Protección inline code/URLs
    └── comments.py     # Extracción/traducción comentarios
```

## 🔧 Troubleshooting

### Error: `GOOGLE_API_KEY` no configurada

```
RuntimeError: Falta GOOGLE_API_KEY en el entorno
```

**Solución**: Exporta la variable antes de ejecutar:

```powershell
$env:GOOGLE_API_KEY="tu_clave_aqui"
```

### Error: Output exists

```
FileExistsError: Output exists: output/file.md
```

**Solución**: Usa `--overwrite` para sobrescribir.

### Código alterado después de traducción

**Causa**: El LLM interpretó mal los placeholders o comentarios.

**Solución**:
1. Revisa el archivo de salida
2. Reporta el caso (podemos ajustar heurísticas)
3. Usa `--translate-code-comments=false` para mayor seguridad

## 📚 Documentación Adicional

- [USAGE.md](USAGE.md) - Guía de uso detallada con ejemplos
- [STATUS.md](STATUS.md) - Estado del proyecto y validaciones
- [REQ-001](.sia/requirements/REQ-001/) - Requirement completo

## 🎯 Limitaciones

- **No traduce código**: Solo texto Markdown y comentarios (opcional)
- **Comentarios inline complejos**: Se ignoran para evitar falsos positivos
- **Costo**: Cada archivo = 1+ llamadas a Gemini (según tamaño)
- **Calidad**: Depende del modelo; puede requerir revisión humana

## 📄 Licencia

Ver archivo LICENSE en el repositorio principal.
