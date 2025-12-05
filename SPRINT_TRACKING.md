# 🏃‍♂️ Sprint Tracking - Accent Coach AI Migration

**Inicio del Proyecto:** 4 de diciembre de 2025  
**Duración Total Estimada:** 6 semanas  
**Estado Actual:** Sprint 1 - Día 1

---

## 🎯 Sprint 1: Fundamentos Core (Semanas 1-2)

**Objetivo:** Migrar funcionalidades críticas de alto ROI  
**Duración:** 2 semanas (10 días laborales)  
**Fecha Inicio:** 4 de diciembre de 2025  
**Fecha Fin Estimada:** 18 de diciembre de 2025

### 📊 Progreso General
```
████░░░░░░ 34% completado (2/6 features casi completas)

Tiempo transcurrido: 0 días / 10 días
Horas estimadas: 50h total
Horas completadas: 11.8h / 50h
  - Feature 1 (Advanced Settings): 6.4h / 8h = 80% ✅
  - Feature 2 (PracticeTextManager): 5.4h / 6h = 90% ✅
```

### ✅ Tareas Completadas
- [x] Documento de análisis de migración creado
- [x] Plan de sprints definido
- [x] Repositorio configurado
- [x] Feature 1: Advanced Settings - Implementación base (80%)
- [x] Feature 2: PracticeTextManager - Implementación y UI (90%)

### 📋 Feature 1: Advanced Settings en Sidebar
**Estimado:** 8 horas | **Progreso:** 80% ⚡

**Checklist:**
- [x] Crear `accent_coach/presentation/components/settings.py`
- [x] Implementar selector de modelo ASR
  - [x] Wav2Vec2 Base (Fast, Cloud-Friendly)
  - [x] Wav2Vec2 Large (Better Accuracy)
  - [x] Wav2Vec2 XLSR (Phonetic)
- [x] Agregar checkbox "Use G2P"
- [x] Agregar checkbox "Enable LLM Feedback"
- [x] Agregar selector de idioma
- [x] Implementar sección "Audio Enhancement"
  - [x] Checkbox principal "Enable Audio Enhancement"
  - [x] Checkbox condicional "Voice Activity Detection"
  - [x] Checkbox condicional "Enable Denoising"
- [x] Integrar con `st.session_state.config`
- [x] Agregar al sidebar en `streamlit_app.py`
- [ ] Testing manual en todos los tabs
- [ ] Verificar persistencia entre navegación

**Referencias:**
- Código original: `app.py` líneas 879-927
- Destino: `accent_coach/presentation/components/settings.py`

**Notas:**
```
✅ Componente creado exitosamente en accent_coach/presentation/components/settings.py
✅ Clase AdvancedSettings implementada con todos los controles
✅ Integrado en sidebar de streamlit_app.py (línea ~905)
✅ Import verificado y funcionando correctamente
✅ Sintaxis validada (py_compile OK)

Mejoras implementadas vs código original:
- Mejor organización en clase reutilizable
- Layout mejorado con columnas para checkboxes
- Mensajes informativos sobre estado de enhancement
- Método _get_default_config() para configuración inicial
- Función de conveniencia render_advanced_settings()
- Help texts más descriptivos
- Índices automáticos para selectbox (preserva selección actual)

Pendiente:
- Testing manual navegando entre tabs
- Verificar que cambios persistan correctamente en session_state
- Verificar que modelo ASR seleccionado se use en análisis
```

---

### 📋 Feature 2: PracticeTextManager - Categorías
**Estimado:** 6 horas | **Progreso:** 90% ⚡

**Checklist:**
- [x] Crear `accent_coach/domain/pronunciation/practice_texts.py`
- [x] Importar categorías desde `practice_texts.py` (root)
- [x] Implementar método `get_categories()`
- [x] Implementar método `get_texts_for_category(category)`
- [x] Implementar métodos adicionales: `search_texts()`, `get_random_text()`, `get_category_info()`
- [x] Crear selector de categorías en UI
- [x] Crear selector de textos por categoría
- [x] Agregar opción "Use custom text"
- [x] Integrar en `render_pronunciation_practice_tab()`
- [x] Reemplazar lista hardcoded de presets
- [x] Agregar métricas de categoría (count, description)
- [x] Agregar tracking de cambios de texto (clear drill words)
- [x] Mostrar metadatos (focus, difficulty)
- [ ] Testing manual con todas las categorías (7 total)

**Referencias:**
- Código original: `app.py` líneas 858-876
- Manager migrado: `accent_coach/domain/pronunciation/practice_texts.py`

**Notas:**
```
✅ PracticeTextManager creado con 270+ líneas
✅ 7 categorías implementadas:
   - Beginner (10 textos)
   - Intermediate (10 textos)
   - Advanced (10 textos)
   - Common Phrases (10 textos)
   - Idioms (10 textos)
   - Business English (10 textos)
   - Tongue Twisters (10 textos)

✅ Total: 70+ practice texts organizados

✅ Métodos implementados:
   - get_categories() -> Lista de categorías
   - get_texts_for_category(cat) -> Lista de PracticeText
   - search_texts(query) -> Búsqueda por contenido
   - get_random_text(cat=None) -> Texto aleatorio
   - get_category_info(cat) -> Metadata (count, description)

✅ UI mejorada en streamlit_app.py:
   - Selector de categoría con columnas (2:1)
   - Métrica de count de textos
   - Caption con descripción de categoría
   - Selector de texto dinámico según categoría
   - Info con focus y difficulty del texto seleccionado
   - Tracking de cambios de texto (clear drill words)

Mejoras vs código original:
   - Organización por nivel de dificultad
   - Categorías especializadas (Business, Idioms, Tongue Twisters)
   - Metadata rica en cada texto (focus, difficulty)
   - Búsqueda y selección aleatoria
   - UI más informativa

Pendiente:
   - Testing manual navegando todas las categorías
   - Verificar que drill words se limpien al cambiar texto
```
[Agregar notas durante desarrollo]
```

---

### 📋 Feature 3: Guía IPA Interactiva
**Estimado:** 10 horas | **Progreso:** 0%

**Checklist:**
- [ ] Crear `accent_coach/presentation/components/ipa_guide.py`
- [ ] Implementar generación de breakdown data
  - [ ] Integrar `PhonemeProcessor.create_ipa_guide_data()`
- [ ] Crear tabla/grid de palabras con IPA
- [ ] Implementar multiselect para drilling
- [ ] Agregar descripción de símbolos únicos
- [ ] Integrar con `IPADefinitionsManager`
- [ ] Implementar audio TTS por palabra
- [ ] Agregar reproductor de audio inline
- [ ] Detectar modo drilling (subset vs full)
- [ ] Retornar `subset_text` correctamente
- [ ] Integrar en pronunciation practice tab
- [ ] Testing: selección múltiple + audio

**Referencias:**
- Código original: `app.py` líneas 1001-1018
- Visualizer: `ResultsVisualizer.render_ipa_guide()`

**Notas:**
```
[Agregar notas durante desarrollo]
```

---

### 📋 Feature 4: Persistencia en Firestore
**Estimado:** 8 horas | **Progreso:** 0%

**Checklist:**
- [ ] Crear `accent_coach/infrastructure/persistence/firestore_repositories.py`
- [ ] Implementar `FirestorePronunciationRepository`
  - [ ] Método `save_analysis(user_id, reference_text, result, timestamp)`
  - [ ] Método `get_user_analyses(user_id, limit=10)`
  - [ ] Método `get_analysis_by_id(analysis_id)`
- [ ] Implementar `FirestoreConversationRepository`
- [ ] Implementar `FirestoreWritingRepository`
- [ ] Integrar en `initialize_services()`
- [ ] Reemplazar InMemory por Firestore repositories
- [ ] Agregar en pronunciation después de análisis
- [ ] Agregar manejo de errores completo
- [ ] Testing con datos reales en Firestore

**Referencias:**
- Código original: `auth_manager.save_analysis_to_firestore()`
- Colección: `user_analyses`

**Notas:**
```
[Agregar notas durante desarrollo]
```

---

### 📋 Feature 5: Grabación de Audio (Conversation Tutor)
**Estimado:** 6 horas | **Progreso:** 0%

**Checklist:**
- [ ] Agregar sección "Your Turn" en conversation tab
- [ ] Implementar `st.audio_input("Record your response")`
- [ ] Mostrar mensaje de confirmación al capturar
- [ ] Agregar playback del audio grabado
- [ ] Implementar botón "Send & Get Feedback"
- [ ] Validar audio capturado
  - [ ] Verificar tamaño mínimo
  - [ ] Verificar formato
- [ ] Deshabilitar botón si no hay audio
- [ ] Agregar spinner durante procesamiento
- [ ] Testing con diferentes dispositivos

**Referencias:**
- Código original: `app.py` líneas 312-325
- Destino: `render_conversation_tutor_tab()` línea ~670

**Notas:**
```
[Agregar notas durante desarrollo]
```

---

### 📋 Feature 6: ASR Conversacional
**Estimado:** 12 horas | **Progreso:** 0%

**Checklist:**
- [ ] Crear `accent_coach/domain/conversation/speech_processor.py`
- [ ] Implementar clase `SpeechProcessor`
- [ ] Método `transcribe_audio(audio_bytes)` → text
  - [ ] Cargar modelo ASR
  - [ ] Procesar audio
  - [ ] Retornar transcript
- [ ] Método `analyze_speech(transcript, history)` → feedback
  - [ ] Integrar con LLM
  - [ ] Detectar errores
  - [ ] Generar correction
  - [ ] Generar improved_version
  - [ ] Generar follow_up_question
- [ ] Integrar en `ConversationService`
  - [ ] Nuevo método: `process_speech_turn()`
- [ ] Implementar en UI
  - [ ] Capturar audio → transcribe → feedback
- [ ] Guardar turn con transcripción
- [ ] Testing completo de pipeline

**Referencias:**
- Código original: `ConversationTutor.process_user_speech()` en `app.py` líneas 327-346
- ASR Manager ya inicializado en `streamlit_app.py`

**Notas:**
```
[Agregar notas durante desarrollo]
```

---

## 📈 Métricas Sprint 1

### Velocity
```
Story Points Planeados: 50
Story Points Completados: 0
Velocity: 0 SP/día
```

### Burndown
```
Día 1:  50 SP restantes █████████████████████
Día 2:  __ SP restantes
Día 3:  __ SP restantes
Día 4:  __ SP restantes
Día 5:  __ SP restantes
Día 6:  __ SP restantes
Día 7:  __ SP restantes
Día 8:  __ SP restantes
Día 9:  __ SP restantes
Día 10: 0 SP restantes  (ideal)
```

### Bloqueadores
```
[Ninguno registrado aún]
```

### Riesgos Identificados
- 🚨 **Alto:** Integración de ASR conversacional puede requerir refactoring significativo
- 🚨 **Alto:** Firestore puede necesitar configuración adicional de permisos
- ⚠️ **Medio:** Audio recorder puede tener problemas de compatibilidad cross-browser
- ⚠️ **Medio:** TTS puede agregar latencia significativa

### Decisiones Técnicas
```
[Documentar decisiones importantes durante el sprint]
```

---

## 🎯 Sprint 2: Mejoras de Experiencia (Semanas 3-4)

**Estado:** Pendiente  
**Inicio Estimado:** 18 de diciembre de 2025  
**Features:** 6 (Auto-sugerencia, Drilling, TTS, Feedback, Historial, Logging)

---

## 🎯 Sprint 3: Componentes Avanzados (Semana 5)

**Estado:** Pendiente  
**Inicio Estimado:** 1 de enero de 2026  
**Features:** 6 (Gráficos, Karaoke, Diagnóstico, Cache, Tabs, UI)

---

## 🎯 Sprint 4: Testing y Documentación (Semana 6)

**Estado:** Pendiente  
**Inicio Estimado:** 8 de enero de 2026  
**Features:** Testing, Refactoring, Docs, Deploy

---

## 📝 Daily Standup Template

### ¿Qué hice ayer?
```
[Completar diariamente]
```

### ¿Qué haré hoy?
```
[Completar diariamente]
```

### ¿Hay bloqueadores?
```
[Completar diariamente]
```

---

## 🔄 Sprint Review Template

### Features Completadas
```
[Listar al final del sprint]
```

### Features Parcialmente Completadas
```
[Listar al final del sprint]
```

### Demos
```
[Screenshots/videos de features completadas]
```

### Feedback
```
[Feedback del equipo/stakeholders]
```

---

## 🔍 Sprint Retrospective Template

### ¿Qué salió bien?
```
[Completar al final del sprint]
```

### ¿Qué podemos mejorar?
```
[Completar al final del sprint]
```

### Acciones para el próximo sprint
```
[Completar al final del sprint]
```

---

**Última actualización:** 4 de diciembre de 2025  
**Actualizado por:** Development Team  
**Próxima revisión:** 18 de diciembre de 2025 (Sprint Review)
