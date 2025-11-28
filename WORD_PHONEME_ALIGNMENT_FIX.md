# Word-to-Phoneme Alignment Fix

## 🔍 Problema Detectado

En la imagen del usuario, se observó que la transcripción IPA estaba completamente desalineada con las palabras:

### Ejemplo problemático: "The quick brown fox jumps over the lazy dog"

**Antes del fix:**
```
Word        | IPA mostrado (INCORRECTO)
----------- | -------------------------
The         | ð
quick       | əkwˈɪkbɹˈaʊnfˈɑksd͡ʒˈʌmpsˈoʊv...
brown       | (missing)
fox         | (missing)
jumps       | (missing)
over        | əð
the         | lˈeɪz
lazy        | (desalineado)
dog         | idˈɔg
```

### Causa raíz

El código original en `app.py` línea 527:

```python
phoneme_text = " ".join([phon for _, phon in lexicon])
```

Esto concatenaba **todas** las transcripciones IPA en un solo string sin mantener la correspondencia palabra → fonemas. El widget luego intentaba dividir arbitrariamente este string, causando desalineación total.

## ✅ Solución Implementada

### 1. Nueva función en `app.py`: `prepare_pronunciation_widget_data()`

```python
def prepare_pronunciation_widget_data(reference_text: str, lexicon: List[Tuple[str, str]]) -> Dict:
    """
    Prepare data for pronunciation widget with proper word-to-phoneme alignment.

    Args:
        reference_text: Original text string
        lexicon: List of (word, phonemes) tuples from gruut

    Returns:
        Dict with keys:
        - phoneme_text: Space-separated phonemes for all words
        - word_timings: List of dicts with {word, phonemes} for proper alignment
    """
    word_timings = []
    all_phonemes = []

    for word, phonemes in lexicon:
        # Store word-level mapping for widget
        word_timings.append({
            "word": word,
            "phonemes": phonemes,
            "start": None,
            "end": None
        })

        # Collect all phonemes for backward compatibility
        all_phonemes.append(phonemes)

    return {
        "phoneme_text": " ".join(all_phonemes),
        "word_timings": word_timings
    }
```

### 2. Modificación en `app.py` para usar la nueva función

**Antes:**
```python
lexicon, _ = generate_reference_phonemes(reference_text, st.session_state.config['lang'])
phoneme_text = " ".join([phon for _, phon in lexicon])
tts_audio = TTSGenerator.generate_audio(reference_text)

streamlit_pronunciation_widget(
    reference_text,
    phoneme_text,
    b64_audio,
    syllable_timings=syllable_timings
)
```

**Después:**
```python
lexicon, _ = generate_reference_phonemes(reference_text, st.session_state.config['lang'])
widget_data = prepare_pronunciation_widget_data(reference_text, lexicon)
phoneme_text = widget_data["phoneme_text"]
word_timings = widget_data["word_timings"]
tts_audio = TTSGenerator.generate_audio(reference_text)

streamlit_pronunciation_widget(
    reference_text,
    phoneme_text,
    b64_audio,
    word_timings=word_timings,
    syllable_timings=syllable_timings
)
```

### 3. Mejoras en `st_pronunciation_widget.py`

#### A. Generación de word-phoneme pairs

```python
# Prepare word-to-phoneme mapping for display
word_phoneme_pairs = []
if word_timings:
    for wt in word_timings:
        word_phoneme_pairs.append({
            "word": html.escape(wt.get("word", "")),
            "phonemes": html.escape(wt.get("phonemes", "")),
            "start": wt.get("start"),
            "end": wt.get("end")
        })
```

#### B. Nueva tabla de visualización en HTML

Agregada antes del audio player:

```html
<!-- Word-to-Phoneme Mapping Table -->
<div id="pp-word-phoneme-map" style="margin-top:12px; margin-bottom:12px; max-height:200px; overflow-y:auto;">
  <div style="display:grid; grid-template-columns: minmax(80px, auto) 1fr; gap:4px 8px; font-size:14px; background:#f8f9fb; padding:10px; border-radius:6px; border:1px solid #e3e8ef;">
    <!-- Header -->
    <div style="font-weight:600; color:#4a5568; border-bottom:1px solid #d1d9e4; padding-bottom:4px;">Word</div>
    <div style="font-weight:600; color:#4a5568; border-bottom:1px solid #d1d9e4; padding-bottom:4px;">IPA Phonemes</div>
    <!-- Rows will be inserted by JS -->
  </div>
</div>
```

#### C. Nueva función JavaScript para renderizar la tabla

```javascript
// Render word-to-phoneme mapping table
function renderWordPhonemeMap() {
    const mapContainer = document.getElementById('pp-word-phoneme-map');
    if (!mapContainer) return;

    const grid = mapContainer.querySelector('div');
    if (!grid) return;

    // Clear existing rows (keep headers)
    while (grid.children.length > 2) {
        grid.removeChild(grid.lastChild);
    }

    // Add rows from word_phoneme_pairs
    if (payload.word_phoneme_pairs && payload.word_phoneme_pairs.length) {
        payload.word_phoneme_pairs.forEach((pair, idx) => {
            // Word cell
            const wordCell = document.createElement('div');
            wordCell.style.cssText = 'padding:4px 6px; color:#2d3748; background:#ffffff; border-radius:4px;';
            wordCell.textContent = pair.word;
            grid.appendChild(wordCell);

            // Phonemes cell
            const phonCell = document.createElement('div');
            phonCell.style.cssText = 'padding:4px 6px; color:#9b2c2c; font-family:\'Courier New\', monospace; background:#ffffff; border-radius:4px;';
            phonCell.textContent = '/' + pair.phonemes + '/';
            grid.appendChild(phonCell);
        });
    }
}
```

## 📊 Resultado Esperado

**Después del fix:**
```
Word        | IPA Phonemes
----------- | -------------------------
the         | /ð ə/
quick       | /k w ˈɪ k/
brown       | /b ɹ ˈaʊ n/
fox         | /f ˈɑ k s/
jumps       | /d͡ʒ ˈʌ m p s/
over        | /ˈoʊ v ɚ/
the         | /ð ə/
lazy        | /l ˈeɪ z i/
dog         | /d ˈɔ ɡ/
```

## ✅ Tests Realizados

### Test exitoso con "The quick brown fox jumps over the lazy dog"

Archivo: `test_word_phoneme_simple.py`

```bash
$ python test_word_phoneme_simple.py

======================================================================
Testing Word-to-Phoneme Alignment
======================================================================

Input text: The quick brown fox jumps over the lazy dog.

Lexicon generated by gruut:
----------------------------------------------------------------------
  the          → /ð ə/
  quick        → /k w ˈɪ k/
  brown        → /b ɹ ˈaʊ n/
  fox          → /f ˈɑ k s/
  jumps        → /d͡ʒ ˈʌ m p s/
  over         → /ˈoʊ v ɚ/
  the          → /ð ə/
  lazy         → /l ˈeɪ z i/
  dog          → /d ˈɔ ɡ/

✓ All word-to-phoneme mappings are correct!
✓ Alignment preserved correctly!

======================================================================
SUCCESS: Word-phoneme alignment working correctly!
======================================================================
```

## 📝 Archivos Modificados

1. **app.py**
   - Agregada función: `prepare_pronunciation_widget_data()`
   - Modificado: Llamada a `streamlit_pronunciation_widget()` con `word_timings`

2. **st_pronunciation_widget.py**
   - Agregado: Generación de `word_phoneme_pairs`
   - Agregado: Tabla HTML de visualización
   - Agregado: Función JS `renderWordPhonemeMap()`
   - Modificado: Payload incluye `word_phoneme_pairs`

3. **Archivos de test** (nuevos)
   - `test_word_phoneme_alignment.py`
   - `test_word_phoneme_simple.py`

## 🎯 Beneficios

✅ **Alineación correcta**: Cada palabra se muestra con su transcripción IPA correcta

✅ **Visualización clara**: Nueva tabla muestra explícitamente la correspondencia palabra → fonemas

✅ **Backward compatible**: La función mantiene `phoneme_text` para compatibilidad

✅ **Preparado para timings**: La estructura soporta agregar `start/end` timestamps en el futuro

✅ **Testeable**: Tests automatizados verifican la corrección

## 🔮 Próximos Pasos (Opcional)

### Para mejorar aún más:

1. **Agregar timings reales desde ASR**
   - Usar forced alignment para obtener timestamps precisos
   - Mapear timestamps a nivel de palabra desde el modelo ASR

2. **Mejorar visualización**
   - Agregar highlights en la tabla cuando el audio toca cada palabra
   - Sincronizar tabla con karaoke player

3. **Soporte para errores de pronunciación**
   - Comparar user recording con reference
   - Highlight en rojo palabras con errores en la tabla

## 📌 Notas Técnicas

- La función `prepare_pronunciation_widget_data()` mantiene la correspondencia 1:1 entre palabras y fonemas
- `word_timings` es una lista de dicts con estructura: `{word, phonemes, start, end}`
- Para TTS preview, `start` y `end` son `None` y el widget auto-particiona el audio
- Para ASR analysis, se pueden agregar timestamps reales desde el modelo

## 🔗 Referencias

- Gruut documentation: https://github.com/rhasspy/gruut
- IPA definitions: `ipa_definitions.py`
- Syllabifier improvements: `SYLLABIFIER_IMPROVEMENTS.md`
