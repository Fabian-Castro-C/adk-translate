# Guía de Uso - Traductor ADK

## Setup Inicial

### 1. Crear entorno virtual
```powershell
cd traductor
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 3. Configurar API key
```powershell
# Copia el ejemplo
copy .env.example .env

# Edita .env y agrega tu GOOGLE_API_KEY
notepad .env
```

O exporta directamente:
```powershell
$env:GOOGLE_API_KEY="tu_clave_aqui"
```

## Uso Básico

### Traducir un archivo
```powershell
python translate.py file --in examples/sample.md --out output/sample_es.md
```

### Traducir con comentarios de código
```powershell
python translate.py file `
  --in examples/sample.md `
  --out output/sample_es.md `
  --translate-code-comments
```

### Batch paralelo (múltiples archivos)
```powershell
python translate.py batch `
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
python translate.py batch `
  --paths @(Get-Content paths.txt) `
  --root ..\adk-docs\docs `
  --out-dir output `
  --jobs 4 `
  --translate-code-comments
```

## Tests

```powershell
python tests/test_basic.py
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
**Causa probable**: El LLM interpretó mal los placeholders o los comentarios.

**Solución**:
1. Revisa el archivo de salida
2. Si el código cambió, reporta el caso (podemos ajustar las heurísticas)
3. Usa `--translate-code-comments=false` para mayor seguridad

## Limitaciones

- **No traduce código**: Solo texto Markdown y comentarios (si se activa `--translate-code-comments`)
- **Comentarios inline complejos**: Se ignoran para evitar falsos positivos
- **Costo**: Cada archivo = 1+ llamadas a Gemini (según tamaño/segmentos)
- **Calidad**: Depende del modelo; puede requerir revisión humana
