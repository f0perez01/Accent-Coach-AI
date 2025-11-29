# 🗣️ Conversation Tutor - Guía de Uso

## 📖 Descripción General

El **Conversation Tutor** es una nueva funcionalidad integrada en Accent Coach AI que permite practicar conversación en inglés de forma natural con feedback en tiempo real.

## 🎯 Características Principales

### 1. **Conversación por Voz**
- Habla naturalmente en inglés
- Transcripción automática (STT)
- Respuestas por voz (TTS)

### 2. **Feedback Inteligente**
- ✏️ **Correcciones gramaticales** inmediatas
- 📚 **Explicaciones simples** adaptadas a tu nivel
- ✅ **Versiones mejoradas** de tus frases
- 🤖 **Preguntas de seguimiento** para mantener la conversación

### 3. **Modos de Práctica**

#### Modo Practice
- Feedback inmediato después de cada turno
- Correcciones y explicaciones visibles
- Ideal para aprender y mejorar

#### Modo Exam
- Sin feedback durante la conversación
- Evaluación completa al final
- Perfecto para evaluar tu nivel real

### 4. **Tópicos de Conversación**
- Daily Routine (Rutina diaria)
- Travel (Viajes)
- Food & Cooking (Comida y cocina)
- Work & Career (Trabajo y carrera)
- Hobbies & Interests (Pasatiempos)
- Technology (Tecnología)
- Health & Fitness (Salud y ejercicio)
- General Conversation (Conversación general)

### 5. **Niveles de Proficiencia**
- A2 (Elemental)
- B1-B2 (Intermedio) - **Recomendado**
- C1-C2 (Avanzado)

## 🚀 Cómo Usar

### Paso 1: Acceder al Conversation Tutor
1. Inicia sesión en Accent Coach AI
2. Haz clic en la pestaña **"🗣️ Conversation Tutor"**

### Paso 2: Configurar la Sesión
1. **Selecciona un tópico** que te interese
2. **Elige tu nivel** de inglés (B1-B2 recomendado)
3. **Selecciona el modo** (Practice o Exam)

### Paso 3: Iniciar la Conversación
1. Lee la pregunta inicial del tutor
2. Escucha el audio (TTS)
3. Haz clic en **"🚀 Start Conversation"**

### Paso 4: Conversar
1. Haz clic en el grabador de audio
2. **Habla naturalmente** respondiendo la pregunta
3. Haz clic en **"🚀 Send & Get Feedback"**
4. Lee el feedback (correcciones y explicaciones)
5. Responde la siguiente pregunta del tutor
6. Repite el proceso

### Paso 5: Finalizar y Exportar
1. Haz clic en **"📊 Session Stats"** para ver estadísticas
2. Haz clic en **"💾 Export Session"** para descargar el transcript
3. Haz clic en **"🔚 End Session"** cuando termines

## 💡 Ejemplo de Flujo

### Turno 1
**Tutor:** "Tell me about your typical morning routine."

**Tú (grabas):** "I wake up at 7am and I go to work."

**Feedback:**
- ✏️ **Correction:** "Great! But you can add more details about what you do between waking up and going to work."
- 📚 **Explanation:** "You can use sequence words like 'first', 'then', 'after that'."
- ✅ **Better:** "I wake up at 7am. First, I take a shower. Then I have breakfast, and after that I go to work."
- 🤖 **Follow-up:** "What do you usually have for breakfast?"

### Turno 2
**Tú (grabas):** "I usually eating toast and coffee."

**Feedback:**
- ✏️ **Correction:** "You should say: 'I usually **eat** toast and **drink** coffee.'"
- 📚 **Explanation:** "After 'usually', use the base form of the verb (eat, not eating)."
- ✅ **Better:** "I usually eat toast and drink coffee for breakfast."
- 🤖 **Follow-up:** "Do you prefer black coffee or with milk?"

## 📊 Estadísticas de Sesión

Al finalizar una sesión, verás:
- **Total turns:** Número de turnos conversacionales
- **Total errors:** Errores totales detectados
- **Duration:** Duración de la sesión en minutos
- **Topic:** Tópico practicado
- **Level:** Tu nivel de proficiencia

## 🔧 Arquitectura Técnica

### Módulos Creados

1. **conversation_tutor.py**
   - Clase `ConversationTutor`: Procesa el flujo STT → LLM → TTS
   - Clase `ConversationSession`: Maneja sesiones individuales

2. **prompt_templates.py**
   - Clase `ConversationPromptTemplate`: Templates para el LLM
   - Clase `ConversationStarters`: Preguntas iniciales por tópico

3. **conversation_manager.py**
   - Clase `ConversationManager`: Gestión de persistencia en Firestore
   - Funciones de exportación y estadísticas

4. **app.py** (modificado)
   - Nueva pestaña "Conversation Tutor"
   - Función `render_conversation_tutor()`
   - Estado de sesión en `st.session_state`

### Flujo de Datos

```
1. Usuario graba audio
   ↓
2. STT (ASR Model: Wav2Vec2)
   ↓
3. Transcripción de texto
   ↓
4. LLM (Groq: Llama-3.1-70b)
   ↓
5. Feedback estructurado
   ↓
6. TTS (gTTS)
   ↓
7. Audio de respuesta
   ↓
8. Firestore (persistencia)
```

## 🎓 Casos de Uso

### Para Estudiantes
- Practicar conversación sin presión
- Mejorar fluidez y gramática
- Recibir feedback instantáneo

### Para Profesores
- Asignar tópicos específicos
- Revisar transcripts de sesiones
- Evaluar progreso de estudiantes

### Para Preparación de Exámenes
- Modo Exam para simular condiciones reales
- Práctica de speaking para IELTS, TOEFL, Cambridge

## 🚧 Limitaciones Actuales

1. **Idioma:** Solo inglés (en-us)
2. **LLM:** Requiere API key de Groq
3. **ASR:** Requiere modelos Wav2Vec2
4. **TTS:** gTTS requiere conexión a internet

## 🔮 Posibles Mejoras Futuras

- [ ] Modo examen con evaluación automática
- [ ] Análisis de pronunciación fonética en tiempo real
- [ ] Flashcards generadas a partir de errores frecuentes
- [ ] Medidor de progreso lingüístico
- [ ] Soporte para más idiomas
- [ ] Integración con sistemas de gestión de aprendizaje (LMS)

## 📝 Notas Importantes

1. **API Keys Requeridas:**
   - `GROQ_API_KEY`: Para el LLM conversacional
   - `HF_API_TOKEN`: Para los modelos ASR

2. **Almacenamiento:**
   - Las sesiones se guardan en Firestore
   - Los audios NO se almacenan (solo transcripciones)

3. **Privacidad:**
   - Solo el usuario autenticado puede ver sus sesiones
   - Las transcripciones se almacenan de forma segura

## 🎉 ¡Listo para Usar!

La funcionalidad está completamente integrada y lista para usar. Solo necesitas:
1. Tener configuradas las API keys
2. Iniciar sesión en la aplicación
3. Ir a la pestaña "Conversation Tutor"
4. ¡Empezar a practicar!

---

**Desarrollado con ❤️ para mejorar tu inglés conversacional**
