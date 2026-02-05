# Guía de Uso - Traductor ADK

## Setup Inicial

### 1. Instalar con uv (recomendado)
```powershell
cd traductor
uv sync

# Para OpenAI, Anthropic, GitHub Models
uv sync --extra litellm

# Para Copilot SDK
uv sync --extra copilot
```

### 2. Configurar API key
```powershell
# Para Gemini (default)
$env:GOOGLE_API_KEY="tu_clave_aqui"

# Para OpenAI
$env:OPENAI_API_KEY="sk-..."

# Para Anthropic
$env:ANTHROPIC_API_KEY="sk-ant-..."

# Para GitHub Models
$env:GITHUB_TOKEN="ghp_..."

# Para Copilot SDK: no necesita, usa tu sesión activa
```

## Uso Básico

### Traducir un archivo (comentarios incluidos automáticamente)
```powershell
uv run translate.py file --in examples/sample.md --out output/sample_es.md
```

### Traducir con provider específico
```powershell
uv run translate.py file `
  --in examples/sample.md `
  --out output/sample_es.md `
  --provider openai `
  --model gpt-4o
```

### Batch paralelo (múltiples archivos)
```powershell
uv run translate.py batch `
  --paths "examples/sample.md" "examples/another.md" `
  --root examples `
  --out-dir output `
  --jobs 4
```

### Procesar toda una carpeta
```powershell
# Primero genera la lista de archivos
Get-ChildItem -Path ..\adk-docs\docs\agents -Filter *.md -Recurse | 
  ForEach-Object { $_.FullName } > paths.txt

# Luego traduce
uv run translate.py batch `
  --paths @(Get-Content paths.txt) `
  --root ..\adk-docs\docs `
  --out-dir output `
  --jobs 4
```

## Tests

```powershell
uv run tests/test_basic.py
```

## Troubleshooting

### Error: GOOGLE_API_KEY no configurada
```
RuntimeError: Falta GOOGLE_API_KEY en el entorno
```
**Solución**: Configura la variable de entorno antes de ejecutar.

### Error: Output exists
```
FileExistsError: Output exists: output/sample_es.md
```
**Solución**: Usa `--overwrite` para sobrescribir.

### Traducción incompleta o código alterado
**Causa probable**: El LLM necesita ajuste en las instrucciones.

**Solución**:
1. Revisa el archivo de salida
2. Los comentarios se traducen automáticamente
3. El código se preserva automáticamente
4. Si hay problemas, reporta el caso

## Qué Traduce y Qué Preserva

### ✅ SÍ Traduce
- Títulos y subtítulos
- Párrafos de texto
- Listas y tablas
- **Comentarios dentro del código** (#, //, /* */)

### ❌ NO Traduce (Preserva)
- Código (variables, funciones, imports)
- Inline code (`variable`)
- URLs y links
- HTML tags
- Frontmatter YAML
- **Comentarios inline complejos**: Se ignoran para evitar falsos positivos
- **Costo**: Cada archivo = 1+ llamadas a Gemini (según tamaño/segmentos)
- **Calidad**: Depende del modelo; puede requerir revisión humana
