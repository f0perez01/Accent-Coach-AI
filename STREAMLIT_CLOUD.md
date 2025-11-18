# Streamlit Cloud Deployment Guide

## Problema Resuelto: OSError en Streamlit Cloud

### El Error

```
OSError: This app has encountered an error...
File "/mount/src/accent-coach-ai/app.py", line 214, in load_asr_model
```

**Causa**: El modelo `facebook/wav2vec2-large-960h` (~2GB) es demasiado grande para el tier gratuito de Streamlit Cloud, que tiene **limitaciones de espacio en disco**.

### ✅ Solución Implementada

He cambiado el modelo por defecto a **`facebook/wav2vec2-base-960h`** que es:
- ✅ **Más pequeño** (~360MB vs ~2GB)
- ✅ **Más rápido** de descargar
- ✅ **Compatible con Streamlit Cloud** gratuito
- ✅ **Buena precisión** (95%+ accuracy en la mayoría de casos)

## Cambios Realizados

### 1. Nuevos Modelos Disponibles

```python
MODEL_OPTIONS = {
    "Wav2Vec2 Base (Fast, Cloud-Friendly)": "facebook/wav2vec2-base-960h",  # DEFAULT
    "Wav2Vec2 Large (Better Accuracy, Needs More RAM)": "facebook/wav2vec2-large-960h",
    "Wav2Vec2 XLSR (Phonetic)": "mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme",
}
```

### 2. Modelo por Defecto

El modelo **Base** se usa por defecto, ideal para:
- Streamlit Cloud (tier gratuito)
- Máquinas con poca RAM
- Testing rápido
- La mayoría de casos de uso

## Configuración en Streamlit Cloud

### Paso 1: Crear `secrets.toml`

En el dashboard de Streamlit Cloud:

1. Ve a **"Manage app"**
2. Selecciona **"Settings"**
3. Abre **"Secrets"**
4. Añade:

```toml
GROQ_API_KEY = "your-groq-api-key-here"
# HF_API_TOKEN = "your-hf-token" # Opcional
```

### Paso 2: Configurar requirements.txt

Asegúrate de que `requirements.txt` tiene versiones específicas para evitar conflictos:

```txt
torch>=2.0.0,<2.2.0
torchaudio
transformers>=4.30.0
streamlit>=1.28.0
```

### Paso 3: Recursos del Sistema

**Tier Gratuito de Streamlit Cloud**:
- CPU: 1 core
- RAM: 1GB
- Storage: Limitado (~5GB temporal)

**Recomendaciones**:
- ✅ Usa `Wav2Vec2 Base` (default)
- ✅ Audio < 10 segundos
- ✅ Desactiva otros servicios pesados durante el uso

## Comparación de Modelos

| Modelo | Tamaño | RAM | Precisión | Cloud Gratuito |
|--------|--------|-----|-----------|----------------|
| **Base** | ~360MB | ~1GB | 95%+ | ✅ SÍ |
| **Large** | ~2GB | ~4GB | 97%+ | ❌ NO |
| **XLSR** | ~1.2GB | ~3GB | 96%+ | ⚠️ Depende |

## Troubleshooting en Cloud

### Error: "Out of disk space"

**Solución**:
1. Usa el modelo Base (ya configurado por defecto)
2. O actualiza a Streamlit Cloud Pro ($20/mes)

### Error: "CUDA out of memory"

**Solución**:
- Streamlit Cloud no tiene GPU
- El código automáticamente usa CPU
- No requiere acción

### Procesamiento Lento

**Normal en tier gratuito**:
- Primera carga: 30-60 segundos (descarga modelo)
- Análisis: 5-15 segundos
- Cacheo funciona después de la primera ejecución

**Para mejorar**:
- Reduce duración del audio
- Usa el modelo Base

### Error: "ModuleNotFoundError"

**Solución**:
```bash
# Verifica que requirements.txt está completo
# Streamlit Cloud instala automáticamente
```

Si persiste, añade al `requirements.txt`:
```txt
phonemizer
python-Levenshtein
```

## Monitoreo

### Ver Logs

En Streamlit Cloud:
1. Click **"Manage app"**
2. Click **"Logs"**
3. Busca errores en tiempo real

### Métricas de Uso

- CPU: Disponible en dashboard
- RAM: Muestra warnings si está alto
- Storage: No visible directamente

## Optimizaciones Adicionales

### 1. Caché Agresivo

```python
@st.cache_resource(ttl=3600)  # Cache por 1 hora
def load_asr_model(model_name: str, hf_token: Optional[str] = None):
    ...
```

### 2. Límite de Duración de Audio

```python
MAX_AUDIO_DURATION = 15  # segundos

if duration > MAX_AUDIO_DURATION:
    st.error(f"Audio too long. Max {MAX_AUDIO_DURATION}s")
```

### 3. Procesamiento por Lotes

Para múltiples usuarios simultáneos, considera:
- API externa (Groq, OpenAI Whisper API)
- Queue system
- Rate limiting

## Alternativas a Streamlit Cloud

Si necesitas el modelo Large:

### 1. Streamlit Cloud Pro
- $20/mes
- 4 cores, 4GB RAM
- Puede manejar modelo Large

### 2. Otros Hosting
- **Railway**: $5/mes, más recursos
- **Render**: Free tier con 512MB RAM
- **Hugging Face Spaces**: Free tier con 16GB RAM
- **Google Colab**: Gratis con GPU

### 3. Self-Hosted
```bash
# En tu servidor
streamlit run app.py --server.port 8501
```

## Testing Local vs Cloud

### Local (Desarrollo)
```bash
# Puedes usar cualquier modelo
streamlit run app.py
```

### Cloud (Producción)
- Usa modelo Base por defecto
- Prueba límites de recursos
- Monitorea logs

## Deployment Checklist

Antes de deploy:

- [ ] `requirements.txt` completo
- [ ] Secrets configurados (GROQ_API_KEY)
- [ ] Modelo Base como default
- [ ] Audio limits configurados
- [ ] Error handling robusto
- [ ] README actualizado
- [ ] `.gitignore` incluye secrets locales

## URL de Tu App

Una vez deployed:
```
https://share.streamlit.io/[username]/accent-coach-ai/main/app.py
```

O app_alternative.py:
```
https://share.streamlit.io/[username]/accent-coach-ai/main/app_alternative.py
```

## Próximos Pasos

1. **Push cambios** a GitHub
2. **Refresh app** en Streamlit Cloud (automático)
3. **Verifica** que el modelo Base se carga correctamente
4. **Prueba** con audio de 5-10 segundos
5. **Monitorea logs** para errores

## Soporte

Si el error persiste:
1. Verifica logs en Streamlit Cloud
2. Confirma que usa modelo Base
3. Prueba con audio más corto (<5s)
4. Considera upgrade a Pro tier

---

**¡Listo!** Tu app ahora debería funcionar en Streamlit Cloud tier gratuito. 🎉
