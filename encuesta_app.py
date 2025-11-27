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
from datetime import datetime

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
# SAVE TO FIRESTORE
# -------------------------
def save_response(responses):
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
def render_question(item, index):
    """Renderiza una pregunta según su tipo y retorna la respuesta"""
    title = item.get("title", "")
    question_item = item.get("questionItem", {})
    question = question_item.get("question", {})
    required = question.get("required", False)
    
    # Label con asterisco si es requerido
    label = f"{title} {'*' if required else ''}"
    key = f"q_{index}"
    
    # Text Question
    if "textQuestion" in question:
        return st.text_input(label, key=key)
    
    # Paragraph Question
    elif "paragraphQuestion" in question:
        return st.text_area(label, key=key, height=100)
    
    # Choice Question (Radio o Checkbox)
    elif "choiceQuestion" in question:
        choice_q = question["choiceQuestion"]
        options = [opt["value"] for opt in choice_q.get("options", [])]
        choice_type = choice_q.get("type", "RADIO")
        
        if choice_type == "RADIO":
            return st.radio(label, options, key=key, index=None)
        
        elif choice_type == "CHECKBOX":
            selected = []
            st.markdown(f"**{label}**")
            for opt in options:
                if st.checkbox(opt, key=f"{key}_{opt}"):
                    selected.append(opt)
            return selected if selected else None
    
    return None

# -------------------------
# SUMMARY PANEL
# -------------------------
def show_summary_panel():
    """Muestra un resumen de todas las respuestas para evitar duplicados"""
    st.subheader("📊 Resumen de Colaboraciones")
    st.caption("Revisa qué han aportado los demás para coordinar mejor")
    
    db = get_db()
    if not db:
        st.warning("No hay conexión con la base de datos.")
        return
    
    try:
        docs = db.collection("encuesta_piscina").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        
        all_responses = []
        for doc in docs:
            data = doc.to_dict()
            all_responses.append(data.get("responses", {}))
        
        if not all_responses:
            st.info("Aún no hay respuestas registradas. ¡Sé el primero!")
            return
        
        # Métricas generales
        st.markdown("### 📈 Resumen General")
        col1, col2, col3, col4 = st.columns(4)
        
        total_personas = sum([int(r.get("¿Cuántas personas vienen contigo?", 0) or 0) for r in all_responses])
        confirmados = sum([1 for r in all_responses if "Sí" in str(r.get("¿Confirmas tu asistencia?", "")) or "Confirmo" in str(r.get("¿Confirmas tu asistencia?", ""))])
        
        col1.metric("👥 Total personas", total_personas)
        col2.metric("✅ Confirmados", confirmados)
        col3.metric("📝 Respuestas", len(all_responses))
        
        # Resumen de transporte
        necesitan_transporte = sum([1 for r in all_responses if "NECESITO que me lleven" in str(r.get("¿Cuál es tu situación con respecto al transporte?", ""))])
        ofrecen_cupos = [r for r in all_responses if "puedo llevar a otras personas" in str(r.get("¿Cuál es tu situación con respecto al transporte?", ""))]
        total_cupos = sum([int(r.get("Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?", 0) or 0) for r in ofrecen_cupos])
        
        col4.metric("🚗 Cupos disponibles", f"{total_cupos}")
        
        if necesitan_transporte > 0:
            st.warning(f"⚠️ {necesitan_transporte} persona(s) necesitan transporte")
        
        st.markdown("---")
        
        # Resumen por persona
        st.markdown("### 👥 Participantes")
        for idx, resp in enumerate(all_responses, 1):
            nombre = resp.get("Nombre y apellido", "Sin nombre")
            personas = resp.get("¿Cuántas personas vienen contigo?", "?")
            adultos_menores = resp.get("Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)", "")
            asistencia = resp.get("¿Confirmas tu asistencia?", "Sin confirmar")
            
            # Color según confirmación
            emoji = "✅" if "Sí" in str(asistencia) or "Confirmo" in str(asistencia) else "❓" if "seguro" in str(asistencia) else "❌"
            
            with st.expander(f"{emoji} {nombre} - {personas} personas ({adultos_menores})"):
                st.markdown(f"**Asistencia:** {asistencia}")
                
                # Preferencias de comida
                comida_pref = resp.get("¿Qué preferimos comer en el asado?")
                if comida_pref:
                    items = comida_pref if isinstance(comida_pref, list) else [comida_pref]
                    st.markdown(f"**🍖 Preferencia:** {', '.join(items)}")
                
                # Cooperación almuerzo
                almuerzo_coop = resp.get("¿Cómo puedes cooperar para el almuerzo (asado)?")
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
                bebidas = resp.get("¿Qué bebidas prefieres llevar o aportar?")
                cantidad_bebidas = resp.get("¿Cuántas bebidas (botellas o litros) podrías llevar?")
                if bebidas or cantidad_bebidas:
                    st.markdown("**🥤 Bebidas**")
                    if bebidas:
                        items = bebidas if isinstance(bebidas, list) else [bebidas]
                        st.write(f"• Tipo: {', '.join(items)}")
                    if cantidad_bebidas:
                        st.write(f"• Cantidad: {cantidad_bebidas}")
                
                # Hora del té
                te = resp.get("¿Qué prefieres aportar para la hora del té?")
                if te:
                    items = te if isinstance(te, list) else [te]
                    st.markdown(f"**☕ Hora del té:** {', '.join(items)}")
                
                comentario_te = resp.get("Comentarios para la hora del té")
                if comentario_te:
                    st.caption(f"💬 {comentario_te}")
                
                # Transporte
                transporte = resp.get("¿Cuál es tu situación con respecto al transporte?")
                cupos = resp.get("Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?")
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
                items = resp.get("¿Qué preferimos comer en el asado?")
                if items:
                    item_list = items if isinstance(items, list) else [items]
                    for item in item_list:
                        comida_items[item] = comida_items.get(item, 0) + 1
            
            for item, count in sorted(comida_items.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {item}: {count}")
            
            st.markdown("")
            st.markdown("**💰 Cooperación Almuerzo**")
            almuerzo_items = {}
            for resp in all_responses:
                items = resp.get("¿Cómo puedes cooperar para el almuerzo (asado)?")
                if items:
                    item_list = items if isinstance(items, list) else [items]
                    for item in item_list:
                        almuerzo_items[item] = almuerzo_items.get(item, 0) + 1
            
            for item, count in sorted(almuerzo_items.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {item}: {count}")
        
        with col2:
            st.markdown("**🥤 Bebidas**")
            bebida_items = {}
            for resp in all_responses:
                items = resp.get("¿Qué bebidas prefieres llevar o aportar?")
                if items:
                    item_list = items if isinstance(items, list) else [items]
                    for item in item_list:
                        bebida_items[item] = bebida_items.get(item, 0) + 1
            
            for item, count in sorted(bebida_items.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {item}: {count}")
            
            st.markdown("")
            st.markdown("**☕ Hora del té**")
            te_items = {}
            for resp in all_responses:
                items = resp.get("¿Qué prefieres aportar para la hora del té?")
                if items:
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
                trans = resp.get("¿Cuál es tu situación con respecto al transporte?", "")
                if "puedo llevar a otras personas" in trans:
                    nombre = resp.get("Nombre y apellido", "Sin nombre")
                    cupos = resp.get("Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?", "?")
                    st.write(f"✅ {nombre}: {cupos} cupos")
        
        with col2:
            st.markdown("**Necesitan transporte:**")
            for resp in all_responses:
                trans = resp.get("¿Cuál es tu situación con respecto al transporte?", "")
                if "NECESITO que me lleven" in trans:
                    nombre = resp.get("Nombre y apellido", "Sin nombre")
                    personas = resp.get("¿Cuántas personas vienen contigo?", "?")
                    st.write(f"❗ {nombre} ({personas} personas)")
        
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
        responses = {}
        
        with st.form("encuesta_form"):
            for idx, item in enumerate(items):
                response = render_question(item, idx)
                question_item = item.get("questionItem", {})
                question = question_item.get("question", {})
                required = question.get("required", False)
                
                responses[item.get("title", f"question_{idx}")] = response
                
                # Validación básica de campos requeridos se hace en el submit
                st.markdown("")  # Espaciado
            
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
                    
                    if required and not responses.get(title):
                        errors.append(title)
                
                if errors:
                    st.error(f"Por favor completa los campos requeridos: {', '.join(errors)}")
                else:
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
