# Traductor ADK (EN→ES)

Herramienta CLI para traducir documentación Markdown del inglés al español usando **Google ADK** (Agent Development Kit).

## ✨ Características

- ✅ Traduce texto normal del Markdown a español
- ✅ **Preserva bloques de código** (no traduce el código)
- ✅ **Preserva inline code** (`` `...` ``) y URLs
- ✅ Opcionalmente traduce **solo comentarios** dentro de code fences
- ✅ Procesamiento **paralelo** para múltiples archivos
- ✅ Replica estructura de directorios en output

## 🚀 Quick Start

### 1. Instalación (con uv)

```powershell
# Clonar o navegar al directorio
cd traductor

# uv maneja Python + deps automáticamente
uv sync
```

### 2. Configurar API Key

```powershell
# Opción 1: Variable de entorno (recomendado)
$env:GOOGLE_API_KEY="tu_clave_de_gemini"

# Opción 2: Archivo .env
copy .env.example .env
# Edita .env y agrega tu clave
```

Obtén tu API key en: [Google AI Studio - API Keys](https://aistudio.google.com/app/apikey)

### 3. Uso Básico

```powershell
# Traducir un archivo
uv run translate.py file --in examples/sample.md --out output/sample_es.md

# Traducir con comentarios de código
uv run translate.py file `
  --in examples/sample.md `
  --out output/sample_es.md `
  --translate-code-comments

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
- `--translate-code-comments`: Traduce comentarios dentro de code fences
- `--overwrite`: Sobrescribe archivo de salida si existe

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
- `--translate-code-comments`: Traduce comentarios en código
- `--fail-fast`: Detiene ejecución al primer error
- `--overwrite`: Sobrescribe archivos existentes

## 🔬 Tests

```powershell
# Tests unitarios (no requiere API key)
uv run tests/test_basic.py

# Test de integración (requiere GOOGLE_API_KEY)
$env:GOOGLE_API_KEY="tu_clave"
uv run tests/test_integration.py
```

## 🛡️ Garantías de Preservación

El traductor implementa los siguientes **invariantes**:

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
