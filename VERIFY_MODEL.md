# 🔍 Cómo Verificar que el Modelo se Descargó Correctamente

## Método 1: Botón de Verificación (Más Fácil) ⭐

**EN LA APP**:

1. Abre la app en Streamlit Cloud
2. Ve al **sidebar** (barra lateral izquierda)
3. Scroll hasta abajo, sección **"🔧 Model Status"**
4. Click en **"✅ Test Model Download"**

### Qué Esperar:

**✅ SI FUNCIONA**:
```
✅ Model loaded successfully!
📦 Model: facebook/wav2vec2-base-960h
💻 Device: cpu
Parameters: 95,000,000
```

**❌ SI FALLA**:
```
❌ Model download failed!
Error: [mensaje de error]
💡 Try:
1. Clear cache (button below)
2. Use 'Wav2Vec2 Base' model
3. Check your internet connection
```

---

## Método 2: Probar con Audio Real

**PASOS**:

1. Graba un audio de prueba (di "Hello world")
2. Click **"🚀 Analyze Pronunciation"**

### Qué Esperar:

**✅ SI EL MODELO SE DESCARGÓ**:

Verás estas notificaciones:
1. `📥 Downloading model...` (primera vez, 30-60 segundos)
2. `Loading processor...` (toast notification)
3. `Loading model weights...` (toast notification)
4. `✅ Model ready` (toast notification)
5. `Transcribing audio...`
6. `Generating reference phonemes...`
7. `Aligning sequences...`
8. Resultados mostrados ✅

**❌ SI FALLA**:

Verás:
```
❌ Failed to load model facebook/wav2vec2-base-960h
Error: [descripción del error]
```

Con una de estas causas:
- **🗄️ Disk Space Issue** → Espacio insuficiente
- **🌐 Network Issue** → Problema de conexión
- **❓ Unknown Issue** → Otro problema

---

## Método 3: Ver los Logs (Para Debugging)

**EN STREAMLIT CLOUD**:

1. Click **"Manage app"** (abajo a la derecha)
2. Click **"Logs"**
3. Busca estas líneas:

### Logs Buenos ✅:

```
📥 Downloading model: facebook/wav2vec2-base-960h...
Loading processor...
Loading model weights...
✅ Model ready: facebook/wav2vec2-base-960h
```

### Logs Malos ❌:

```
OSError: Disk quota exceeded
Failed to download model
Connection timeout
```

---

## Método 4: Verificar Caché (Local)

**SI ESTÁS EJECUTANDO LOCALMENTE**:

El modelo se descarga a:
```
# Windows
C:\Users\[tu-usuario]\.cache\huggingface\hub\

# Linux/Mac
~/.cache/huggingface/hub/
```

Verifica que existe la carpeta:
```
models--facebook--wav2vec2-base-960h
```

Tamaño aproximado:
- **Base**: ~360MB
- **Large**: ~2GB

---

## Señales de que TODO está OK ✅

1. **En el sidebar**:
   - ✅ Test Model Download → Success
   - Model: Wav2Vec2 Base (Fast, Cloud-Friendly)

2. **Al grabar y analizar**:
   - Sin errores OSError
   - Muestra resultados en ~5-15 segundos
   - Tabs de resultados aparecen

3. **En los logs**:
   - No hay líneas con "Failed" o "Error"
   - Aparece "Model ready"

---

## Señales de PROBLEMA ❌

### 1. Error de Espacio en Disco

**Síntomas**:
```
OSError: Disk quota exceeded
No space left on device
```

**Solución**:
1. Click **"🗑️ Clear Model Cache"** en sidebar
2. Refresh la página
3. Asegúrate que estás usando modelo **Base**

### 2. Error de Red

**Síntomas**:
```
Connection timeout
Failed to fetch
Network error
```

**Solución**:
1. Verifica tu conexión a internet
2. Espera unos minutos
3. Intenta de nuevo

### 3. Modelo Incorrecto Cacheado

**Síntomas**:
- Usa modelo Base pero sigue fallando
- Logs muestran modelo Large

**Solución**:
1. **"🗑️ Clear Model Cache"** en sidebar
2. Refresh la página
3. Verifica en Advanced Settings que dice "Base"

---

## Timeline Normal de Descarga

### Primera Vez (Sin Caché):
```
0s    → Click "Analyze"
5s    → "Downloading model..."
30s   → "Loading processor..."
45s   → "Loading model weights..."
60s   → "Model ready"
65s   → "Transcribing audio..."
70s   → Resultados mostrados
```

### Segunda Vez en Adelante (Con Caché):
```
0s    → Click "Analyze"
1s    → "Loading model..." (desde caché)
2s    → "Transcribing audio..."
7s    → Resultados mostrados
```

---

## FAQs

### ¿Cuánto tarda la primera descarga?

- **Modelo Base**: 30-60 segundos
- **Modelo Large**: 2-5 minutos (no recomendado en Cloud free)

### ¿Se descarga cada vez?

**NO**. El modelo se cachea:
- **Primera vez**: Descarga desde HuggingFace
- **Siguientes**: Usa caché (instantáneo)

**Excepto**:
- Si limpias el caché
- Si cambias de modelo
- Si Streamlit Cloud reinicia la app

### ¿Cómo sé si está usando caché?

Si carga en **menos de 5 segundos**, está usando caché ✅

Si tarda **30+ segundos**, está descargando 📥

### ¿El caché persiste entre sesiones?

**En Streamlit Cloud**: Sí, mientras no:
- Limpies el caché manualmente
- La app se reinicie (puede pasar)
- Se actualice el código

**Local**: Sí, permanentemente hasta que lo borres

---

## Comandos de Verificación (Local)

```bash
# Ver si el modelo existe
ls ~/.cache/huggingface/hub/ | grep wav2vec2

# Ver tamaño del caché
du -sh ~/.cache/huggingface/

# Limpiar caché local
rm -rf ~/.cache/huggingface/hub/models--facebook--wav2vec2-*
```

---

## Resumen Visual

```
🎙️ App Cargada
     ↓
📊 Sidebar → "✅ Test Model Download"
     ↓
📥 "Downloading model..." (30-60s primera vez)
     ↓
✅ "Model ready: facebook/wav2vec2-base-960h"
     ↓
🎉 LISTO PARA USAR!
```

Si en cualquier punto sale ❌ en lugar de ✅:
1. Lee el mensaje de error
2. Sigue las sugerencias
3. O consulta [FIX_STREAMLIT_CLOUD.md](FIX_STREAMLIT_CLOUD.md)

---

**¿Todo OK?** Si ves ✅ en "Test Model Download", ¡estás listo! 🚀
