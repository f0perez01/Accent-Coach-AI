# Troubleshooting: Word-Phoneme Alignment Table

## Problema Reportado

La tabla de Word → IPA Phonemes en el Pronunciation Trainer aparece vacía.

## Diagnóstico

### Paso 1: Verificar mensajes de debug en Streamlit

Cuando ejecutes la app, deberías ver uno de estos mensajes **encima del widget**:

✅ **Caso correcto:**
```
ℹ️ ✓ Prepared 9 word-phoneme mappings
```

⚠️ **Casos problemáticos:**
```
⚠️ word_timings provided (9 items) but word_phoneme_pairs is empty
```
o
```
⚠️ No word_timings provided to widget
```

### Paso 2: Verificar la consola del navegador

1. Abre las DevTools del navegador (F12)
2. Ve a la pestaña "Console"
3. Busca mensajes que comiencen con "Rendering word-phoneme map"

**Salida esperada:**
```
Rendering word-phoneme map
payload.word_phoneme_pairs: Array(9)
  0: {word: "the", phonemes: "ð ə", start: null, end: null}
  1: {word: "quick", phonemes: "k w ˈɪ k", start: null, end: null}
  ...
Rendering 9 word-phoneme pairs
```

**Problema si ves:**
```
No word_phoneme_pairs available
Using word_timings as fallback
```

## Soluciones por Caso

### Caso A: "Prepared X mappings" pero tabla vacía

**Causa:** JavaScript no está recibiendo los datos correctamente

**Solución:**
1. Verifica en la consola del navegador si `payload.word_phoneme_pairs` está definido
2. Si está vacío, el problema es la serialización JSON en Python
3. Revisa que `_safe_json()` esté funcionando correctamente

### Caso B: "word_timings provided but word_phoneme_pairs is empty"

**Causa:** La lógica de construcción de `word_phoneme_pairs` está fallando

**Solución:**
1. Verifica que `word_timings` tenga la estructura correcta:
   ```python
   [
       {"word": "the", "phonemes": "ð ə", "start": None, "end": None},
       ...
   ]
   ```

2. Ejecuta el test de flujo:
   ```bash
   python test_full_widget_flow.py
   ```

3. Si el test pasa pero la app falla, hay un problema con cómo se pasan los datos desde `app.py`

### Caso C: "No word_timings provided"

**Causa:** `app.py` no está pasando `word_timings` al widget

**Solución:**
1. Verifica en [app.py](app.py:581-587) que se esté llamando:
   ```python
   streamlit_pronunciation_widget(
       reference_text,
       phoneme_text,
       b64_audio,
       word_timings=word_timings,  # ← Debe estar presente
       syllable_timings=syllable_timings
   )
   ```

2. Verifica que `widget_data["word_timings"]` no esté vacío antes de la llamada

## Tests Disponibles

### Test 1: Lógica de alineación
```bash
python test_word_phoneme_simple.py
```
Verifica que la generación de fonemas y alineación funcione correctamente.

### Test 2: Flujo completo
```bash
python test_full_widget_flow.py
```
Simula todo el flujo: app.py → widget.py

### Test 3: Preparación de datos del widget
```bash
python test_widget_data.py
```
Prueba específicamente la construcción de `word_phoneme_pairs`

## Verificación Manual en JavaScript

Abre la consola del navegador y ejecuta:

```javascript
// Ver datos del payload
window._pp_widget
```

Deberías ver el objeto con información del widget.

```javascript
// Ver word_phoneme_pairs específicamente
document.getElementById('pp-word-phoneme-map')
```

Debería mostrar el contenedor de la tabla.

## Código de Fallback

Si `word_phoneme_pairs` está vacío, el código ahora usa `word_timings` como fallback:

```javascript
// Try to use word_timings as fallback
if (payload.word_timings && payload.word_timings.length) {
    console.log('Using word_timings as fallback');
    payload.word_timings.forEach((wt, idx) => {
        const wordCell = document.createElement('div');
        wordCell.textContent = wt.word || wt.text || '?';
        grid.appendChild(wordCell);

        const phonCell = document.createElement('div');
        phonCell.textContent = '/' + (wt.phonemes || wt.ipa || '?') + '/';
        grid.appendChild(phonCell);
    });
}
```

## Solución Temporal

Si nada funciona, puedes usar el código de fallback manualmente. Agrega esto en [app.py](app.py) justo después del widget:

```python
# Temporary: Show word-phoneme mapping in Streamlit
import pandas as pd
if widget_data.get("word_timings"):
    df = pd.DataFrame(widget_data["word_timings"])
    st.dataframe(df[["word", "phonemes"]], use_container_width=True)
```

Esto mostrará los datos en una tabla de Pandas mientras se resuelve el problema del widget.

## Contacto

Si ninguna de estas soluciones funciona:

1. Copia la salida de la consola del navegador
2. Copia los mensajes de debug de Streamlit
3. Ejecuta: `python test_full_widget_flow.py` y copia el resultado
4. Reporta el issue con toda esta información

## Archivos Relevantes

- [app.py](app.py:201-234) - Función `prepare_pronunciation_widget_data()`
- [app.py](app.py:560-587) - Llamada al widget
- [st_pronunciation_widget.py](st_pronunciation_widget.py:74-98) - Construcción de `word_phoneme_pairs`
- [st_pronunciation_widget.py](st_pronunciation_widget.py:277-341) - Función JS `renderWordPhonemeMap()`

## Estado Actual

✅ Tests unitarios: PASANDO
✅ Test de flujo completo: PASANDO
❓ Integración en Streamlit: PENDIENTE VERIFICACIÓN

Ejecuta la app y reporta qué mensaje de debug aparece para continuar el troubleshooting.
