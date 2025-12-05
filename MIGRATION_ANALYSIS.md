# Análisis de Migración: app.py → streamlit_app.py

## Resumen Ejecutivo

Este documento compara las funcionalidades entre `app.py` (aplicación legacy monolítica de 1,296 líneas) y `accent_coach/presentation/streamlit_app.py` (nueva arquitectura DDD con 986 líneas), identificando qué funcionalidades han sido migradas y cuáles aún faltan.

**Estado Global de Migración:** ~60% completado

---

## 🎯 Tab 1: Pronunciation Practice

### ✅ Funcionalidades Migradas

| Funcionalidad | app.py | streamlit_app.py | Estado |
|---------------|--------|------------------|---------|
| Selección de texto de referencia | ✓ | ✓ | ✅ Migrado |
| Opciones predefinidas de frases | ✓ | ✓ | ✅ Migrado |
| Texto personalizado | ✓ | ✓ | ✅ Migrado |
| Grabación de audio (file upload) | ✓ | ✓ | ✅ Migrado |
| Grabación por micrófono | ✓ | ✓ | ✅ Migrado (con audio-recorder-streamlit) |
| Análisis de pronunciación | ✓ | ✓ | ✅ Migrado |
| Métricas básicas (word/phoneme accuracy) | ✓ | ✓ | ✅ Migrado |
| Comparación palabra por palabra | ✓ | ✓ | ✅ Migrado |
| Feedback de LLM | ✓ | ✓ | ✅ Migrado |
| Configuración avanzada | ✓ | ✓ | ✅ Migrado (parcial) |

### ❌ Funcionalidades NO Migradas

| Funcionalidad | Descripción | Ubicación en app.py | Prioridad |
|---------------|-------------|---------------------|-----------|
| **Selector de categorías** | PracticeTextManager con categorías organizadas | Líneas 858-876 | 🔴 Alta |
| **Guía IPA interactiva** | ResultsVisualizer.render_ipa_guide() con selección de palabras | Líneas 1006-1018 | 🔴 Alta |
| **Modo Drilling** | Selección de palabras específicas para practicar | Líneas 1011-1025 | 🟡 Media |
| **Auto-sugerencia de palabras con errores** | Identificación automática de palabras para re-practicar | Líneas 1153-1161 | 🟡 Media |
| **Reproductor Karaoke** | streamlit_pronunciation_widget con sincronización | Líneas 1030-1056 | 🟢 Baja |
| **Silabificación** | phonemes_to_syllables_with_fallback() | Líneas 1042-1048 | 🟢 Baja |
| **Audio TTS de referencia** | TTSGenerator para escuchar texto de referencia | Líneas 1049-1056 | 🟡 Media |
| **Diagnóstico de audio** | Análisis de sample rate, duración, samples | Líneas 1074-1088 | 🟢 Baja |
| **Historial de sesión con exportación** | Tab "History" con múltiples intentos + Export JSON | Líneas 1237-1258 | 🟡 Media |
| **Gráficos técnicos** | plot_waveform(), plot_error_distribution() | Líneas 1229-1231 | 🟢 Baja |
| **Tab "Technical Analysis"** | Métricas detalladas, waveform, distribución de errores | Líneas 1209-1235 | 🟢 Baja |
| **Cache clearing** | Botón para limpiar cache de análisis | Líneas 957-963 | 🟢 Baja |
| **IPA Breakdown con audio** | Guía educativa con reproductor TTS por palabra | Líneas 382-391 (streamlit_app) vs más completo en app.py | 🟡 Media |

---

## 🗣️ Tab 2: Conversation Tutor

### ✅ Funcionalidades Migradas

| Funcionalidad | app.py | streamlit_app.py | Estado |
|---------------|--------|------------------|---------|
| Selección de modo (Practice/Exam) | ✓ | ✓ | ✅ Migrado |
| Selección de topic | ✓ | ✓ | ✅ Migrado |
| Selección de nivel (A2, B1-B2, C1-C2) | ✓ | ✓ | ✅ Migrado |
| Inicio de sesión | ✓ | ✓ | ✅ Migrado |
| Historial de conversación | ✓ | ✓ | ✅ Migrado |
| Input de texto del usuario | ✓ | ✓ | ✅ Migrado |
| Respuesta del tutor | ✓ | ✓ | ✅ Migrado |
| Correcciones en modo Practice | ✓ | ✓ | ✅ Migrado |
| Cierre de sesión | ✓ | ✓ | ✅ Migrado |

### ❌ Funcionalidades NO Migradas

| Funcionalidad | Descripción | Ubicación en app.py | Prioridad |
|---------------|-------------|---------------------|-----------|
| **Grabación de audio/voz** | st.audio_input() para respuestas habladas | Líneas 312-325 | 🔴 Alta |
| **Transcripción ASR** | process_user_speech() con análisis de audio | Líneas 327-346 | 🔴 Alta |
| **Audio TTS del tutor** | TTSGenerator para respuestas del AI | Líneas 271-277, 387-397 | 🟡 Media |
| **Starter prompts con audio** | ConversationStarters con reproducción | Líneas 271-277 | 🟡 Media |
| **Feedback detallado** | Explanation, improved_version, correction | Líneas 365-376 | 🟡 Media |
| **Estadísticas de sesión** | session.get_session_stats() | Líneas 406-408 | 🟢 Baja |
| **Exportar transcript** | Descarga de conversación completa | Líneas 410-417 | 🟢 Baja |
| **ResultsVisualizer.render_conversation_history()** | Visualización mejorada del historial | Líneas 303-307 | 🟢 Baja |
| **Logging de actividades** | ActivityLogger para progreso | Líneas 356-364 | 🟡 Media |

---

## ✍️ Tab 3: Writing Coach

### ✅ Funcionalidades Migradas

| Funcionalidad | app.py | streamlit_app.py | Estado |
|---------------|--------|------------------|---------|
| Selección de categoría de pregunta | ✓ | ✓ | ✅ Migrado |
| Selección de dificultad | ✓ | ✓ | ✅ Migrado |
| Área de escritura | ✓ | ✓ | ✅ Migrado |
| Contador de palabras | ✓ | ✓ | ✅ Migrado |
| Evaluación de escritura | ✓ | ✓ | ✅ Migrado |
| Métricas (CEFR, Vocabulary Variety) | ✓ | ✓ | ✅ Migrado |
| Versión corregida | ✓ | ✓ | ✅ Migrado |
| Sugerencias de mejora | ✓ | ✓ | ✅ Migrado |
| Expansión de vocabulario | ✓ | ✓ | ✅ Migrado |
| Preguntas de seguimiento | ✓ | ✓ | ✅ Migrado |
| Teacher feedback | ✓ | ✓ | ✅ Migrado |

### ❌ Funcionalidades NO Migradas

| Funcionalidad | Descripción | Ubicación en app.py | Prioridad |
|---------------|-------------|---------------------|-----------|
| **Audio TTS para versión corregida** | Reproducción de la versión pulida | Líneas 594-599 | 🟡 Media |
| **Audio TTS para vocabulario** | Pronunciación de palabras de expansión | Líneas 637-643 | 🟡 Media |
| **Mostrar texto original en tab** | Expander con texto sin corregir | Líneas 608-609 | 🟢 Baja |
| **Tabs organizados** | 4 tabs: Polished/Tips/Questions/Vocabulary | Líneas 579-646 | 🟢 Baja |
| **Métricas de lote (batch)** | Potential XP calculation | Líneas 572-576 | 🟢 Baja |
| **Guardar análisis en Firestore** | save_writing_analysis_to_firestore() | Líneas 649-656 | 🟡 Media |
| **Copy feedback button** | Botón para copiar feedback | No implementado en ninguno | 🟢 Baja |

---

## 💬 Tab 4: Language Assistant

### ✅ Funcionalidades Migradas

| Funcionalidad | app.py | streamlit_app.py | Estado |
|---------------|--------|------------------|---------|
| Historial de chat | ✓ | ✓ | ✅ Migrado |
| Input de pregunta | ✓ | ✓ | ✅ Migrado |
| Respuesta del LLM | ✓ | ✓ | ✅ Migrado |
| Categorización de queries | ✓ | ✓ | ✅ Migrado |
| Contexto conversacional | ✓ | ✓ | ✅ Migrado |
| Limpiar historial | ✓ | ✓ | ✅ Migrado |

### ❌ Funcionalidades NO Migradas

| Funcionalidad | Descripción | Ubicación en app.py | Prioridad |
|---------------|-------------|---------------------|-----------|
| **Guardar queries en Firestore** | auth_manager.save_language_query() | Línea 740 | 🟡 Media |
| **Logging de actividad** | ActivityLogger.log_conversation_activity() | Líneas 743-749 | 🟡 Media |
| **Estado temp_query** | Pre-población desde ejemplos | Líneas 704-710 | 🟢 Baja |
| **Divider entre mensajes** | Separador visual mejorado | Línea 689 | 🟢 Baja |

---

## 🎨 Sidebar & UI Global

### ✅ Funcionalidades Migradas

| Funcionalidad | app.py | streamlit_app.py | Estado |
|---------------|--------|------------------|---------|
| Información de usuario | ✓ | ✓ | ✅ Migrado |
| Daily Goal Progress | ✓ | ✓ | ✅ Migrado |
| Barra de progreso visual | ✓ | ✓ | ✅ Migrado |
| System info (LLM status) | ✓ | ✓ | ✅ Migrado |
| Botón de logout | ✓ | ✓ | ✅ Migrado |

### ❌ Funcionalidades NO Migradas

| Funcionalidad | Descripción | Ubicación en app.py | Prioridad |
|---------------|-------------|---------------------|-----------|
| **Selector de historial** | render_user_info_and_history() | Líneas 853-855 | 🟡 Media |
| **Botón de cache clearing** | Limpiar análisis en memoria | Líneas 957-963 | 🟢 Baja |
| **Advanced Settings en sidebar** | ASR model, G2P, LLM, Audio Enhancement | Líneas 879-927 | 🔴 Alta |

---

## 📊 Infraestructura & Persistencia

### ✅ Componentes Migrados

- ✅ ASRModelManager inicializado correctamente
- ✅ Repositorios in-memory implementados
- ✅ Dependency injection funcionando
- ✅ Separación de capas (domain, infrastructure, presentation)

### ❌ Funcionalidades NO Migradas

| Funcionalidad | Descripción | Prioridad |
|---------------|-------------|-----------|
| **Guardar análisis en Firestore** | save_analysis_to_firestore() | 🔴 Alta |
| **Guardar escritura en Firestore** | save_writing_analysis_to_firestore() | 🟡 Media |
| **Guardar queries de lenguaje** | save_language_query() | 🟡 Media |
| **Logging de actividades** | ActivityLogger completo | 🟡 Media |
| **Exportación de historial** | JSON export de análisis | 🟢 Baja |

---

## 🎯 Prioridades de Migración

### 🔴 Prioridad Alta (Críticas)

1. **Advanced Settings en sidebar** - Configuración de ASR, G2P, LLM, Audio Enhancement
2. **Selector de categorías** - PracticeTextManager para textos organizados
3. **Guía IPA interactiva** - Componente educativo clave
4. **Grabación de audio en Conversation Tutor** - Funcionalidad core
5. **Transcripción ASR en conversaciones** - Análisis de speech
6. **Guardar análisis en Firestore** - Persistencia crítica

### 🟡 Prioridad Media (Importantes)

7. Modo Drilling (selección de palabras específicas)
8. Auto-sugerencia de palabras con errores
9. Audio TTS de referencia
10. Historial de sesión con exportación
11. Feedback detallado en conversaciones
12. Audio TTS del tutor
13. Logging de actividades
14. Guardar escritura/queries en Firestore

### 🟢 Prioridad Baja (Nice-to-have)

15. Reproductor Karaoke
16. Silabificación
17. Diagnóstico de audio
18. Gráficos técnicos (waveform, error distribution)
19. Tab "Technical Analysis"
20. Estadísticas de sesión
21. Exportar transcript
22. Cache clearing
23. Tabs organizados en Writing Coach

---

## 📈 Métricas de Migración

| Categoría | Migradas | Pendientes | % Completado |
|-----------|----------|------------|--------------|
| Pronunciation Practice | 10 | 13 | 43% |
| Conversation Tutor | 9 | 9 | 50% |
| Writing Coach | 11 | 7 | 61% |
| Language Assistant | 6 | 4 | 60% |
| Sidebar & UI | 5 | 3 | 63% |
| Infraestructura | 4 | 5 | 44% |
| **TOTAL** | **45** | **41** | **52%** |

---

## 🚀 Roadmap de Sprints (Planificación Detallada)

### 📋 Sprint 1: Fundamentos Core (Semana 1-2)
**Objetivo:** Migrar funcionalidades críticas de alto ROI

#### 🎯 Tareas Principales

**1. Advanced Settings en Sidebar** (Prioridad: 🔴 Alta | Estimado: 8h)
- [ ] Migrar selector de modelo ASR
  - Ubicación original: `app.py` líneas 879-881
  - Crear componente en `accent_coach/presentation/components/settings.py`
  - Modelos: Wav2Vec2 Base, Large, XLSR Phonetic
- [ ] Checkbox Use G2P (Grapheme-to-Phoneme)
  - Ubicación: `app.py` línea 883
- [ ] Checkbox Enable LLM Feedback
  - Ubicación: `app.py` línea 884
- [ ] Selector de idioma (inicialmente solo 'en-us')
  - Ubicación: `app.py` línea 885
- [ ] Sección Audio Enhancement
  - Enable Audio Enhancement (checkbox)
  - Voice Activity Detection (checkbox condicional)
  - Enable Denoising (checkbox condicional)
  - Ubicación: `app.py` líneas 888-901
- [ ] Integrar con `st.session_state.config`
- [ ] Testing: Verificar que cambios persistan entre tabs

**2. PracticeTextManager - Categorías de Texto** (Prioridad: 🔴 Alta | Estimado: 6h)
- [ ] Migrar `PracticeTextManager` a domain layer
  - Crear: `accent_coach/domain/pronunciation/practice_texts.py`
  - Importar categorías desde `practice_texts.py` (root)
- [ ] Implementar selector de categorías
  - Ubicación original: `app.py` líneas 858-864
  - Categorías: Greetings, Common Phrases, Idioms, etc.
- [ ] Implementar selector de textos por categoría
  - Ubicación: `app.py` líneas 866-869
- [ ] Agregar opción "Use custom text"
  - Ubicación: `app.py` líneas 871-876
- [ ] Integrar en `render_pronunciation_practice_tab()`
- [ ] Testing: Verificar carga de categorías y selección

**3. Guía IPA Interactiva** (Prioridad: 🔴 Alta | Estimado: 10h)
- [ ] Migrar `ResultsVisualizer.render_ipa_guide()`
  - Ubicación original: `app.py` líneas 1006-1018
  - Crear: `accent_coach/presentation/components/ipa_guide.py`
- [ ] Implementar generación de breakdown data
  - Usar `PhonemeProcessor.create_ipa_guide_data()`
  - Ubicación: `app.py` líneas 1001-1005
- [ ] Agregar selector de palabras (multiselect)
  - Retornar `subset_text` con palabras seleccionadas
- [ ] Integrar con drilling mode
  - Detección de modo drilling vs full text
  - Ubicación: `app.py` líneas 1019-1025
- [ ] Agregar símbolos únicos IPA con descripciones
  - Usar `IPADefinitionsManager`
- [ ] Audio TTS por símbolo/palabra
  - Usar `TTSGenerator.generate_audio()`
- [ ] Testing: Selección de palabras + audio playback

**4. Persistencia en Firestore - Análisis** (Prioridad: 🔴 Alta | Estimado: 8h)
- [ ] Crear repositorio Firestore para pronunciación
  - Path: `accent_coach/infrastructure/persistence/firestore_repositories.py`
  - Implementar `FirestorePronunciationRepository`
- [ ] Implementar método `save_analysis()`
  - Campos: user_id, reference_text, result, timestamp
  - Ubicación original: `auth_manager.save_analysis_to_firestore()`
- [ ] Integrar en `render_pronunciation_practice_tab()`
  - Guardar después de análisis exitoso (línea ~280 en streamlit_app.py)
- [ ] Agregar manejo de errores
- [ ] Testing: Verificar guardado en Firestore

**5. Grabación de Audio en Conversation Tutor** (Prioridad: 🔴 Alta | Estimado: 6h)
- [ ] Agregar `st.audio_input()` en tab Conversation
  - Ubicación original: `app.py` líneas 312-325
  - Ubicación destino: `render_conversation_tutor_tab()` línea ~670
- [ ] Mostrar playback de audio capturado
  - Ubicación: `app.py` líneas 318-319
- [ ] Agregar botón "Send & Get Feedback"
  - Ubicación: `app.py` línea 321
- [ ] Implementar validación de audio
  - Verificar tamaño, formato
- [ ] Testing: Captura y reproducción

**6. ASR Conversacional** (Prioridad: 🔴 Alta | Estimado: 12h)
- [ ] Migrar `ConversationTutor.process_user_speech()`
  - Ubicación: `app.py` líneas 327-346
  - Crear en: `accent_coach/domain/conversation/speech_processor.py`
- [ ] Integrar ASR transcription
  - Cargar modelo ASR si no está cargado
  - Transcribir audio a texto
- [ ] Procesar con LLM
  - Enviar transcript + history al LLM
  - Obtener correction, improved_version, follow_up
- [ ] Integrar en `ConversationService`
  - Método: `process_speech_turn()`
- [ ] Guardar turn en repositorio
  - Actualizar `conversation_repo`
- [ ] Testing: Audio → Transcript → Feedback

**Entregables Sprint 1:**
- ✅ Settings sidebar funcional
- ✅ Categorías de texto implementadas
- ✅ Guía IPA interactiva con selector
- ✅ Persistencia básica en Firestore
- ✅ Grabación de audio en conversaciones
- ✅ Pipeline ASR conversacional funcional

**Riesgos Sprint 1:**
- 🚨 Integración de ASR puede requerir refactoring
- 🚨 Firestore puede necesitar configuración adicional
- ⚠️ Audio recorder puede tener problemas de compatibilidad

---

### 📋 Sprint 2: Mejoras de Experiencia (Semana 3-4)
**Objetivo:** Implementar features que mejoran significativamente UX

#### 🎯 Tareas Principales

**1. Auto-sugerencia de Palabras con Errores** (Prioridad: 🟡 Media | Estimado: 6h)
- [ ] Implementar detección de palabras con errores
  - Ubicación: `app.py` líneas 1153-1161
  - Criterios: `match=False` O `phoneme_accuracy < 80%`
- [ ] Guardar en session_state
  - Key: `suggested_drill_words`
- [ ] Mostrar toast notification
  - "⚠️ Se detectaron X palabras para practicar"
- [ ] Auto-seleccionar en IPA Guide
  - Pasar `default_selection` a render_ipa_guide
  - Ubicación: `app.py` línea 1009
- [ ] Limpiar sugerencias al cambiar texto
  - Ubicación: `app.py` líneas 877-878
- [ ] Testing: Análisis → Auto-select errores

**2. Drilling Mode** (Prioridad: 🟡 Media | Estimado: 5h)
- [ ] Implementar lógica de modo drilling
  - Variable: `is_subset_mode`
  - Ubicación: `app.py` líneas 1019-1025
- [ ] Usar `effective_reference_text`
  - Si subset: usar palabras seleccionadas
  - Si no: usar texto completo
- [ ] Mostrar indicador visual
  - "🎯 Modo Drilling Activado: Practicando X palabras"
  - Ubicación: `app.py` línea 1024
- [ ] Ajustar análisis a subset
  - Pasar effective_reference_text a pipeline
  - Ubicación: `app.py` línea 1117
- [ ] Ajustar guardado de historial
  - Usar effective_reference_text
  - Ubicación: `app.py` línea 1126
- [ ] Testing: Seleccionar palabras → Drilling activo

**3. Audio TTS - Referencias y Tutor** (Prioridad: 🟡 Media | Estimado: 10h)
- [ ] Migrar `TTSGenerator` a infrastructure
  - Crear: `accent_coach/infrastructure/audio/tts_service.py`
  - Métodos: `generate_audio(text)`, `generate_from_phonemes()`
- [ ] TTS para texto de referencia (Pronunciation)
  - Agregar botón "🔊 Listen to Reference"
  - Ubicación sugerida: Después de mostrar texto (línea ~193)
  - Generar audio con gTTS
- [ ] TTS para IPA Guide
  - Audio por palabra en breakdown
  - Ubicación: streamlit_app.py líneas 382-385 (ya existe parcial)
- [ ] TTS para vocabulario (Writing Coach)
  - Reproducir expansión de palabras
  - Ubicación original: `app.py` líneas 637-643
- [ ] TTS para Conversation Starter
  - Ubicación: `app.py` líneas 271-277
- [ ] TTS para respuestas del tutor
  - Ubicación: `app.py` líneas 387-397
- [ ] Cachear audio generado
  - Evitar regenerar mismo texto
- [ ] Testing: Audio playback en cada contexto

**4. Feedback Mejorado en Conversaciones** (Prioridad: 🟡 Media | Estimado: 6h)
- [ ] Expandir display de feedback
  - Mostrar: transcript, correction, improved_version, explanation
  - Ubicación: `app.py` líneas 365-376
- [ ] Layout en 2 columnas
  - Col 1: Transcript + Corrections
  - Col 2: Explanation
- [ ] Agregar badges de calidad
  - Verde: Sin errores
  - Amarillo: Errores menores
  - Rojo: Errores mayores
- [ ] Mostrar follow-up con audio
  - Ubicación: `app.py` líneas 380-397
- [ ] Testing: Diferentes escenarios de feedback

**5. Historial Exportable** (Prioridad: 🟡 Media | Estimado: 8h)
- [ ] Crear tab "History" en Pronunciation
  - Ubicación original: `app.py` líneas 1237-1258
- [ ] Mostrar lista de intentos
  - Timestamp, métricas clave, audio
- [ ] Implementar exportación JSON
  - Botón: "💾 Export History as JSON"
  - Incluir: timestamp, reference_text, metrics, comparisons
  - Ubicación: `app.py` líneas 1245-1257
- [ ] Agregar download button
  - Formato: `accent_coach_history_YYYYMMDD_HHMMSS.json`
- [ ] Implementar para Conversation
  - Exportar transcript completo
  - Ubicación: `app.py` líneas 410-417
- [ ] Testing: Exportar y validar JSON

**6. Logging de Actividades** (Prioridad: 🟡 Media | Estimado: 6h)
- [ ] Integrar `ActivityLogger` en todos los tabs
  - Pronunciation: líneas 1139-1148 en app.py
  - Conversation: líneas 356-364 en app.py
  - Writing: Después de evaluación
  - Language: Después de query
- [ ] Implementar logs específicos por tipo
  - `log_pronunciation_activity()`: audio_duration, word_count, errors
  - `log_conversation_activity()`: transcript_length, turn_number, errors
  - `log_writing_activity()`: word_count, CEFR_level
  - `log_query_activity()`: query_length, category
- [ ] Guardar en Firestore
  - Colección: `user_activities`
  - Método: `auth_manager.log_activity()`
- [ ] Actualizar Daily Goal en tiempo real
- [ ] Testing: Verificar logs en Firestore

**Entregables Sprint 2:**
- ✅ Auto-sugerencia funcional
- ✅ Drilling mode implementado
- ✅ TTS integrado en múltiples puntos
- ✅ Feedback conversacional mejorado
- ✅ Exportación de historial
- ✅ Logging completo de actividades

**Riesgos Sprint 2:**
- ⚠️ TTS puede tener problemas de latencia
- ⚠️ Exportación JSON puede ser grande
- ⚠️ Logging excesivo puede afectar performance

---

### 📋 Sprint 3: Componentes Avanzados (Semana 5)
**Objetivo:** Pulir y agregar componentes opcionales

#### 🎯 Tareas Principales

**1. Gráficos Técnicos** (Prioridad: 🟢 Baja | Estimado: 6h)
- [ ] Crear tab "Technical Analysis"
  - Ubicación original: `app.py` líneas 1209-1235
- [ ] Implementar `plot_waveform()`
  - Usar plotly para visualizar forma de onda
  - Input: audio_array, sample_rate
  - Ubicación: `app.py` líneas 1229-1230
- [ ] Implementar `plot_error_distribution()`
  - Gráfico de barras: Substitutions, Insertions, Deletions
  - Ubicación: `app.py` línea 1226
- [ ] Mostrar métricas técnicas detalladas
  - PER, WER, por tipo de error
  - Ubicación: `app.py` líneas 1213-1220
- [ ] Agregar expander con detalles raw
  - Raw decoded text
  - Phoneme string completo
  - Ubicación: `app.py` líneas 1233-1235
- [ ] Testing: Visualización correcta

**2. Reproductor Karaoke** (Prioridad: 🟢 Baja | Estimado: 10h)
- [ ] Migrar `streamlit_pronunciation_widget`
  - Ubicación: `app.py` líneas 1030-1056
  - Componente custom de Streamlit
- [ ] Implementar preparación de datos
  - Usar `PhonemeProcessor.prepare_widget_data()`
  - Ubicación: `app.py` líneas 1038-1041
- [ ] Generar TTS para referencia
  - Audio completo del texto
- [ ] Implementar silabificación
  - Usar `phonemes_to_syllables_with_fallback()`
  - Ubicación: `app.py` líneas 1042-1048
- [ ] Integrar widget
  - Pasar: reference_text, phoneme_text, audio, timings
  - Sincronización palabra por palabra
- [ ] Solo mostrar en modo NO-drilling
  - Ubicación: `app.py` líneas 1027-1029
- [ ] Testing: Reproducción y sincronización

**3. Diagnóstico de Audio** (Prioridad: 🟢 Baja | Estimado: 4h)
- [ ] Agregar expander "Audio Diagnostics"
  - Ubicación: `app.py` líneas 1074-1088
- [ ] Mostrar información técnica
  - Sample rate (Hz)
  - Duration (seconds)
  - Number of samples
  - Audio size (KB)
- [ ] Usar librería soundfile
  - Leer waveform y sample rate
- [ ] Agregar validaciones
  - Mínimo 1 segundo
  - Máximo 30 segundos
  - Sample rate adecuado (16kHz)
- [ ] Testing: Diferentes formatos de audio

**4. Cache Clearing** (Prioridad: 🟢 Baja | Estimado: 2h)
- [ ] Agregar botón en sidebar
  - "🗑️ Clear Cache"
  - Ubicación: `app.py` líneas 957-963
- [ ] Limpiar session_state
  - current_result
  - analysis_history
  - pronunciation_result
  - conversation_history
  - etc.
- [ ] Mostrar confirmación
- [ ] Recargar página
  - `st.rerun()`
- [ ] Testing: Limpieza correcta

**5. Tabs Organizados en Writing Coach** (Prioridad: 🟢 Baja | Estimado: 4h)
- [ ] Reorganizar resultados en 4 tabs
  - Ubicación: `app.py` líneas 579-646
  - Tab 1: "✅ Polished Version"
  - Tab 2: "💡 Improvement Tips"
  - Tab 3: "❓ Follow-up Questions"
  - Tab 4: "📚 Vocabulary Expansion"
- [ ] Tab 1: Versión corregida + TTS
  - Ubicación: `app.py` líneas 586-599
- [ ] Tab 2: Mejoras + texto original
  - Ubicación: `app.py` líneas 601-609
- [ ] Tab 3: Preguntas de seguimiento
  - Ubicación: `app.py` líneas 611-618
- [ ] Tab 4: Vocabulario + audio
  - Ubicación: `app.py` líneas 620-646
- [ ] Testing: Navegación entre tabs

**6. Extras de UI** (Prioridad: 🟢 Baja | Estimado: 4h)
- [ ] Selector de historial en sidebar
  - Ubicación: `app.py` líneas 853-855
  - Dropdown con análisis previos
- [ ] Dividers mejorados en Language Assistant
  - Ubicación: `app.py` línea 689
- [ ] Copy feedback button
  - En pronunciation y conversation feedback
- [ ] Guardar escritura/queries en Firestore
  - `save_writing_analysis_to_firestore()`
  - `save_language_query()`
- [ ] Botón "Save Analysis" en Pronunciation
  - Ubicación: `app.py` líneas 649-656
- [ ] Testing: Pequeñas mejoras de UX

**Entregables Sprint 3:**
- ✅ Gráficos técnicos implementados
- ✅ Karaoke player funcional
- ✅ Diagnóstico de audio
- ✅ Cache clearing
- ✅ Tabs organizados en Writing
- ✅ Mejoras de UI completadas

**Riesgos Sprint 3:**
- ⚠️ Karaoke widget puede requerir debugging
- ⚠️ Gráficos pueden afectar performance
- 🟢 Bajo riesgo general (features opcionales)

---

### 📋 Sprint 4: Testing y Documentación (Semana 6)
**Objetivo:** Asegurar calidad y documentar

#### 🎯 Tareas Principales

**1. Testing Integral** (Estimado: 12h)
- [ ] Unit tests para nuevos servicios
  - PracticeTextManager
  - SpeechProcessor
  - TTSService
  - FirestoreRepositories
- [ ] Integration tests
  - Pipeline completo de pronunciación
  - Pipeline conversacional con ASR
  - Persistencia en Firestore
- [ ] E2E tests con Streamlit
  - Flujo completo por tab
  - Validar exports
- [ ] Testing de audio
  - Diferentes formatos (WAV, MP3, M4A)
  - Diferentes duraciones
  - Edge cases (silencio, ruido)

**2. Refactoring y Optimización** (Estimado: 8h)
- [ ] Code review completo
- [ ] Eliminar código duplicado
- [ ] Optimizar queries a Firestore
- [ ] Cachear operaciones costosas
- [ ] Mejorar manejo de errores

**3. Documentación** (Estimado: 8h)
- [ ] Actualizar README
- [ ] Documentar nuevas features
- [ ] Actualizar guías de usuario
- [ ] Documentar arquitectura actualizada
- [ ] Crear CHANGELOG

**4. Deploy y Validación** (Estimado: 4h)
- [ ] Deploy a Streamlit Cloud
- [ ] Validar en producción
- [ ] Ajustes de performance
- [ ] Feedback de usuarios beta

**Entregables Sprint 4:**
- ✅ Suite completa de tests
- ✅ Código refactorizado y optimizado
- ✅ Documentación actualizada
- ✅ Aplicación en producción

---

## 📊 Resumen de Sprints

| Sprint | Duración | Features | Prioridad | Riesgo |
|--------|----------|----------|-----------|--------|
| Sprint 1 | 2 semanas | 6 features core | 🔴 Alta | 🚨 Alto |
| Sprint 2 | 2 semanas | 6 mejoras UX | 🟡 Media | ⚠️ Medio |
| Sprint 3 | 1 semana | 6 componentes opcionales | 🟢 Baja | 🟢 Bajo |
| Sprint 4 | 1 semana | Testing y docs | - | 🟢 Bajo |
| **TOTAL** | **6 semanas** | **18+ features** | - | - |

---

## 📈 Tracking de Progreso

### Sprint 1 (Actual)
```
Progress: [░░░░░░░░░░] 0/6 completado (0%)

□ Advanced Settings
□ PracticeTextManager
□ IPA Guide interactiva
□ Persistencia Firestore
□ Grabación audio (Conversation)
□ ASR conversacional
```

### Sprint 2
```
Progress: [░░░░░░░░░░] 0/6 completado (0%)

□ Auto-sugerencia
□ Drilling mode
□ Audio TTS
□ Feedback mejorado
□ Historial exportable
□ Logging actividades
```

### Sprint 3
```
Progress: [░░░░░░░░░░] 0/6 completado (0%)

□ Gráficos técnicos
□ Karaoke player
□ Diagnóstico audio
□ Cache clearing
□ Tabs Writing Coach
□ Extras UI
```

---

## 🎯 KPIs de Éxito

### Sprint 1
- ✅ 6/6 features críticas implementadas
- ✅ Persistencia funcionando en Firestore
- ✅ ASR conversacional con <5s latencia
- ✅ 0 regresiones en funcionalidad existente

### Sprint 2
- ✅ Auto-sugerencia con >80% precisión
- ✅ TTS generado en <2s
- ✅ Exportación JSON funcional
- ✅ Logs guardándose correctamente

### Sprint 3
- ✅ Todos los componentes opcionales funcionales
- ✅ UI pulida y profesional
- ✅ Documentación actualizada

### Sprint 4
- ✅ >80% code coverage
- ✅ 0 bugs críticos
- ✅ Aplicación en producción estable
- ✅ Feedback positivo de usuarios

---

## 📝 Notas Técnicas

### Diferencias Arquitectónicas

**app.py (Legacy)**
- Arquitectura monolítica (1,296 líneas)
- Managers globales (asr_manager, groq_manager, etc.)
- Lógica mezclada en funciones render
- Dependencias directas a Firebase

**streamlit_app.py (Nueva)**
- Arquitectura DDD por capas (986 líneas)
- Dependency injection
- Separación clara de responsabilidades
- Repositorios abstraídos

### Ventajas de la Nueva Arquitectura

✅ **Más mantenible** - Código más pequeño y organizado
✅ **Más testeable** - Servicios independientes
✅ **Más escalable** - Fácil agregar nuevas features
✅ **Mejor separación** - Domain logic independiente de UI

### Desafíos de Migración

⚠️ **Componentes visuales complejos** - ResultsVisualizer, IPA Guide
⚠️ **Audio processing** - TTSGenerator, audio_recorder integration
⚠️ **Persistencia** - Firestore integration en nueva arquitectura
⚠️ **Estado global** - session_state management

---

## Conclusión

La migración ha avanzado significativamente (**52% completado**) con las funcionalidades core migradas exitosamente. Las principales áreas pendientes son:

1. **Configuración avanzada** (settings sidebar)
2. **Componentes educativos** (IPA guide, drilling mode)
3. **Audio features** (TTS, grabación en conversaciones)
4. **Persistencia** (Firestore integration)

La arquitectura nueva es más limpia y mantenible, pero requiere completar la migración de componentes visuales complejos y la integración completa con Firebase/Firestore.

---

**Documento generado:** 4 de diciembre de 2025
**Autor:** Análisis automatizado comparativo
**Versión:** 1.0
