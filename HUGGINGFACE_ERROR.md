# 🔌 Error: "not a valid model identifier" de Hugging Face

## El Error

```
❌ Failed to load model facebook/wav2vec2-base-960h

Error: facebook/wav2vec2-base-960h is not a local folder and is not a valid model identifier
listed on 'https://huggingface.co/models'
```

## ¿Por Qué Sucede?

Este error indica que **Streamlit Cloud no puede conectarse a Hugging Face** para descargar el modelo.

### Causas Comunes:

1. **🔥 Firewall/Red de Streamlit Cloud**
   - Streamlit Cloud free tier a veces tiene restricciones de red
   - Puede estar bloqueando huggingface.co

2. **📦 Versión incompatible de transformers**
   - Versiones viejas o muy nuevas pueden tener problemas
   - Parámetros de autenticación cambiaron

3. **🌐 Hugging Face temporalmente inaccesible**
   - Outage de HuggingFace
   - Problemas de CDN

4. **💾 Caché corrupto**
   - Intento previo dejó archivos incompletos

## ✅ Soluciones

### Solución 1: Actualizar Dependencias (HECHO)

He actualizado `requirements.txt` con versiones específicas:

```txt
transformers>=4.30.0,<4.42.0
huggingface-hub>=0.16.0
torch>=2.0.0,<2.2.0
numpy<2.0.0
```

**Acción**: Hacer push de estos cambios:
```bash
git add requirements.txt app.py
git commit -m "Fix HuggingFace connection with compatible versions"
git push origin main
```

### Solución 2: Limpiar Caché y Reiniciar

**EN STREAMLIT CLOUD**:

1. Click **"Manage app"** → **"Reboot app"**
2. Espera 2-3 minutos
3. Cuando cargue, ve al sidebar
4. Click **"🗑️ Clear Model Cache"**
5. Intenta de nuevo

### Solución 3: Verificar Status de HuggingFace

Visita: https://status.huggingface.co/

Si hay un outage:
- ⏳ Espera a que se resuelva
- 🔄 Intenta más tarde

### Solución 4: Usar Modelo Pre-descargado (Avanzado)

Si el problema persiste, puedes hospedar el modelo tú mismo:

#### Opción A: Git LFS en tu Repo

```bash
# Descargar modelo localmente
huggingface-cli download facebook/wav2vec2-base-960h

# Subir a tu repo (requiere Git LFS)
git lfs install
git lfs track "models/**"
```

**No recomendado**: El modelo es ~360MB, GitHub tiene límites.

#### Opción B: Usar URL directa

Modificar `load_asr_model()` para intentar URL de respaldo.

### Solución 5: Cambiar de Plataforma 🚀

Si Streamlit Cloud free tier sigue fallando:

#### A. Hugging Face Spaces (RECOMENDADO)

**Ventajas**:
- ✅ Acceso directo a HuggingFace (mismo servidor)
- ✅ 16GB RAM gratis
- ✅ GPU gratuito disponible
- ✅ Sin problemas de conectividad

**Cómo**:

1. Ve a https://huggingface.co/spaces
2. Click "Create new Space"
3. Selecciona "Streamlit"
4. Conecta tu repo de GitHub
5. Deploy

#### B. Railway.app

**Ventajas**:
- ✅ $5 gratis/mes
- ✅ Más recursos que Streamlit free
- ✅ Sin restricciones de red

**Cómo**:

1. Ve a https://railway.app/
2. "New Project" → "Deploy from GitHub"
3. Selecciona tu repo
4. Railway detecta Streamlit automáticamente
5. Deploy

#### C. Render.com

**Ventajas**:
- ✅ Free tier con 512MB RAM
- ✅ Sin restricciones de red

**Cómo**:

1. Ve a https://render.com/
2. "New" → "Web Service"
3. Conecta GitHub
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `streamlit run app.py --server.port $PORT`

#### D. Local (Para desarrollo)

```bash
# En tu máquina
streamlit run app.py
```

Funciona perfecto localmente porque no hay restricciones de red.

## 🔍 Diagnóstico

### Verificar Conectividad HuggingFace

Prueba esto en Python:

```python
from transformers import AutoProcessor

# Intenta conectar
try:
    processor = AutoProcessor.from_pretrained("facebook/wav2vec2-base-960h")
    print("✅ Conexión OK")
except Exception as e:
    print(f"❌ Error: {e}")
```

Si falla local → Problema tuyo
Si falla solo en Cloud → Problema de Streamlit Cloud

### Ver Logs Detallados

**EN STREAMLIT CLOUD → Logs**, busca:

**Problema de Red**:
```
ConnectionError: HTTPSConnectionPool
timeout
Unable to reach huggingface.co
```

**Problema de Versión**:
```
AttributeError: 'AutoProcessor' object has no attribute 'from_pretrained'
ImportError: cannot import name 'AutoProcessor'
```

**Problema de Espacio**:
```
OSError: Disk quota exceeded
No space left on device
```

## 🛠️ Workaround Temporal

Mientras solucionas, puedes:

### 1. Usar OpenAI Whisper API

Cambia el ASR a Whisper API (requiere API key):

```python
import openai

def transcribe_with_whisper(audio_bytes):
    client = openai.OpenAI(api_key="tu-key")
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_bytes
    )
    return response.text
```

**Costo**: ~$0.006 por minuto de audio

### 2. Usar Assembly AI

Otra API de transcripción:

```python
import assemblyai as aai

aai.settings.api_key = "tu-key"
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(audio_url)
```

**Costo**: Tiene free tier

## 📊 Comparación de Opciones

| Plataforma | Setup | Costo | HF Access | RAM | Recomendación |
|------------|-------|-------|-----------|-----|---------------|
| **Streamlit Cloud** | Fácil | Gratis | ⚠️ A veces | 1GB | Si funciona |
| **HF Spaces** | Fácil | Gratis | ✅ Directo | 16GB | ⭐ MEJOR |
| **Railway** | Medio | $5/mes | ✅ | 8GB | Bueno |
| **Render** | Medio | Gratis | ✅ | 512MB | OK |
| **Local** | N/A | Gratis | ✅ | Tu RAM | Desarrollo |

## 🎯 Recomendación Final

### Para TU caso específico:

**OPCIÓN 1: Hugging Face Spaces** ⭐⭐⭐

```bash
# 1. Crear Space en HuggingFace
# 2. Conectar tu repo
# 3. Deploy
```

**Por qué**:
- Mismo servidor que los modelos
- Sin problemas de conectividad
- Más recursos (16GB RAM)
- Gratis

**OPCIÓN 2: Arreglar Streamlit Cloud**

```bash
# 1. Push requirements.txt actualizado
git push

# 2. Reboot app en Streamlit Cloud
# 3. Clear cache
# 4. Esperar que funcione
```

**Por qué**:
- Ya lo tienes configurado
- Puede funcionar después de actualizar
- Gratis

## 🔄 Siguientes Pasos

1. **Inmediato**: Push los cambios de requirements.txt
2. **Esperar 5 min**: Streamlit Cloud rebuild
3. **Probar**: "Test Model Download" button
4. **Si falla**: Migrar a HuggingFace Spaces

## 📞 Ayuda Adicional

Si nada funciona:

1. **Verifica** https://status.huggingface.co/
2. **Prueba local** primero
3. **Migra a HF Spaces** (solución garantizada)
4. **Reporta bug** a Streamlit Cloud support

---

**Resumen**: El problema es conectividad de Streamlit Cloud → HuggingFace. Mejor solución: **Hugging Face Spaces**. 🚀
