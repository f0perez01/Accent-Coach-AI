"""
Encuesta Streamlit - Organización Familiar Día en la Piscina
Lee encuesta.json y guarda respuestas en Firestore.
Sin login, solo identificación por nombre.

USAGE:
  streamlit run encuesta_app.py
"""

import streamlit as st
import json
import uuid
import re
from datetime import datetime
from typing import Any, Dict, List

# Firebase (opcional)
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:
    firebase_admin = None

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(
    page_title="Encuesta - Día en la Piscina",
    page_icon="🏊",
    layout="centered"
)

# -------------------------
# FIREBASE INIT
# -------------------------
def init_firebase():
    if not firebase_admin:
        return
    if not firebase_admin._apps:
        try:
            if "FIREBASE" in st.secrets:
                cred_dict = dict(st.secrets["FIREBASE"])
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.warning(f"Firebase no disponible: {e}")

def get_db():
    return firestore.client() if firebase_admin and firebase_admin._apps else None

# -------------------------
# LOAD SURVEY
# -------------------------
@st.cache_data
def load_survey():
    try:
        with open("encuesta.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error cargando encuesta.json: {e}")
        return None

# -------------------------
# UTILITIES: Normalización y parseo
# -------------------------
def normalize_str(s: Any) -> Any:
    """Si s es string lo normaliza a strip y lower, si es lista, normaliza cada elemento."""
    if isinstance(s, list):
        return [str(x).strip() for x in s]
    if isinstance(s, str):
        return s.strip()
    return s

def try_int(v: Any):
    """Intenta convertir a entero, si no puede devuelve el original."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    try:
        # limpiar texto
        s = str(v).strip()
        # si es una cifra decimal sin coma
        if re.fullmatch(r"\d+", s):
            return int(s)
        # extraer primer número encontrado
        m = re.search(r"(\d+)", s)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return v

def parse_adults_minors(text: str):
    """
    Trata de extraer número de adultos y menores desde un texto.
    Retorna (adults:int, minors:int) o (None, None) si no puede inferir.
    Estrategias:
      - Buscar "adult" / "menor" / "adultos" / "menores" con números alrededor
      - Buscar dos números: asumir primero adultos, segundo menores
      - Si solo un número y coincide con 'personas' se usará como adultos
    """
    if not text:
        return None, None

    s = str(text).lower()
    # buscar patrones tipo "2 adultos, 1 menor"
    m = re.search(r"(\d+)\s*(adult[oa]s?)", s)
    n = re.search(r"(\d+)\s*(menor[ea]s?|niñ[oa]s?)", s)
    if m:
        adults = int(m.group(1))
        minors = int(n.group(1)) if n else 0
        return adults, minors

    # buscar "adultos: 2 menores: 1"
    m_alt = re.findall(r"(\d+)", s)
    if len(m_alt) >= 2:
        return int(m_alt[0]), int(m_alt[1])
    if len(m_alt) == 1:
        # si el texto contiene la palabra 'menor' asumimos que ese número son menores
        if "menor" in s or "niño" in s or "niña" in s:
            return 0, int(m_alt[0])
        # sino asumimos adultos
        return int(m_alt[0]), 0

    # si encontro palabras que indiquen "todos adultos" o "solo adultos"
    if "adult" in s and ("solo" in s or "todos" in s):
        return None, None  # el usuario no dio números concretos

    return None, None

# -------------------------
# SAVE TO FIRESTORE
# -------------------------
def save_response(responses: Dict[str, Any]):
    db = get_db()
    if not db:
        st.warning("Firestore no está configurado. Respuestas no se guardarán en la nube.")
        return False

    try:
        doc_ref = db.collection("encuesta_piscina").document()
        doc_ref.set({
            "response_id": str(uuid.uuid4()),
            "timestamp": firestore.SERVER_TIMESTAMP,
            "submitted_at": datetime.utcnow().isoformat(),
            "responses": responses
        })
        return True
    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        return False

# -------------------------
# RENDER QUESTION
# -------------------------
def render_question(item: Dict[str, Any], index: int, state: Dict[str, Any]) -> Any:
    """Renderiza una pregunta según su tipo y retorna la respuesta(normalizada)."""
    title = item.get("title", "")
    question_item = item.get("questionItem", {})
    question = question_item.get("question", {})
    required = question.get("required", False)

    # Label con asterisco si es requerido
    label = f"{title}{' *' if required else ''}"
    key = f"q_{index}"

    # Text Question
    if "textQuestion" in question:
        val = st.text_input(label, key=key)
        return normalize_str(val)

    # Paragraph Question
    elif "paragraphQuestion" in question:
        val = st.text_area(label, key=key, height=100)
        return normalize_str(val)

    # Choice Question (Radio o Checkbox)
    elif "choiceQuestion" in question:
        choice_q = question["choiceQuestion"]
        options = [opt["value"] for opt in choice_q.get("options", [])]
        choice_type = choice_q.get("type", "RADIO")

        if choice_type == "RADIO":
            val = st.radio(label, options, key=key, index=0 if not required else None)
            return normalize_str(val)

        elif choice_type == "CHECKBOX":
            st.markdown(f"**{label}**")
            selected = []
            # use stable keys (no special chars)
            for opt in options:
                safe_opt = re.sub(r"\W+", "_", opt)
                checked = st.checkbox(opt, key=f"{key}_{safe_opt}")
                if checked:
                    selected.append(opt)
            # en vez de None devolver lista vacía si nada seleccionado
            return selected

    return None

# -------------------------
# SUMMARY HELPERS (contabilidad)
# -------------------------
def compute_meat_suggestion(all_responses: List[Dict[str, Any]]):
    """
    Calcula una sugerencia de kg de carne total basada en adultos y menores.
    Usaremos por defecto:
      - Adultos: 0.5 kg por persona
      - Menores: 0.18 kg por persona
    También intentamos usar los números que cada respuesta indique.
    """
    adult_kg = 0.5
    minor_kg = 0.18

    total_adults = 0
    total_minors = 0
    fallback_total_people = 0

    for r in all_responses:
        # intentar obtener adultos/minores desde el campo específico
        am_text = r.get("Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)", "")
        adults, minors = parse_adults_minors(am_text)
        # fallback a campo "¿Cuántas personas vienen contigo?"
        total_people_field = try_int(r.get("¿Cuántas personas vienen contigo?") or 0) or 0
        fallback_total_people += total_people_field

        if adults is None and minors is None:
            # si no se parsea, asumimos que todos son adultos (salvo si el total <=2 and likely family with child? but keep simple)
            total_adults += total_people_field
        else:
            total_adults += (adults or 0)
            total_minors += (minors or 0)

    # Si no se detectaron menores, pero el fallback_total_people > total_adults assume 0 minors
    total_people = total_adults + total_minors
    if total_people == 0:
        total_people = fallback_total_people

    suggested_kg = total_adults * adult_kg + total_minors * minor_kg
    # safety min: at least 0.5 kg per 2 persons
    suggested_kg = max(suggested_kg, max(0.5, 0.25 * total_people))
    return {
        "total_people_estimated": total_people,
        "total_adults": total_adults,
        "total_minors": total_minors,
        "suggested_kg_total": round(suggested_kg, 2),
        "adult_kg_per_person": adult_kg,
        "minor_kg_per_person": minor_kg
    }

# -------------------------
# SUMMARY PANEL
# -------------------------
def show_summary_panel():
    """Muestra un resumen de todas las respuestas para evitar duplicados"""
    st.subheader("📊 Resumen de Colaboraciones")
    st.caption("Revisa qué han aportado los demás para coordinar mejor")

    db = get_db()
    if not db:
        st.warning("No hay conexión con la base de datos. El resumen se basa en datos locales si existen.")
    try:
        docs = []
        if db:
            docs = db.collection("encuesta_piscina").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
            all_responses = [doc.to_dict().get("responses", {}) for doc in docs]
        else:
            # No firestore -> intentar cargar respuestas locales (no implementado). Mostrar mensaje y salir.
            st.info("Modo sin conexión a Firestore: no hay respuestas en la nube para mostrar.")
            return

        if not all_responses:
            st.info("Aún no hay respuestas registradas. ¡Sé el primero!")
            return

        # Normalizar y analizar respuestas
        # Convertir campos numéricos donde apliquen
        for resp in all_responses:
            # convertir posibles numeros
            for k in list(resp.keys()):
                if isinstance(resp[k], str):
                    resp[k] = resp[k].strip()
                # normalizar checkbox None -> []
                if resp.get(k) is None and "¿Qué" in k or "¿Cómo" in k:
                    resp[k] = []
            # try to convert certain known numeric fields
            resp["__num_personas"] = try_int(resp.get("¿Cuántas personas vienen contigo?"))
            resp["__cupos"] = try_int(resp.get("Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?"))
            resp["__bebidas_qty"] = try_int(resp.get("¿Cuántas bebidas (botellas o litros) podrías llevar?"))

        # Métricas generales
        st.markdown("### 📈 Resumen General")
        col1, col2, col3, col4 = st.columns(4)

        total_personas = sum([int(r.get("__num_personas") or 0) for r in all_responses])
        confirmados = sum([1 for r in all_responses if "Sí" in str(r.get("¿Confirmas tu asistencia?", "")) or "Confirmo" in str(r.get("¿Confirmas tu asistencia?", ""))])

        col1.metric("👥 Total personas (reportadas)", total_personas)
        col2.metric("✅ Confirmados", confirmados)
        col3.metric("📝 Respuestas recibidas", len(all_responses))

        # Resumen de transporte
        def lower_str(x): 
            try:
                return str(x).lower()
            except:
                return ""

        necesitan_transporte = sum([1 for r in all_responses if "necesit" in lower_str(r.get("¿Cuál es tu situación con respecto al transporte?", ""))])
        ofrecen_cupos = [r for r in all_responses if "llevar a otras personas" in lower_str(r.get("¿Cuál es tu situación con respecto al transporte?", ""))]
        total_cupos = sum([int(r.get("__cupos") or 0) for r in ofrecen_cupos])

        col4.metric("🚗 Cupos disponibles", f"{total_cupos}")

        if necesitan_transporte > 0:
            st.warning(f"⚠️ {necesitan_transporte} persona(s) necesitan transporte")

        st.markdown("---")

        # Resumen por persona
        st.markdown("### 👥 Participantes")
        for idx, resp in enumerate(all_responses, 1):
            nombre = resp.get("Nombre y apellido", resp.get("Nombre", "Sin nombre"))
            personas = resp.get("¿Cuántas personas vienen contigo?", "?")
            adultos_menores = resp.get("Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)", "")
            asistencia = resp.get("¿Confirmas tu asistencia?", "Sin confirmar")

            # Color según confirmación
            asistencia_s = str(asistencia).lower()
            emoji = "✅" if "sí" in asistencia_s or "confirm" in asistencia_s else "❓" if "seguro" in asistencia_s else "❌"

            with st.expander(f"{emoji} {nombre} - {personas} personas ({adultos_menores})"):
                st.markdown(f"**Asistencia:** {asistencia}")

                # Preferencias de comida
                comida_pref = resp.get("¿Qué preferimos comer en el asado?") or []
                if comida_pref:
                    items = comida_pref if isinstance(comida_pref, list) else [comida_pref]
                    st.markdown(f"**🍖 Preferencia:** {', '.join(items)}")

                # Cooperación almuerzo
                almuerzo_coop = resp.get("¿Cómo puedes cooperar para el almuerzo (asado)?") or []
                if almuerzo_coop:
                    st.markdown("**💰 Cooperación Almuerzo**")
                    items = almuerzo_coop if isinstance(almuerzo_coop, list) else [almuerzo_coop]
                    for item in items:
                        st.write(f"• {item}")

                # Cantidad específica de carne
                cantidad_carne = resp.get("Si vas a comprar carne, pollo o longaniza, indica qué tipo y qué cantidad podrías aportar (si lo sabes).")
                if cantidad_carne:
                    st.info(f"📦 {cantidad_carne}")

                comentario_almuerzo = resp.get("Comentario adicional sobre tu aporte para el almuerzo")
                if comentario_almuerzo:
                    st.caption(f"💬 {comentario_almuerzo}")

                # Bebidas
                bebidas = resp.get("¿Qué bebidas prefieres llevar o aportar?") or []
                cantidad_bebidas = resp.get("__bebidas_qty")
                if bebidas or cantidad_bebidas:
                    st.markdown("**🥤 Bebidas**")
                    if bebidas:
                        items = bebidas if isinstance(bebidas, list) else [bebidas]
                        st.write(f"• Tipo: {', '.join(items)}")
                    if cantidad_bebidas:
                        st.write(f"• Cantidad (estimada): {cantidad_bebidas}")

                # Hora del té
                te = resp.get("¿Qué prefieres aportar para la hora del té?") or []
                if te:
                    items = te if isinstance(te, list) else [te]
                    st.markdown(f"**☕ Hora del té:** {', '.join(items)}")

                comentario_te = resp.get("Comentarios para la hora del té")
                if comentario_te:
                    st.caption(f"💬 {comentario_te}")

                # Transporte
                transporte = resp.get("¿Cuál es tu situación con respecto al transporte?")
                cupos = resp.get("__cupos")
                if transporte:
                    st.markdown(f"**🚗 Transporte:** {transporte}")
                    if cupos:
                        st.write(f"   → Cupos disponibles: {cupos}")

                # Horario
                hora = resp.get("¿A qué hora puedes llegar?")
                if hora:
                    st.markdown(f"**🕐 Llegada:** {hora}")

                # Extras
                extras = resp.get("¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?")
                if extras:
                    st.markdown(f"**➕ Extras:** {extras}")

                # Restricciones
                restricciones = resp.get("¿Tienes alguna restricción alimentaria o preferencia?")
                if restricciones:
                    st.markdown(f"**⚠️ Restricciones:** {restricciones}")

        # Resumen consolidado
        st.markdown("---")
        st.markdown("### 📋 Consolidado de Aportes")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🍖 Preferencias de Comida**")
            comida_items = {}
            for resp in all_responses:
                items = resp.get("¿Qué preferimos comer en el asado?") or []
                item_list = items if isinstance(items, list) else [items]
                for item in item_list:
                    comida_items[item] = comida_items.get(item, 0) + 1

            for item, count in sorted(comida_items.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {item}: {count}")

            st.markdown("")
            st.markdown("**💰 Cooperación Almuerzo**")
            almuerzo_items = {}
            for resp in all_responses:
                items = resp.get("¿Cómo puedes cooperar para el almuerzo (asado)?") or []
                item_list = items if isinstance(items, list) else [items]
                for item in item_list:
                    almuerzo_items[item] = almuerzo_items.get(item, 0) + 1

            for item, count in sorted(almuerzo_items.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {item}: {count}")

        with col2:
            st.markdown("**🥤 Bebidas**")
            bebida_items = {}
            for resp in all_responses:
                items = resp.get("¿Qué bebidas prefieres llevar o aportar?") or []
                item_list = items if isinstance(items, list) else [items]
                for item in item_list:
                    bebida_items[item] = bebida_items.get(item, 0) + 1

            for item, count in sorted(bebida_items.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {item}: {count}")

            st.markdown("")
            st.markdown("**☕ Hora del té**")
            te_items = {}
            for resp in all_responses:
                items = resp.get("¿Qué prefieres aportar para la hora del té?") or []
                item_list = items if isinstance(items, list) else [items]
                for item in item_list:
                    te_items[item] = te_items.get(item, 0) + 1

            for item, count in sorted(te_items.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {item}: {count}")

        # Resumen de transporte detallado
        st.markdown("---")
        st.markdown("### 🚗 Coordinación de Transporte")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Ofrecen llevar personas:**")
            for resp in all_responses:
                trans = str(resp.get("¿Cuál es tu situación con respecto al transporte?", "")).lower()
                if "llevar a otras personas" in trans:
                    nombre = resp.get("Nombre y apellido", resp.get("Nombre", "Sin nombre"))
                    cupos = resp.get("__cupos", "?")
                    st.write(f"✅ {nombre}: {cupos} cupos")

        with col2:
            st.markdown("**Necesitan transporte:**")
            for resp in all_responses:
                trans = str(resp.get("¿Cuál es tu situación con respecto al transporte?", "")).lower()
                if "necesit" in trans:
                    nombre = resp.get("Nombre y apellido", resp.get("Nombre", "Sin nombre"))
                    personas = resp.get("¿Cuántas personas vienen contigo?", "?")
                    st.write(f"❗ {nombre} ({personas} personas)")

        # Cálculo sugerido de carne
        st.markdown("---")
        st.markdown("### 🧾 Sugerencia de compras (carne) basada en respuestas")
        meat = compute_meat_suggestion(all_responses)
        st.write(f"• Personas estimadas: **{meat['total_people_estimated']}**")
        st.write(f"• Adultos (detectados): **{meat['total_adults']}**")
        st.write(f"• Menores (detectados): **{meat['total_minors']}**")
        st.write(f"• Kg sugeridos totales de carne: **{meat['suggested_kg_total']} kg**")
        st.caption(f"(Se usó {meat['adult_kg_per_person']} kg/adulto y {meat['minor_kg_per_person']} kg/menor como referencia)")

    except Exception as e:
        st.error(f"Error cargando resumen: {e}")

# -------------------------
# MAIN APP
# -------------------------
def main():
    init_firebase()

    survey = load_survey()
    if not survey:
        st.stop()

    # Header
    st.title(survey.get("title", "Encuesta"))
    st.markdown(survey.get("description", ""))

    # Navigation tabs - Mobile friendly
    tab1, tab2 = st.tabs(["📝 Responder", "📊 Ver Respuestas"])

    with tab2:
        show_summary_panel()

    with tab1:
        st.markdown("---")

        # Initialize session state
        if "submitted" not in st.session_state:
            st.session_state.submitted = False

        if st.session_state.submitted:
            st.success("✅ ¡Gracias! Tu respuesta ha sido registrada.")
            st.info("💡 Revisa la pestaña 'Ver Respuestas' para coordinar con los demás.")
            if st.button("Enviar otra respuesta"):
                st.session_state.submitted = False
                st.rerun()
            st.stop()

        # Render questions
        items = survey.get("items", [])
        responses: Dict[str, Any] = {}

        # We'll capture transport selection to show/hide cupos dynamically
        transport_selection = None
        cupos_value = None

        with st.form("encuesta_form"):
            for idx, item in enumerate(items):
                title = item.get("title", "")
                # If this is the cupos question, we skip rendering here; we will render conditionally below
                if title == "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?":
                    continue

                # render normally
                response = render_question(item, idx, st.session_state)
                # normalize checkboxes to [] if None
                if isinstance(response, list):
                    responses[title] = response
                else:
                    responses[title] = response if response is not None else ""

                # track transport selection
                if title == "¿Cuál es tu situación con respecto al transporte?":
                    transport_selection = responses[title] or ""

                st.markdown("")  # Espaciado

            # transport-dependent cupos field (dynamic)
            if transport_selection:
                ts = str(transport_selection).lower()
                if "llevar a otras personas" in ts:
                    cupos_value = st.number_input("Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?",
                                                  min_value=0, step=1, value=1, key="dynamic_cupos")
                    responses["Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?"] = int(cupos_value)
                else:
                    # if the survey had a pre-defined cupos answer (should not) ensure it's empty
                    responses["Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?"] = ""

            # If no transport selection (user skipped), still render cupos as hidden empty string
            if "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?" not in responses:
                responses["Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?"] = ""

            # Submit button
            submitted = st.form_submit_button("📤 Enviar Respuesta", type="primary", use_container_width=True)

            if submitted:
                # Validar campos requeridos
                errors = []
                for idx, item in enumerate(items):
                    title = item.get("title", "")
                    question_item = item.get("questionItem", {})
                    question = question_item.get("question", {})
                    required = question.get("required", False)
                    val = responses.get(title)
                    # normalized empty checks: for checkbox expect list, for others expect non-empty string
                    if required:
                        if isinstance(val, list):
                            if len(val) == 0:
                                errors.append(title)
                        else:
                            if val is None or str(val).strip() == "":
                                errors.append(title)

                if errors:
                    st.error(f"Por favor completa los campos requeridos: {', '.join(errors)}")
                else:
                    # Post-process numeric conversions for key fields
                    # Convert some well-known fields to int when possible
                    numeric_fields = [
                        "¿Cuántas personas vienen contigo?",
                        "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?",
                        "¿Cuántas bebidas (botellas o litros) podrías llevar?"
                    ]
                    for nf in numeric_fields:
                        if nf in responses:
                            responses[nf] = try_int(responses[nf])

                    # ensure checkboxes are lists (not None)
                    for k, v in list(responses.items()):
                        if isinstance(v, list):
                            responses[k] = v
                        else:
                            # keep strings trimmed
                            if isinstance(v, str):
                                responses[k] = v.strip()

                    # Guardar respuestas
                    success = save_response(responses)
                    if success or not get_db():
                        st.session_state.submitted = True
                        st.rerun()

        # Info footer
        st.markdown("---")
        st.caption("🏊 Encuesta Familiar - Día en la Piscina")

if __name__ == "__main__":
    main()
