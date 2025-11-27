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
    st.markdown("---")
    
    # Initialize session state
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    
    if st.session_state.submitted:
        st.success("✅ ¡Gracias! Tu respuesta ha sido registrada.")
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
    
    # Admin: ver respuestas (opcional)
    with st.expander("🔧 Admin - Ver respuestas guardadas"):
        db = get_db()
        if db:
            try:
                docs = db.collection("encuesta_piscina").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream()
                count = 0
                for doc in docs:
                    count += 1
                    data = doc.to_dict()
                    st.json(data.get("responses", {}))
                    st.caption(f"ID: {doc.id} - {data.get('submitted_at', 'N/A')}")
                    st.markdown("---")
                
                if count == 0:
                    st.info("No hay respuestas aún.")
            except Exception as e:
                st.error(f"Error cargando respuestas: {e}")
        else:
            st.warning("Firestore no configurado.")


if __name__ == "__main__":
    main()
