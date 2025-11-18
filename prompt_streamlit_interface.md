# Prompt: Interfaz Streamlit para Detección y Diagnóstico de Errores de Pronunciación

## Contexto del Sistema

Basado en el pipeline implementado en `run_mdd.py`, se requiere crear una interfaz de usuario en Streamlit que permita a usuarios practicar pronunciación en inglés americano mediante grabación de audio y retroalimentación automatizada.

## Arquitectura del Pipeline Actual (run_mdd.py)

### Componentes Principales

1. **Carga y Procesamiento de Audio**
   - Función: `load_audio()` - Soporta librosa y torchaudio
   - Función: `convert_to_wav()` - Conversión automática a WAV 16kHz mono
   - Formato: 16000 Hz, mono, float32

2. **Transcripción Fonética (ASR)**
   - Modelo por defecto: `facebook/wav2vec2-large-960h` (ortográfico)
   - Modelo alternativo: `mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme` (fonético)
   - Función: `transcribe_phonemes_local()`
   - Pipeline:
     - Carga de modelo Wav2Vec2 con AutoProcessor y AutoModelForCTC
     - Inferencia CTC (Connectionist Temporal Classification)
     - Decodificación a texto/fonemas
     - G2P opcional con gruut para conversión grafema-fonema

3. **Generación de Referencia Fonética**
   - Función: `generate_reference_phonemes()`
   - Usa gruut para obtener fonemas de referencia del texto esperado
   - Retorna léxico (palabra, fonemas) y lista de palabras
   - Limpieza de puntuación automática

4. **Tokenización y Alineamiento**
   - Función: `tokenize_phonemes()` - Tokeniza cadenas fonéticas
   - Función: `align_sequences()` - Algoritmo Needleman-Wunsch
   - Función: `align_per_word()` - Alineamiento palabra por palabra
   - Manejo de gaps (_) para desalineamientos

5. **Feedback Especializado (LLM)**
   - Cliente: Groq API con modelo `llama-3.1-8b-instant`
   - System prompt: Coach de acento americano especializado
   - Input: Comparación palabra por palabra (esperado vs. producido)
   - Output estructurado:
     - Overall Impression
     - Specific Feedback
     - Google Pronunciation Respelling Suggestions
     - Additional Tips

### Flujo de Datos

```
Audio Input (cualquier formato)
    ↓
Conversión a WAV 16kHz mono
    ↓
Transcripción ASR (Wav2Vec2) → texto/fonemas grabados
    ↓
Generación de referencia fonética (gruut) → fonemas esperados
    ↓
Tokenización de ambas secuencias
    ↓
Alineamiento global (Needleman-Wunsch)
    ↓
Segmentación por palabra (align_per_word)
    ↓
Comparación palabra por palabra
    ↓
LLM Feedback (Groq) → Retroalimentación personalizada
```

### Configuración y Variables de Entorno

- `HF_API_TOKEN`: Token de Hugging Face para modelos privados (opcional)
- `GROQ_API_KEY`: API key de Groq para feedback LLM
- `DEBUG_TRANSCRIBE`: Flag para modo debug (opcional)

### Parámetros CLI Actuales

```python
--audio, -a: Ruta al archivo de audio (requerido)
--text, -t: Texto de referencia (opcional, puede pedirse interactivamente)
--model, -m: Modelo ASR (default: facebook/wav2vec2-large-960h)
--lang: Código de idioma (default: en-us)
--no-llm: Desactiva feedback LLM
--no-g2p: Desactiva conversión G2P
--force-phoneme-model: Fuerza modelo fonético
--emit-json: Ruta para exportar resultados JSON estructurados
```

## Especificaciones de la Interfaz Streamlit

### Requisitos Funcionales

#### 1. Panel de Configuración (Sidebar)

- **Selector de texto de práctica**
  - Lista predefinida de frases para practicar (mínimo 10 opciones)
  - Opción para texto personalizado (text area)
  - Categorías: palabras difíciles, frases comunes, trabalenguas, etc.

- **Configuración avanzada** (expandible)
  - Selector de modelo ASR (dropdown)
    - facebook/wav2vec2-large-960h (ortográfico - recomendado)
    - mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme (fonético)
  - Toggle G2P (activado por defecto)
  - Toggle feedback LLM (activado por defecto)
  - Selector de idioma (default: en-us)

- **Información del sistema**
  - Estado de conexión API (Groq)
  - Modelo activo
  - Indicador de dispositivo (CPU/CUDA)

#### 2. Panel Principal

**2.1 Sección de Texto de Referencia**
- Display del texto seleccionado (tamaño grande, legible)
- Indicador de longitud/complejidad
- Botón para reproducir audio de referencia (opcional, TTS)

**2.2 Sección de Grabación**
- **Botón de grabación** (Start/Stop)
  - Indicador visual de estado (grabando/detenido)
  - Contador de duración en tiempo real
  - Límite máximo: 30 segundos
- **Visualización de forma de onda** (real-time durante grabación)
- **Controles de reproducción**
  - Play/Pause del audio grabado
  - Botón de re-grabación
  - Descarga del audio grabado

**2.3 Panel de Resultados** (aparece después de análisis)

**Tab 1: Comparación Palabra por Palabra**
- Tabla interactiva con columnas:
  - Palabra
  - Fonemas esperados
  - Fonemas producidos
  - Indicador de coincidencia (✓/✗ o colores)
  - Tooltip con explicación fonética
- Resaltado de palabras con errores
- Filtro para mostrar solo errores

**Tab 2: Feedback del Coach**
- Secciones estructuradas del feedback LLM:
  - Overall Impression (con emoji de rating)
  - Specific Feedback (lista con bullet points)
  - Pronunciation Respelling Suggestions (formato destacado)
  - Additional Tips (lista colapsable)
- Botón para regenerar feedback
- Opción para copiar feedback

**Tab 3: Análisis Técnico**
- Visualización de alineamiento completo
- Secuencia de tokens grabados vs. referencia
- Métricas cuantitativas:
  - % de palabras correctas
  - % de fonemas correctos (PER - Phoneme Error Rate)
  - Errores de sustitución/inserción/eliminación
- Gráfico de distribución de errores

**Tab 4: Historial de Intentos**
- Lista de grabaciones previas en la sesión
- Comparación entre intentos
- Exportación de resultados (JSON/CSV)

### Requisitos No Funcionales

#### Performance
- Tiempo de procesamiento < 10 segundos para audio de 30s
- Feedback en tiempo real para grabación
- Caché de modelos para evitar recargas

#### UX/UI
- Diseño responsive
- Temas claro/oscuro
- Mensajes de error informativos
- Progress bars para operaciones largas
- Tooltips explicativos para usuarios novatos

#### Robustez
- Manejo de errores de micrófono
- Validación de entrada de texto
- Fallback si LLM no está disponible
- Logging de errores del lado cliente

### Estructura de Datos

#### Session State (st.session_state)

```python
{
    'audio_recordings': [],  # Lista de grabaciones (bytes)
    'analysis_results': [],  # Resultados históricos
    'current_text': str,     # Texto actual seleccionado
    'model_loaded': bool,    # Estado de carga del modelo
    'processor': object,     # Processor cacheado
    'model': object,         # Modelo cacheado
    'config': {              # Configuración activa
        'model_name': str,
        'use_g2p': bool,
        'use_llm': bool,
        'lang': str
    }
}
```

#### Resultado de Análisis (estructura)

```python
{
    'timestamp': datetime,
    'audio_data': bytes,
    'reference_text': str,
    'raw_decoded': str,
    'recorded_phoneme_str': str,
    'per_word_comparison': [
        {
            'word': str,
            'ref_phonemes': str,
            'rec_phonemes': str,
            'match': bool
        }
    ],
    'llm_feedback': {
        'overall_impression': str,
        'specific_feedback': list,
        'pronunciation_suggestions': list,
        'additional_tips': list
    },
    'metrics': {
        'word_accuracy': float,
        'phoneme_error_rate': float,
        'substitutions': int,
        'insertions': int,
        'deletions': int
    }
}
```

### Funciones Principales a Implementar

#### 1. Grabación de Audio
```python
def record_audio_streamlit() -> bytes:
    """
    Captura audio desde el micrófono usando st.audio_input()
    o audio_recorder (streamlit-audio-recorder)
    Retorna audio en formato WAV 16kHz mono
    """
```

#### 2. Pipeline de Análisis (adaptado de run_mdd.py)
```python
@st.cache_resource
def load_asr_model(model_name: str, hf_token: str = None):
    """Carga y cachea el modelo ASR"""

def process_audio_pipeline(
    audio_bytes: bytes,
    reference_text: str,
    config: dict
) -> dict:
    """
    Pipeline completo:
    1. Convierte audio_bytes a numpy array
    2. Transcripción ASR
    3. Generación de referencia
    4. Alineamiento
    5. Feedback LLM
    Retorna estructura de resultado completa
    """
```

#### 3. Visualizaciones
```python
def plot_waveform(audio: np.ndarray, sr: int):
    """Plotly/matplotlib waveform"""

def display_comparison_table(per_word_comparison: list):
    """Tabla interactiva con pandas/streamlit"""

def calculate_metrics(per_word_ref: list, per_word_rec: list) -> dict:
    """Calcula métricas de error"""
```

#### 4. LLM Feedback Parsing
```python
def parse_llm_feedback(raw_feedback: str) -> dict:
    """
    Parsea la respuesta del LLM en secciones estructuradas
    Usa regex o LLM con JSON output para estructura
    """
```

### Textos de Práctica Sugeridos

```python
PRACTICE_TEXTS = {
    "Beginner": [
        "The quick brown fox jumps over the lazy dog.",
        "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
        "She sells seashells by the seashore.",
    ],
    "Intermediate": [
        "Peter Piper picked a peck of pickled peppers.",
        "I scream, you scream, we all scream for ice cream.",
        "Six thick thistle sticks. Six thick thistles stick.",
    ],
    "Advanced": [
        "The sixth sick sheikh's sixth sheep's sick.",
        "Pad kid poured curd pulled cod.",
        "Can you can a can as a canner can can a can?",
    ],
    "Common Phrases": [
        "Could you please repeat that?",
        "I would like to make a reservation.",
        "What time does the meeting start?",
    ]
}
```

### Dependencias Adicionales

```python
# requirements.txt additions
streamlit>=1.28.0
streamlit-audio-recorder>=0.0.8  # Para grabación de audio
plotly>=5.17.0  # Visualizaciones interactivas
pandas>=2.0.0  # Tablas de datos
soundfile>=0.12.0  # Audio I/O
# Mantener dependencias existentes de run_mdd.py:
# torch, torchaudio, transformers, librosa, gruut, phonemizer, sequence-align, groq
```

### Layout Propuesto (Wireframe Textual)

```
┌─────────────────────────────────────────────────────────────┐
│ SIDEBAR                     │ MAIN PANEL                    │
│                             │                               │
│ ┌─────────────────────────┐│ ┌───────────────────────────┐ │
│ │ 🎯 Select Practice Text ││ │ 📝 Reference Text         │ │
│ │ [Dropdown categories]   ││ │ "The quick brown fox..."  │ │
│ │ [Dropdown phrases]      ││ └───────────────────────────┘ │
│ │ [Custom text area]      ││                               │
│ └─────────────────────────┘│ ┌───────────────────────────┐ │
│                             │ │ 🎙️ Audio Recorder         │ │
│ ┌─────────────────────────┐│ │ [Record Button - pulsing] │ │
│ │ ⚙️ Advanced Settings    ││ │ [Waveform visualization]  │ │
│ │ [ ] Model: [dropdown]   ││ │ Duration: 00:05 / 00:30   │ │
│ │ [x] Use G2P             ││ │ [Play] [Re-record]        │ │
│ │ [x] LLM Feedback        ││ └───────────────────────────┘ │
│ │ Language: [en-us]       ││                               │
│ └─────────────────────────┘│ [Analyze Pronunciation] 🚀    │
│                             │                               │
│ ┌─────────────────────────┐│ ┌───────────────────────────┐ │
│ │ 📊 System Info          ││ │ 📊 Results (Tabs)         │ │
│ │ ✓ Groq API Connected    ││ │ [Comparison][Feedback]    │ │
│ │ Model: wav2vec2-large   ││ │ [Technical][History]      │ │
│ │ Device: CUDA            ││ │                           │ │
│ └─────────────────────────┘│ │ Word-by-Word Comparison:  │ │
│                             │ │ ┌──────┬──────┬──────┬─┐ │ │
│                             │ │ │Word  │Exp   │Got   │✓│ │ │
│                             │ │ ├──────┼──────┼──────┼─┤ │ │
│                             │ │ │quick │kwɪk  │kwɪk  │✓│ │ │
│                             │ │ │brown │braʊn │bɹaʊn │✗│ │ │
│                             │ │ └──────┴──────┴──────┴─┘ │ │
│                             │ │                           │ │
│                             │ │ 🎓 Coach Feedback:        │ │
│                             │ │ Overall: Good effort! ... │ │
│                             │ └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Implementación por Fases

**Fase 1: MVP (Minimum Viable Product)**
- Grabación de audio básica
- Texto de referencia fijo
- Pipeline de análisis sin LLM
- Tabla de comparación simple

**Fase 2: Core Features**
- Selector de textos predefinidos
- Integración LLM feedback
- Visualización de resultados mejorada
- Métricas básicas

**Fase 3: Polish & Advanced**
- Configuración avanzada completa
- Historial de sesión
- Exportación de resultados
- Visualizaciones interactivas
- TTS para audio de referencia

**Fase 4: Production Ready**
- Manejo robusto de errores
- Testing completo
- Optimización de performance
- Documentación de usuario
- Deploy instructions (Streamlit Cloud)

### Consideraciones de Seguridad

- **API Keys**: Usar st.secrets para GROQ_API_KEY y HF_API_TOKEN
- **Validación de entrada**: Sanitizar texto personalizado
- **Límites**: Rate limiting para llamadas LLM
- **Privacy**: No almacenar grabaciones de audio permanentemente (solo sesión)
- **CORS**: Configuración adecuada para micrófono

### Métricas de Éxito

- Tiempo de respuesta < 10s para análisis completo
- Tasa de error de transcripción < 20% (WER)
- Feedback LLM coherente y útil en > 90% casos
- UX fluida sin crashes en 95% sesiones
- Compatibilidad con Chrome, Firefox, Safari

### Preguntas para Aclarar (opcional)

1. ¿Se requiere autenticación de usuarios o es uso anónimo? NO.
2. ¿Debe soportar múltiples idiomas o solo inglés? Solo Ingles.
3. ¿Se necesita persistencia de datos (DB) o solo sesión temporal? Solo Sesion temporal.
4. ¿Hay restricciones de hosting (local, Streamlit Cloud, custom server)? Local.
5. ¿Se requiere integración con sistemas externos (LMS, etc.)?
No.
---

## Prompt Final para Implementación

**Implementa una aplicación Streamlit que permita a usuarios practicar pronunciación en inglés americano mediante:**

1. **Grabación de audio** desde el navegador (30s máximo)
2. **Selección de texto de referencia** de catálogo predefinido o personalizado
3. **Análisis automatizado** usando el pipeline de `run_mdd.py`:
   - Modelo ASR: facebook/wav2vec2-large-960h
   - Generación de referencia fonética con gruut
   - Alineamiento palabra por palabra (Needleman-Wunsch)
   - Feedback de coach de acento vía Groq LLM (llama-3.1-8b-instant)
4. **Visualización de resultados** en múltiples tabs:
   - Comparación fonética palabra por palabra
   - Feedback estructurado del LLM coach
   - Métricas técnicas y análisis de errores
   - Historial de intentos de la sesión
5. **Configuración avanzada** para selección de modelo, G2P, idioma

**Requisitos técnicos:**
- Reutilizar funciones de `run_mdd.py` (load_audio, transcribe_phonemes_local, generate_reference_phonemes, align_per_word)
- Cachear modelos con @st.cache_resource
- Usar st.audio_input() o streamlit-audio-recorder para captura
- Implementar visualizaciones con Plotly/Matplotlib
- Gestionar API keys con st.secrets
- Diseño responsive con sidebar de configuración
- Manejo robusto de errores y feedback al usuario

**Entregables:**
- Código completo de la aplicación Streamlit (`app.py`)
- Archivo requirements.txt actualizado
- README con instrucciones de setup y uso
- Configuración de ejemplo para secrets.toml

**Prioriza:** UX intuitiva, feedback educativo valioso, tiempo de respuesta < 10s, robustez ante errores.
