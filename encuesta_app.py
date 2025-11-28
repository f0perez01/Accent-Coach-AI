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
import csv
import io
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
# FIELD MAPPINGS: Compatibilidad entre versiones de campos
# -------------------------
# Mapeo de nombres de campos antiguos -> nuevos (para normalización al guardar)
FIELD_NORMALIZATION = {
    "Nombre y apellido": "Nombre completo",
    "¿Cuántas personas vienen contigo?": "¿Cuántas personas en total van contigo?",
    "¿Cómo puedes cooperar para el almuerzo (asado)?": "¿En qué te gustaría cooperar para el almuerzo?",
    "¿Qué preferimos comer en el asado?": "¿Qué opción prefieres para el almuerzo?",
    "Comentario adicional sobre tu aporte para el almuerzo": "Comentario adicional para el almuerzo",
    "¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?": "¿Puedes llevar algo adicional? (sombrillas, juegos, parlante, etc.)",
    "¿Cuántas bebidas (botellas o litros) podrías llevar?": "¿Cuántas bebidas podrías llevar?"
}

# Mapeo de campos a todos sus posibles aliases (para búsqueda al cargar)
FIELD_ALIASES = {
    "Nombre y apellido": ["Nombre completo", "Nombre y apellido", "Nombre"],
    "¿Cuántas personas vienen contigo?": ["¿Cuántas personas en total van contigo?", "¿Cuántas personas vienen contigo?"],
    "¿Cómo puedes cooperar para el almuerzo (asado)?": ["¿En qué te gustaría cooperar para el almuerzo?", "¿Cómo puedes cooperar para el almuerzo (asado)?"],
    "¿Qué preferimos comer en el asado?": ["¿Qué opción prefieres para el almuerzo?", "¿Qué preferimos comer en el asado?"],
    "Comentario adicional sobre tu aporte para el almuerzo": ["Comentario adicional para el almuerzo", "Comentario adicional sobre tu aporte para el almuerzo"],
    "¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?": ["¿Puedes llevar algo adicional? (sombrillas, juegos, parlante, etc.)", "¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?"],
    "¿Cuántas bebidas (botellas o litros) podrías llevar?": ["¿Cuántas bebidas podrías llevar?", "¿Cuántas bebidas (botellas o litros) podrías llevar?"],
    "Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)": ["Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)", "¿Cuántas personas en total van contigo?"]
}

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

def remove_accents(text: str) -> str:
    """Remueve acentos de un texto para comparaciones más robustas."""
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def normalize_confirmation(text: Any) -> str:
    """Normaliza respuesta de confirmación de asistencia."""
    if not text:
        return "no_respondido"
    s = str(text).lower().strip()
    s = remove_accents(s)

    if "si" in s or "confirm" in s:
        return "confirmado"
    elif "no estoy seguro" in s or "tal vez" in s or "quiza" in s:
        return "incierto"
    elif "no" in s:
        return "no_asiste"
    return "no_respondido"


def get_field_value(resp: Dict[str, Any], *field_names) -> Any:
    """Obtiene valor de un campo soportando múltiples nombres (compatibilidad)."""
    for field_name in field_names:
        if field_name in resp:
            return resp[field_name]
    return None


def resolve_default_value(resp: Dict[str, Any], title: str) -> Any:
    """Resuelve el valor por defecto para una pregunta `title` buscando en `resp`.
    Estrategias (en orden):
      - clave exacta
      - aliases definidos en FIELD_ALIASES
      - clave resultante de FIELD_NORMALIZATION
      - normalización (sin tildes / minúsculas) y comparación exacta
      - comparación por inclusión (titulo dentro de clave o viceversa)
    """
    if not resp:
        return None

    # 1) exact match
    if title in resp:
        return resp[title]

    # 2) aliases map for this title
    aliases = FIELD_ALIASES.get(title, [])
    for a in aliases:
        if a in resp:
            return resp[a]

    # 3) normalization mapping (old -> new)
    if title in FIELD_NORMALIZATION:
        norm = FIELD_NORMALIZATION[title]
        if norm in resp:
            return resp[norm]

    # helper normalizer for fuzzy compare
    def norm_key(s: Any) -> str:
        return remove_accents(str(s).lower()).strip()

    target = norm_key(title)

    # 4) exact normalized match against keys
    for k in resp.keys():
        if norm_key(k) == target:
            return resp[k]

    # 5) inclusion-based fuzzy match
    for k in resp.keys():
        nk = norm_key(k)
        if target in nk or nk in target:
            return resp[k]

    # 6) try matching against any alias normalization globally
    for alias_list in FIELD_ALIASES.values():
        for a in alias_list:
            if norm_key(a) == target:
                # find that alias in resp
                for k in resp.keys():
                    if norm_key(k) == norm_key(a):
                        return resp[k]

    return None

def tiene_datos_relevantes(resp: Dict[str, Any]) -> bool:
    """Verifica si la respuesta tiene datos relevantes para mostrar en expander."""
    # Campos con AMBAS versiones (compatibilidad con datos antiguos y nuevos)
    campos_importantes = [
        # Versiones nuevas (datos reales de Firestore)
        "¿En qué te gustaría cooperar para el almuerzo?",
        "Comentario adicional para el almuerzo",
        "¿Qué bebidas prefieres llevar o aportar?",
        "¿Qué prefieres aportar para la hora del té?",
        "¿Puedes llevar algo adicional? (sombrillas, juegos, parlante, etc.)",
        "¿Tienes alguna restricción alimentaria o preferencia?",
        # Versiones antiguas (compatibilidad)
        "¿Cómo puedes cooperar para el almuerzo (asado)?",
        "Si vas a comprar carne, pollo o longaniza, indica qué tipo y qué cantidad podrías aportar (si lo sabes).",
        "Comentario adicional sobre tu aporte para el almuerzo",
        "¿Cuál es tu situación con respecto al transporte?",
        "¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?"
    ]

    for campo in campos_importantes:
        val = resp.get(campo)
        if val:
            # Si es lista, verificar que no esté vacía
            if isinstance(val, list) and len(val) > 0:
                # Excluir listas con solo "Nada" o vacíos
                if not (len(val) == 1 and any(x in str(val[0]).lower() for x in ["nada", ""])):
                    return True
            # Si es string, verificar que no esté vacío
            elif isinstance(val, str) and val.strip():
                return True
    return False

def export_to_csv(responses: List[Dict[str, Any]]) -> str:
    """Exporta las respuestas a formato CSV."""
    output = io.StringIO()

    if not responses:
        return ""

    # Campos principales a exportar
    fieldnames = [
        "Nombre y apellido",
        "Confirmación",
        "Total personas",
        "Adultos y menores",
        "Preferencias comida",
        "Cooperación almuerzo",
        "Cantidad carne",
        "Comentario adicional",
        "Bebidas tipo",
        "Bebidas cantidad",
        "Hora del té",
        "Transporte",
        "Cupos disponibles",
        "Hora llegada",
        "Extras",
        "Restricciones"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for resp in responses:
        # Formatear listas como strings separados por comas
        def format_field(val):
            if isinstance(val, list):
                return ", ".join([str(v) for v in val if v])
            return str(val) if val else ""

        confirmacion_text = {
            "confirmado": "Confirmado",
            "incierto": "No está seguro",
            "no_asiste": "No asistirá",
            "no_respondido": "Sin confirmar"
        }

        row = {
            "Nombre y apellido": get_field_value(resp, "Nombre completo", "Nombre y apellido", "Nombre") or "Sin nombre",
            "Confirmación": confirmacion_text.get(resp.get("__confirmacion_normalizada", "no_respondido"), "Sin confirmar"),
            "Total personas": resp.get("__num_personas", ""),
            "Adultos y menores": get_field_value(resp, "Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)", "¿Cuántas personas en total van contigo?") or "",
            "Preferencias comida": format_field(get_field_value(resp, "¿Qué opción prefieres para el almuerzo?", "¿Qué preferimos comer en el asado?")),
            "Cooperación almuerzo": format_field(get_field_value(resp, "¿En qué te gustaría cooperar para el almuerzo?", "¿Cómo puedes cooperar para el almuerzo (asado)?")),
            "Cantidad carne": get_field_value(resp, "Si vas a comprar carne, pollo o longaniza, indica qué tipo y qué cantidad podrías aportar (si lo sabes).") or "",
            "Bebidas tipo": format_field(resp.get("¿Qué bebidas prefieres llevar o aportar?")),
            "Bebidas cantidad": resp.get("__bebidas_qty", ""),
            "Hora del té": format_field(resp.get("¿Qué prefieres aportar para la hora del té?")),
            "Transporte": get_field_value(resp, "¿Cuál es tu situación con respecto al transporte?") or "",
            "Cupos disponibles": resp.get("__cupos", ""),
            "Hora llegada": resp.get("¿A qué hora puedes llegar?", ""),
            "Extras": get_field_value(resp, "¿Puedes llevar algo adicional? (sombrillas, juegos, parlante, etc.)", "¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?") or "",
            "Restricciones": resp.get("¿Tienes alguna restricción alimentaria o preferencia?", ""),
            "Comentario adicional": get_field_value(resp, "Comentario adicional para el almuerzo", "Comentario adicional sobre tu aporte para el almuerzo") or ""
        }

        writer.writerow(row)

    return output.getvalue()

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
    
    # Estrategia: primero buscar el patrón "palabra: número" que es más específico
    # luego buscar "número palabra" como fallback
    
    # Patrón 1: "adultos: 2" o "menores: 1" (palabra CON dos puntos antes del número)
    adults_with_colon = re.findall(r"\b(?:adult[oa]s?)\s*:\s*(\d+)", s)
    minors_with_colon = re.findall(r"\b(?:menor(?:es)?|niñ[oa]s?)\s*:\s*(\d+)", s)
    
    # Patrón 2: "2 adultos" o "1 menor" (número antes de la palabra)
    adults_num_first = re.findall(r"(\d+)\s+(?:adult[oa]s?)\b", s) if not adults_with_colon else []
    minors_num_first = re.findall(r"(\d+)\s+(?:menor(?:es)?|niñ[oa]s?)\b", s) if not minors_with_colon else []
    
    # Combinar resultados priorizando el patrón con dos puntos
    adults_matches = adults_with_colon or adults_num_first
    minors_matches = minors_with_colon or minors_num_first
    
    # Si encontramos palabras clave específicas, usarlas
    if adults_matches or minors_matches:
        adults = int(adults_matches[0]) if adults_matches else 0
        minors = int(minors_matches[0]) if minors_matches else 0
        return adults, minors

    # buscar "adultos: 2 menores: 1" o similar con dos números
    all_nums = re.findall(r"(\d+)", s)
    if len(all_nums) >= 2:
        return int(all_nums[0]), int(all_nums[1])
    if len(all_nums) == 1:
        # si el texto contiene la palabra 'menor' asumimos que ese número son menores
        if "menor" in s or "niño" in s or "niña" in s:
            return 0, int(all_nums[0])
        # sino asumimos adultos
        return int(all_nums[0]), 0

    # si encontro palabras que indiquen "todos adultos" o "solo adultos"
    if "adult" in s and ("solo" in s or "todos" in s):
        return None, None  # el usuario no dio números concretos

    return None, None

# -------------------------
# FIRESTORE OPERATIONS
# -------------------------
def get_all_participant_names():
    """Obtiene lista de nombres de todos los participantes."""
    db = get_db()
    if not db:
        return []

    try:
        docs = db.collection("encuesta_piscina").stream()
        names = []
        for doc in docs:
            data = doc.to_dict()
            responses = data.get("responses", {})
            nombre = get_field_value(responses, "Nombre completo", "Nombre y apellido", "Nombre")
            if nombre:
                names.append({
                    "nombre": nombre,
                    "doc_id": doc.id,
                    "timestamp": data.get("timestamp")
                })
        # Ordenar por nombre
        names.sort(key=lambda x: x["nombre"].lower())
        return names
    except Exception as e:
        st.error(f"Error obteniendo nombres: {e}")
        return []

def load_response_by_name(nombre: str):
    """Carga la respuesta más reciente de un participante por nombre."""
    db = get_db()
    if not db:
        return None, None

    try:
        docs = db.collection("encuesta_piscina").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()

        for doc in docs:
            data = doc.to_dict()
            responses = data.get("responses", {})
            resp_nombre = get_field_value(responses, "Nombre completo", "Nombre y apellido", "Nombre")

            if resp_nombre and resp_nombre.strip().lower() == nombre.strip().lower():
                return doc.id, responses

        return None, None
    except Exception as e:
        st.error(f"Error cargando respuesta: {e}")
        return None, None

def save_response(responses: Dict[str, Any], doc_id: str = None):
    """Guarda o actualiza una respuesta en Firestore."""
    db = get_db()
    if not db:
        st.warning("Firestore no está configurado. Respuestas no se guardarán en la nube.")
        return False

    try:
        if doc_id:
            # Actualizar documento existente
            doc_ref = db.collection("encuesta_piscina").document(doc_id)
            doc_ref.update({
                "timestamp": firestore.SERVER_TIMESTAMP,
                "submitted_at": datetime.utcnow().isoformat(),
                "responses": responses,
                "updated": True
            })
        else:
            # Crear nuevo documento
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
def render_question(item: Dict[str, Any], index: int, default_value: Any = None) -> Any:
    """Renderiza una pregunta según su tipo y retorna la respuesta normalizada."""
    title = item.get("title", "")
    question_item = item.get("questionItem", {})
    question = question_item.get("question", {})
    required = question.get("required", False)

    # Label con asterisco si es requerido
    label = f"{title}{' *' if required else ''}"
    key = f"q_{index}"
    
    # Definir placeholders contextuales
    placeholder = ""
    if "nombre" in title.lower():
        placeholder = "Ej: Juan Pérez"
    elif "personas" in title.lower() and "cuántas" in title.lower():
        placeholder = "Ej: 3"
    elif "adultos" in title.lower() and "menores" in title.lower():
        placeholder = "Ej: 2 adultos, 1 menor  o  adultos: 2 menores: 1"
    elif "cantidad" in title.lower() and "carne" in title.lower():
        placeholder = "Ej: 2 kg de vacuno, 1 kg de pollo"
    elif "bebidas" in title.lower() and "cuántas" in title.lower():
        placeholder = "Ej: 6"
    elif "hora" in title.lower() and "llegar" in title.lower():
        placeholder = "Ej: 11:00 AM"
    elif "cupos" in title.lower():
        placeholder = "Ej: 3"

    # Text Question
    if "textQuestion" in question:
        val = st.text_input(label, value=default_value if default_value else "", key=key, placeholder=placeholder)
        return normalize_str(val)

    # Paragraph Question
    elif "paragraphQuestion" in question:
        val = st.text_area(label, value=default_value if default_value else "", key=key, height=100, placeholder=placeholder)
        return normalize_str(val)

    # Choice Question (Radio o Checkbox)
    elif "choiceQuestion" in question:
        choice_q = question["choiceQuestion"]
        options = [opt["value"] for opt in choice_q.get("options", [])]
        choice_type = choice_q.get("type", "RADIO")

        if choice_type == "RADIO":
            # Encontrar índice del valor por defecto
            default_index = None
            if default_value is not None:
                # si el valor por defecto es lista (datos mal guardados), tomar el primero
                dv = default_value[0] if isinstance(default_value, list) and default_value else default_value
                try:
                    default_index = options.index(dv)
                except Exception:
                    default_index = None
            # Llamar a st.radio con o sin índice según corresponda
            if default_index is not None and isinstance(default_index, int) and 0 <= default_index < len(options):
                val = st.radio(label, options, key=key, index=default_index)
            else:
                val = st.radio(label, options, key=key)
            return normalize_str(val)

        elif choice_type == "CHECKBOX":
            st.markdown(f"**{label}**")
            selected = []
            # Convertir default_value a lista si existe
            default_list = []
            if isinstance(default_value, list):
                default_list = [str(x).strip() for x in default_value if x is not None]
            elif isinstance(default_value, str):
                # intentar parsear JSON estilo lista
                try:
                    parsed = json.loads(default_value)
                    if isinstance(parsed, list):
                        default_list = [str(x).strip() for x in parsed if x is not None]
                except Exception:
                    # fallback: separar por comas
                    default_list = [x.strip() for x in default_value.split(",") if x.strip()]
            # use stable keys (no special chars)
            for opt in options:
                safe_opt = re.sub(r"\W+", "_", opt)
                checked = st.checkbox(opt, value=(opt in default_list), key=f"{key}_{safe_opt}")
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
        
        # Si tenemos datos de adultos/menores, usarlos
        if adults is not None or minors is not None:
            total_adults += (adults or 0)
            total_minors += (minors or 0)
        else:
            # Si no hay datos específicos, asumir que el total son adultos
            total_adults += total_people_field
        
        # Acumular fallback para validación
        fallback_total_people += total_people_field

    total_people = total_adults + total_minors
    # Si no se detectó nada, usar el fallback completo
    if total_people == 0:
        total_people = fallback_total_people
        total_adults = fallback_total_people

    suggested_kg = total_adults * adult_kg + total_minors * minor_kg
    # safety min: at least 0.5 kg per 2 persons
    if total_people > 0:
        suggested_kg = max(suggested_kg, max(0.5, 0.25 * total_people))
    else:
        suggested_kg = 0
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

        # ===== FILTROS Y BÚSQUEDA =====
        st.markdown("### 🔍 Filtros")
        col_search, col_filter1, col_filter2 = st.columns([2, 1, 1])

        with col_search:
            search_term = st.text_input("🔎 Buscar por nombre", "", placeholder="Escribe un nombre...")

        with col_filter1:
            filter_confirmacion = st.selectbox(
                "Filtrar por confirmación",
                ["Todos", "Confirmados", "Inciertos", "No asisten", "Sin responder"]
            )

        with col_filter2:
            filter_transporte = st.selectbox(
                "Filtrar por transporte",
                ["Todos", "Ofrecen cupos", "Necesitan transporte", "Tienen vehículo"]
            )

        st.markdown("---")

        # Normalizar y analizar respuestas
        # Convertir campos numéricos donde apliquen
        for resp in all_responses:
            # convertir posibles numeros
            for k in list(resp.keys()):
                if isinstance(resp[k], str):
                    resp[k] = resp[k].strip()
                # normalizar checkbox None -> []
                if resp.get(k) is None:
                    # Detectar campos de checkbox de manera más robusta
                    if any(keyword in k for keyword in ["¿Qué prefieres", "¿Cómo puedes", "¿Qué bebidas"]):
                        resp[k] = []

            # Campos numéricos (soportar ambos nombres de campo)
            num_personas_field = get_field_value(resp, "¿Cuántas personas en total van contigo?", "¿Cuántas personas vienen contigo?")
            num_personas_val = try_int(num_personas_field)
            resp["__num_personas"] = num_personas_val if isinstance(num_personas_val, int) else 0

            cupos_field = get_field_value(resp, "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?")
            cupos_val = try_int(cupos_field)
            resp["__cupos"] = cupos_val if isinstance(cupos_val, int) else 0

            bebidas_field = get_field_value(resp, "¿Cuántas bebidas podrías llevar?", "¿Cuántas bebidas (botellas o litros) podrías llevar?")
            bebidas_val = try_int(bebidas_field)
            resp["__bebidas_qty"] = bebidas_val if isinstance(bebidas_val, int) else 0

            # Normalizar confirmación
            resp["__confirmacion_normalizada"] = normalize_confirmation(resp.get("¿Confirmas tu asistencia?"))

            # Normalizar transporte
            trans_text = str(resp.get("¿Cuál es tu situación con respecto al transporte?", "")).lower()
            resp["__transporte_tipo"] = "ofrece_cupos" if "llevar a otras personas" in trans_text else \
                                        "necesita" if "necesit" in trans_text else \
                                        "tiene_vehiculo" if "tengo" in trans_text or "propio" in trans_text else "ninguno"

        # ===== APLICAR FILTROS =====
        filtered_responses = all_responses.copy()

        # Filtro por búsqueda de nombre
        if search_term:
            search_normalized = remove_accents(search_term.lower())
            filtered_responses = [
                r for r in filtered_responses
                if search_normalized in remove_accents(
                    str(get_field_value(r, "Nombre completo", "Nombre y apellido", "Nombre") or "").lower()
                )
            ]

        # Filtro por confirmación
        if filter_confirmacion != "Todos":
            filter_map = {
                "Confirmados": "confirmado",
                "Inciertos": "incierto",
                "No asisten": "no_asiste",
                "Sin responder": "no_respondido"
            }
            filtered_responses = [
                r for r in filtered_responses
                if r.get("__confirmacion_normalizada") == filter_map.get(filter_confirmacion)
            ]

        # Filtro por transporte
        if filter_transporte != "Todos":
            transport_map = {
                "Ofrecen cupos": "ofrece_cupos",
                "Necesitan transporte": "necesita",
                "Tienen vehículo": "tiene_vehiculo"
            }
            filtered_responses = [
                r for r in filtered_responses
                if r.get("__transporte_tipo") == transport_map.get(filter_transporte)
            ]

        # Mostrar contador de resultados filtrados y botón de exportación
        col_info, col_export = st.columns([3, 1])

        with col_info:
            if len(filtered_responses) < len(all_responses):
                st.info(f"📋 Mostrando {len(filtered_responses)} de {len(all_responses)} respuestas")
            else:
                st.info(f"📋 Mostrando todas las {len(all_responses)} respuestas")

        with col_export:
            if all_responses:
                csv_data = export_to_csv(all_responses)
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv_data,
                    file_name=f"encuesta_piscina_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Descargar todas las respuestas en formato CSV"
                )

        # Métricas generales (basadas en TODAS las respuestas, no filtradas)
        st.markdown("### 📈 Resumen General")
        col1, col2, col3, col4 = st.columns(4)

        total_personas = sum([r.get("__num_personas", 0) for r in all_responses])
        confirmados = sum([1 for r in all_responses if r.get("__confirmacion_normalizada") == "confirmado"])
        inciertos = sum([1 for r in all_responses if r.get("__confirmacion_normalizada") == "incierto"])

        col1.metric("👥 Total personas", total_personas)
        col2.metric("✅ Confirmados", confirmados)
        col3.metric("📝 Respuestas", len(all_responses))

        # Resumen de transporte mejorado
        necesitan_transporte = sum([1 for r in all_responses if r.get("__transporte_tipo") == "necesita"])
        ofrecen_cupos = [r for r in all_responses if r.get("__transporte_tipo") == "ofrece_cupos"]
        total_cupos = sum([r.get("__cupos", 0) for r in ofrecen_cupos])

        # Calcular personas que necesitan transporte
        personas_necesitan_transporte = sum([
            r.get("__num_personas", 1) for r in all_responses
            if r.get("__transporte_tipo") == "necesita"
        ])

        col4.metric("🚗 Cupos disponibles", f"{total_cupos}")

        # Alertas mejoradas
        if necesitan_transporte > 0:
            balance = total_cupos - personas_necesitan_transporte
            if balance < 0:
                st.error(f"🚨 ALERTA: Faltan {abs(balance)} cupos de transporte ({personas_necesitan_transporte} personas necesitan, solo {total_cupos} cupos disponibles)")
            elif balance == 0:
                st.warning(f"⚠️ Transporte justo: {necesitan_transporte} persona(s) necesitan transporte, hay exactamente {total_cupos} cupos")
            else:
                st.success(f"✅ Transporte OK: {total_cupos} cupos disponibles para {personas_necesitan_transporte} personas que necesitan")

        if inciertos > 0:
            st.info(f"❓ {inciertos} persona(s) aún no han confirmado definitivamente")

        # ===== PANEL DE INSIGHTS Y RECOMENDACIONES =====
        st.markdown("---")
        st.markdown("### 💡 Insights y Recomendaciones")

        # Analizar restricciones alimentarias
        restricciones_list = []
        for resp in all_responses:
            rest = resp.get("¿Tienes alguna restricción alimentaria o preferencia?")
            if rest and str(rest).strip():
                nombre = get_field_value(resp, "Nombre completo", "Nombre y apellido", "Nombre") or "Sin nombre"
                restricciones_list.append((nombre, rest))

        if restricciones_list:
            with st.expander("⚠️ Restricciones Alimentarias - ¡IMPORTANTE!", expanded=True):
                st.warning("**Recordar estas restricciones al preparar la comida:**")
                for nombre, rest in restricciones_list:
                    st.write(f"• **{nombre}**: {rest}")

        # Analizar comentarios especiales
        comentarios_especiales = []
        for resp in all_responses:
            com = get_field_value(resp, "Comentario adicional para el almuerzo", "Comentario adicional sobre tu aporte para el almuerzo")
            if com and str(com).strip():
                nombre = get_field_value(resp, "Nombre completo", "Nombre y apellido", "Nombre") or "Sin nombre"
                comentarios_especiales.append((nombre, com))

        if comentarios_especiales:
            with st.expander("📝 Comentarios Especiales del Almuerzo", expanded=False):
                for nombre, com in comentarios_especiales:
                    st.info(f"**{nombre}**: {com}")

        # Analizar extras que traerán
        extras_items = []
        for resp in all_responses:
            extra = get_field_value(resp, "¿Puedes llevar algo adicional? (sombrillas, juegos, parlante, etc.)", "¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?")
            if extra and str(extra).strip():
                nombre = get_field_value(resp, "Nombre completo", "Nombre y apellido", "Nombre") or "Sin nombre"
                extras_items.append((nombre, extra))

        if extras_items:
            with st.expander("🎉 Extras que traerán", expanded=False):
                st.success("**Items adicionales confirmados:**")
                for nombre, extra in extras_items:
                    st.write(f"• **{nombre}**: {extra}")

        st.markdown("---")

        # Resumen por persona (usar filtered_responses)
        st.markdown("### 👥 Participantes")

        if not filtered_responses:
            st.info("No hay participantes que coincidan con los filtros seleccionados.")

        for resp in filtered_responses:
            nombre = get_field_value(resp, "Nombre completo", "Nombre y apellido", "Nombre") or "Sin nombre"
            personas = resp.get("__num_personas", "?")
            adultos_menores = get_field_value(resp, "Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)", "¿Cuántas personas en total van contigo?") or "No especificado"

            # Emoji según confirmación normalizada
            confirmacion_norm = resp.get("__confirmacion_normalizada", "no_respondido")
            emoji_map = {
                "confirmado": "✅",
                "incierto": "❓",
                "no_asiste": "❌",
                "no_respondido": "⚪"
            }
            emoji = emoji_map.get(confirmacion_norm, "⚪")

            # Solo mostrar expander si tiene datos relevantes
            if not tiene_datos_relevantes(resp):
                st.markdown(f"{emoji} **{nombre}** - {personas} personas ({adultos_menores}) - _Sin detalles adicionales_")
                continue

            with st.expander(f"{emoji} {nombre} - {personas} personas ({adultos_menores})", expanded=False):
                asistencia = resp.get("¿Confirmas tu asistencia?", "Sin confirmar")
                confirmacion_text = {
                    "confirmado": "✅ Confirmado",
                    "incierto": "❓ No está seguro",
                    "no_asiste": "❌ No asistirá",
                    "no_respondido": "⚪ Sin confirmar"
                }
                st.markdown(f"**Asistencia:** {confirmacion_text.get(confirmacion_norm, asistencia)}")

                # Preferencias de comida
                comida_pref = get_field_value(resp, "¿Qué opción prefieres para el almuerzo?", "¿Qué preferimos comer en el asado?") or []
                if comida_pref:
                    items = comida_pref if isinstance(comida_pref, list) else [comida_pref]
                    if items and items != ['']:
                        st.markdown(f"**🍖 Preferencia:** {', '.join(items)}")

                # Cooperación almuerzo
                almuerzo_coop = get_field_value(resp, "¿En qué te gustaría cooperar para el almuerzo?", "¿Cómo puedes cooperar para el almuerzo (asado)?") or []
                if almuerzo_coop:
                    items = almuerzo_coop if isinstance(almuerzo_coop, list) else [almuerzo_coop]
                    # Filtrar "Nada, solo asistiré"
                    items = [item for item in items if "nada" not in str(item).lower() or "asistiré" in str(item).lower()]
                    if items and items != ['']:
                        st.markdown("**💰 Cooperación Almuerzo**")
                        for item in items:
                            st.write(f"• {item}")

                # Cantidad específica de carne
                cantidad_carne = get_field_value(resp, "Si vas a comprar carne, pollo o longaniza, indica qué tipo y qué cantidad podrías aportar (si lo sabes).")
                if cantidad_carne and str(cantidad_carne).strip():
                    st.info(f"📦 {cantidad_carne}")

                comentario_almuerzo = get_field_value(resp, "Comentario adicional para el almuerzo", "Comentario adicional sobre tu aporte para el almuerzo")
                if comentario_almuerzo and str(comentario_almuerzo).strip():
                    st.caption(f"💬 {comentario_almuerzo}")

                # Bebidas
                bebidas = resp.get("¿Qué bebidas prefieres llevar o aportar?") or []
                cantidad_bebidas = resp.get("__bebidas_qty", 0)
                bebidas_items = bebidas if isinstance(bebidas, list) else [bebidas] if bebidas else []
                if (bebidas_items and bebidas_items != ['']) or cantidad_bebidas > 0:
                    st.markdown("**🥤 Bebidas**")
                    if bebidas_items and bebidas_items != ['']:
                        st.write(f"• Tipo: {', '.join(bebidas_items)}")
                    if cantidad_bebidas > 0:
                        st.write(f"• Cantidad: {cantidad_bebidas} unidad(es)")

                # Hora del té
                te = resp.get("¿Qué prefieres aportar para la hora del té?") or []
                if te:
                    items = te if isinstance(te, list) else [te]
                    if items and items != ['']:
                        st.markdown(f"**☕ Hora del té:** {', '.join(items)}")

                comentario_te = resp.get("Comentarios para la hora del té")
                if comentario_te and str(comentario_te).strip():
                    st.caption(f"💬 {comentario_te}")

                # Transporte
                transporte = resp.get("¿Cuál es tu situación con respecto al transporte?")
                cupos = resp.get("__cupos", 0)
                if transporte and str(transporte).strip():
                    st.markdown(f"**🚗 Transporte:** {transporte}")
                    if cupos > 0:
                        st.write(f"   → Cupos disponibles: {cupos}")

                # Horario
                hora = resp.get("¿A qué hora puedes llegar?")
                if hora and str(hora).strip():
                    st.markdown(f"**🕐 Llegada:** {hora}")

                # Extras
                extras = get_field_value(resp, "¿Puedes llevar algo adicional? (sombrillas, juegos, parlante, etc.)", "¿Puedes llevar algo adicional (sombrillas, juegos, parlante, etc.)?")
                if extras and str(extras).strip():
                    st.markdown(f"**➕ Extras:** {extras}")

                # Restricciones
                restricciones = resp.get("¿Tienes alguna restricción alimentaria o preferencia?")
                if restricciones and str(restricciones).strip():
                    st.markdown(f"**⚠️ Restricciones:** {restricciones}")

        # Resumen consolidado
        st.markdown("---")
        st.markdown("### 📋 Consolidado de Aportes")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🍖 Preferencias de Comida**")
            comida_items = {}
            for resp in all_responses:
                items = get_field_value(resp, "¿Qué opción prefieres para el almuerzo?", "¿Qué preferimos comer en el asado?") or []
                item_list = items if isinstance(items, list) else [items] if items else []
                for item in item_list:
                    if item:  # Solo contar items no vacíos
                        comida_items[item] = comida_items.get(item, 0) + 1

            if comida_items:
                for item, count in sorted(comida_items.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"• {item}: {count}")
            else:
                st.info("Sin preferencias registradas")

            st.markdown("")
            st.markdown("**💰 Cooperación Almuerzo**")
            almuerzo_items = {}
            for resp in all_responses:
                items = get_field_value(resp, "¿En qué te gustaría cooperar para el almuerzo?", "¿Cómo puedes cooperar para el almuerzo (asado)?") or []
                item_list = items if isinstance(items, list) else [items] if items else []
                for item in item_list:
                    # Filtrar "Nada, solo asistiré"
                    if item and "nada" not in str(item).lower():
                        almuerzo_items[item] = almuerzo_items.get(item, 0) + 1

            if almuerzo_items:
                for item, count in sorted(almuerzo_items.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"• {item}: {count}")
            else:
                st.info("Sin cooperación registrada")

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

        # Resumen de transporte detallado y mejorado
        st.markdown("---")
        st.markdown("### 🚗 Coordinación de Transporte")

        # Mostrar balance visual
        if necesitan_transporte > 0 or len(ofrecen_cupos) > 0:
            col_balance1, col_balance2, col_balance3 = st.columns(3)

            with col_balance1:
                st.metric("🚗 Ofrecen transporte", len(ofrecen_cupos), help="Personas que pueden llevar a otros")

            with col_balance2:
                st.metric("👥 Necesitan transporte", necesitan_transporte, help="Personas que necesitan que las lleven")

            with col_balance3:
                balance_cupos = total_cupos - personas_necesitan_transporte
                st.metric("📊 Balance",
                         f"{balance_cupos:+d} cupos",
                         delta=None,
                         help="Cupos disponibles menos personas que necesitan")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Ofrecen llevar personas:**")
            if len(ofrecen_cupos) > 0:
                for resp in all_responses:
                    if resp.get("__transporte_tipo") == "ofrece_cupos":
                        nombre = get_field_value(resp, "Nombre completo", "Nombre y apellido", "Nombre") or "Sin nombre"
                        cupos = resp.get("__cupos", 0)
                        hora = resp.get("¿A qué hora puedes llegar?", "")
                        hora_text = f" - Llega: {hora}" if hora and str(hora).strip() else ""
                        st.write(f"✅ **{nombre}**: {cupos} cupo(s){hora_text}")
            else:
                st.info("Nadie ha ofrecido cupos aún")

        with col2:
            st.markdown("**Necesitan transporte:**")
            if necesitan_transporte > 0:
                for resp in all_responses:
                    if resp.get("__transporte_tipo") == "necesita":
                        nombre = get_field_value(resp, "Nombre completo", "Nombre y apellido", "Nombre") or "Sin nombre"
                        personas = resp.get("__num_personas", 1)
                        hora = resp.get("¿A qué hora puedes llegar?", "")
                        hora_text = f" - Prefiere: {hora}" if hora and str(hora).strip() else ""
                        st.write(f"❗ **{nombre}**: {personas} persona(s){hora_text}")
            else:
                st.success("Todos tienen transporte resuelto")

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
        if "edit_mode" not in st.session_state:
            st.session_state.edit_mode = False
        if "edit_doc_id" not in st.session_state:
            st.session_state.edit_doc_id = None
        if "loaded_responses" not in st.session_state:
            st.session_state.loaded_responses = {}

        if st.session_state.submitted:
            st.success("✅ ¡Gracias! Tu respuesta ha sido registrada.")
            st.info("💡 Revisa la pestaña 'Ver Respuestas' para coordinar con los demás.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Enviar otra respuesta", use_container_width=True):
                    st.session_state.submitted = False
                    st.session_state.edit_mode = False
                    st.session_state.edit_doc_id = None
                    st.session_state.loaded_responses = {}
                    st.rerun()
            with col2:
                if st.button("Editar mi respuesta", use_container_width=True):
                    st.session_state.submitted = False
                    st.session_state.edit_mode = True
                    st.rerun()
            st.stop()

        # ===== SECCIÓN DE SELECCIÓN PARA EDITAR =====
        st.markdown("### 📝 Responder o Editar Encuesta")

        # Obtener lista de participantes
        participants = get_all_participant_names()

        if participants and not st.session_state.edit_mode:
            with st.expander("✏️ ¿Ya respondiste? Selecciona tu nombre para editar", expanded=False):
                st.caption("Si ya enviaste tu respuesta y quieres modificarla, selecciona tu nombre:")

                nombres_list = ["-- Respuesta nueva --"] + [p["nombre"] for p in participants]
                selected_name = st.selectbox(
                    "Selecciona tu nombre",
                    nombres_list,
                    key="participant_selector"
                )

                if selected_name == "-- Respuesta nueva --":
                    # Si el usuario vuelve a la opción de nueva respuesta, limpiar modo edición
                    if st.session_state.edit_mode:
                        st.session_state.edit_mode = False
                        st.session_state.edit_doc_id = None
                        st.session_state.loaded_responses = {}
                else:
                    # Cargar automáticamente la respuesta más reciente del participante seleccionado
                    # Evitar recargar si ya está cargada la misma respuesta
                    current_loaded_name = None
                    if st.session_state.get("loaded_responses"):
                        current_loaded_name = get_field_value(
                            st.session_state.loaded_responses,
                            "Nombre completo",
                            "Nombre y apellido",
                            "Nombre"
                        )
                    if not current_loaded_name or (current_loaded_name and current_loaded_name.strip().lower() != selected_name.strip().lower()):
                        doc_id, loaded_resp = load_response_by_name(selected_name)
                        if loaded_resp:
                            st.session_state.edit_mode = True
                            st.session_state.edit_doc_id = doc_id
                            st.session_state.loaded_responses = loaded_resp
                            st.session_state.submitted = False  # Asegurar que no muestre mensaje de enviado
                            st.success(f"✅ Respuesta de {selected_name} cargada. Puedes editarla abajo.")
                            st.rerun()
                        else:
                            st.error("No se pudo cargar la respuesta")

        # Mostrar indicador de modo edición
        if st.session_state.edit_mode:
            nombre_editando = get_field_value(st.session_state.loaded_responses, "Nombre completo", "Nombre y apellido", "Nombre") or "Usuario"
            st.info(f"📝 **Modo Edición** - Editando respuesta de: **{nombre_editando}**")
            if st.button("❌ Cancelar edición"):
                st.session_state.edit_mode = False
                st.session_state.edit_doc_id = None
                st.session_state.loaded_responses = {}
                st.rerun()

        st.markdown("---")

        items = survey.get("items", [])
        responses: Dict[str, Any] = {}

        if not st.session_state.edit_mode:
            st.info("""
            💡 **Consejos para llenar la encuesta:**
            - Para **adultos y menores**, puedes escribir: "2 adultos, 1 menor" o "adultos: 2 menores: 1"
            - Para **cantidad de carne**, indica tipo y peso: "2 kg de vacuno, 1 kg de pollo"
            - Los campos marcados con **\*** son obligatorios
            """)

        transport_selection = None
        cupos_value = None

        with st.form("encuesta_form"):
            for idx, item in enumerate(items):
                title = item.get("title", "")
                # Saltar campo de cupos, se renderiza condicionalmente después
                if title == "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?":
                    continue

                default_val = None
                if st.session_state.edit_mode and st.session_state.loaded_responses:
                    default_val = resolve_default_value(st.session_state.loaded_responses, title)

                response = render_question(item, idx, default_value=default_val)

                if isinstance(response, list):
                    responses[title] = response
                else:
                    responses[title] = response if response is not None else ""

                if title == "¿Cuál es tu situación con respecto al transporte?":
                    transport_selection = responses[title] or ""

                st.markdown("")

            # Campo de cupos solo si ofrece transporte
            if transport_selection and "llevar a otras personas" in str(transport_selection).lower():
                default_cupos = 1
                if st.session_state.edit_mode and st.session_state.loaded_responses:
                    cupos_loaded = get_field_value(
                        st.session_state.loaded_responses,
                        "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?"
                    )
                    if cupos_loaded:
                        cupos_parsed = try_int(cupos_loaded)
                        if isinstance(cupos_parsed, int):
                            default_cupos = cupos_parsed

                cupos_value = st.number_input(
                    "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?",
                    min_value=0,
                    step=1,
                    value=default_cupos,
                    key="dynamic_cupos",
                    help="Indica cuántas personas más podrías transportar en tu vehículo"
                )
                responses["Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?"] = int(cupos_value)
            else:
                responses["Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?"] = ""

            # Submit button con texto dinámico
            button_text = "💾 Actualizar Respuesta" if st.session_state.edit_mode else "📤 Enviar Respuesta"
            submitted = st.form_submit_button(button_text, type="primary", use_container_width=True)

            if submitted:
                errors = []
                for idx, item in enumerate(items):
                    title = item.get("title", "")
                    if title == "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?":
                        continue

                    question_item = item.get("questionItem", {})
                    question = question_item.get("question", {})
                    required = question.get("required", False)
                    val = responses.get(title)

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
                    # Normalizar nombres de campos usando mapeo global
                    normalized_responses = {}
                    for key, value in responses.items():
                        normalized_key = FIELD_NORMALIZATION.get(key, key)
                        normalized_responses[normalized_key] = value
                    responses = normalized_responses

                    # Validación de consistencia
                    total_personas_field = responses.get("¿Cuántas personas en total van contigo?")
                    adultos_menores_field = responses.get("Indica cuántos son ADULTOS y cuántos son MENORES en tu grupo (para calcular comida)")

                    if total_personas_field and adultos_menores_field:
                        total_num = try_int(total_personas_field)
                        adults, minors = parse_adults_minors(adultos_menores_field)

                        if isinstance(total_num, int) and adults is not None and minors is not None:
                            suma_am = (adults or 0) + (minors or 0)
                            if suma_am != total_num:
                                st.warning(f"⚠️ Nota: El total de personas ({total_num}) no coincide con adultos + menores ({suma_am}). Verifica tus respuestas.")

                    # Convertir campos numéricos
                    numeric_fields = [
                        "¿Cuántas personas en total van contigo?",
                        "Si puedes llevar a otras personas, ¿cuántos cupos disponibles tienes?",
                        "¿Cuántas bebidas podrías llevar?"
                    ]
                    for nf in numeric_fields:
                        if nf in responses:
                            responses[nf] = try_int(responses[nf])

                    # Limpiar valores
                    for k, v in list(responses.items()):
                        if isinstance(v, str):
                            responses[k] = v.strip()

                    # Guardar
                    doc_id = st.session_state.edit_doc_id if st.session_state.edit_mode else None
                    success = save_response(responses, doc_id=doc_id)
                    if success or not get_db():
                        st.session_state.submitted = True
                        st.session_state.edit_mode = False
                        st.session_state.edit_doc_id = None
                        st.session_state.loaded_responses = {}
                        st.rerun()

        # Info footer
        st.markdown("---")
        st.caption("🏊 Encuesta Familiar - Día en la Piscina")

if __name__ == "__main__":
    main()
