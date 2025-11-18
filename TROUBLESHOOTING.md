# Troubleshooting Guide

## Problemas Comunes y Soluciones

### 1. Error: KeyError 'match'

**Síntoma**:
```
KeyError: 'match'
```

**Causa**: Error en la función de visualización de tabla.

**Solución**: ✅ **YA CORREGIDO** en las últimas versiones de `app.py` y `app_alternative.py`.

Si aún tienes el error, asegúrate de tener la última versión del código.

---

### 2. Audio con Pitido / Audio Silencioso

**Síntoma**: Al grabar audio, solo se escucha un pitido o silencio.

**Causa**: Problema con `st.audio_input()` en ciertos navegadores o configuraciones de micrófono.

**Soluciones**:

#### Opción A: Usar app_alternative.py (Recomendada)
```bash
streamlit run app_alternative.py
```

Esta versión usa **upload de archivos** en lugar de grabación directa, eliminando todos los problemas de compatibilidad.

**Pasos**:
1. Graba audio con cualquier app:
   - Windows: Voice Recorder (Win + G)
   - Mac: QuickTime / Voice Memos
   - Online: https://online-voice-recorder.com/
2. Sube el archivo WAV/MP3
3. Analiza

#### Opción B: Diagnosticar el problema con app.py
```bash
streamlit run app.py
```

1. Graba tu audio
2. Expande "🔍 Audio Diagnostics"
3. Revisa las amplitudes:
   - Si Min/Max están cerca de 0 → Micrófono no funciona
   - Si son normales pero suena pitido → Problema de codificación

**Pruebas adicionales**:
- Prueba otro navegador (Chrome, Firefox, Edge)
- Verifica permisos del micrófono
- Prueba con otro micrófono
- Revisa configuración de audio del sistema

---

### 3. Error al Cargar Modelos

**Síntoma**:
```
Failed to load model
```

**Soluciones**:

#### Memoria insuficiente:
```python
# En app.py o app_alternative.py, cambia el modelo
"Wav2Vec2 Base": "facebook/wav2vec2-base-960h"  # Modelo más pequeño
```

#### Descarga manual:
```bash
# Instala huggingface-cli
pip install huggingface_hub

# Descarga el modelo
huggingface-cli download facebook/wav2vec2-large-960h
```

---

### 4. Error: Import "soundfile" could not be resolved

**Síntoma**: Warnings de imports no resueltos en el IDE.

**Solución**:
```bash
# Instala todas las dependencias
pip install -r requirements.txt

# Si persiste, instala específicamente
pip install soundfile librosa
```

---

### 5. Error: Groq API Not Available

**Síntoma**: No se genera feedback del coach de IA.

**Soluciones**:

#### Opción A: Configurar API Key
```bash
# Crear .streamlit/secrets.toml
GROQ_API_KEY = "tu-api-key-aqui"
```

Obtener API key gratis en: https://console.groq.com/keys

#### Opción B: Desactivar LLM Feedback
En el sidebar: desactiva "Enable LLM Feedback"

El análisis fonético seguirá funcionando.

---

### 6. Error: CUDA Out of Memory

**Síntoma**:
```
RuntimeError: CUDA out of memory
```

**Soluciones**:

1. **Forzar CPU**:
```python
# En app.py línea ~165, cambia:
device = "cpu"  # Forzar CPU en lugar de CUDA
```

2. **Cerrar otras aplicaciones** que usen GPU

3. **Usar modelo más pequeño** (ver sección 3)

---

### 7. Audio no se reproduce después de grabar

**Síntoma**: El reproductor muestra el audio pero no suena nada.

**Causa**: Formato de audio incompatible o corrupción.

**Solución**: Usa `app_alternative.py` con archivos pre-grabados.

---

### 8. Error: gruut G2P failed

**Síntoma**:
```
G2P conversion failed: ...
```

**Causa**: gruut no puede procesar ciertas palabras.

**Solución**:
- Esto es normal y no crítico
- El sistema usa el texto original como fallback
- O desactiva G2P en Advanced Settings

---

### 9. Procesamiento Muy Lento

**Síntomas**: El análisis toma más de 30 segundos.

**Soluciones**:

1. **Primera ejecución**: Los modelos se descargan (~2GB), es normal que tarde.

2. **Ejecuciones posteriores**:
   - Verifica si tienes CUDA disponible (más rápido)
   - Usa modelo más pequeño
   - Reduce duración del audio (<10 segundos)

3. **Verificar progreso**:
```bash
# En la terminal verás mensajes de:
# - "Loading model..."
# - "Transcribing audio..."
# - "Getting AI coach feedback..."
```

---

### 10. Error: Failed to load audio with all methods

**Síntoma**: No puede cargar ningún archivo de audio.

**Causa**: Archivo corrupto o formato no soportado.

**Soluciones**:

1. **Convierte a WAV**:
```bash
# Usando ffmpeg
ffmpeg -i tu_audio.mp3 -ar 16000 -ac 1 audio.wav

# O usa un convertidor online
https://online-audio-converter.com/
```

2. **Formatos soportados**:
   - ✅ WAV (más compatible)
   - ✅ MP3
   - ✅ M4A
   - ✅ FLAC
   - ⚠️ OGG (puede fallar)
   - ⚠️ WEBM (puede fallar)

---

## Verificación del Sistema

Ejecuta el script de prueba:

```bash
python test_setup.py
```

Esto verificará:
- ✓ Todas las dependencias instaladas
- ✓ PyTorch y CUDA
- ✓ Transformers
- ✓ Gruut
- ✓ API keys configuradas

---

## Logs y Debug

### Habilitar modo debug:

```bash
# Windows
set DEBUG_TRANSCRIBE=1
streamlit run app.py

# Linux/Mac
export DEBUG_TRANSCRIBE=1
streamlit run app.py
```

Esto mostrará información adicional en la terminal.

---

## Contacto y Ayuda

Si ninguna solución funciona:

1. **Revisa los logs** en la terminal donde ejecutaste `streamlit run`
2. **Copia el error completo** incluyendo el traceback
3. **Especifica**:
   - Sistema operativo
   - Versión de Python (`python --version`)
   - Navegador usado
   - Qué versión de app estás usando (app.py vs app_alternative.py)

---

## Tips de Rendimiento

### Para mejor experiencia:

1. **Usa `app_alternative.py`** - Más confiable
2. **Graba audio corto** - 5-10 segundos es ideal
3. **Formato WAV** - Más compatible que MP3
4. **Chrome o Firefox** - Mejor compatibilidad
5. **CUDA si disponible** - 5-10x más rápido

---

## Quick Fixes

```bash
# Reinstalar dependencias
pip uninstall -y soundfile librosa
pip install soundfile librosa

# Limpiar caché de Streamlit
streamlit cache clear

# Verificar versión de Streamlit
streamlit --version  # Debe ser >= 1.28.0

# Actualizar Streamlit
pip install --upgrade streamlit
```
