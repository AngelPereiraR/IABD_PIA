import streamlit as st
import time
from motor_rag import TeaRagEngine

# --- CONFIGURACIÓN ---
FECHA_ACTUALIZACION = "10 de noviembre de 2025" # Actualizar esta fecha según tu recopilación real
# ---------------------

# Configuración de la página
st.set_page_config(
    page_title="Asistente TEA Andalucía",
    page_icon="🧩",
    layout="wide"
)

# --- BARRA LATERAL: AVISOS IMPORTANTES ---
with st.sidebar:
    st.header("⚠️ AVISO IMPORTANTE")
    
    st.info(
        "**HERRAMIENTA INFORMATIVA**\n\n"
        "Este asistente utiliza inteligencia artificial para facilitar el acceso a la información. "
        "**NO sustituye el asesoramiento profesional** de trabajadores sociales, abogados o personal de la administración pública."
    )
    
    st.warning(
        f"**ACTUALIZACIÓN NORMATIVA**\n\n"
        f"La documentación base fue recopilada hasta: **{FECHA_ACTUALIZACION}**.\n"
        "La normativa puede haber cambiado. Verifica siempre los trámites en las sedes oficiales enlazadas."
    )
    
    st.success(
        "**ACCESIBILIDAD**\n\n"
        "El asistente está diseñado para responder con un lenguaje claro, sencillo y respetuoso, "
        "pensando en la diversidad de las familias."
    )
    
    st.divider()
    st.caption("Basado en documentación oficial de la Junta de Andalucía y BOE.")

# --- INTERFAZ PRINCIPAL ---

# Título y descripción
st.title("🧩 Asistente Virtual TEA Andalucía")
st.markdown("""
Bienvenido/a. Estoy aquí para responder tus dudas sobre **trámites, ayudas y derechos** relacionados con el TEA en Andalucía. 
Mis respuestas se basan exclusivamente en guías y normativas oficiales.
""")

# --- Inicialización del Motor RAG (solo una vez) ---
@st.cache_resource(show_spinner=False) # Cachear para no recargar el modelo en cada interacción
def load_rag_engine():
    try:
        return TeaRagEngine()
    except Exception as e:
        st.error(f"No se pudo iniciar el motor de Inteligencia Artificial.\nError: {e}")
        return None

with st.spinner("Iniciando el motor de búsqueda normativa..."):
    rag_engine = load_rag_engine()

if not rag_engine:
    st.warning("Por favor, verifica que el archivo .env contiene la GEMINI_API_KEY correcta y reinicia la aplicación.")
    st.stop()

# --- Historial de Chat ---

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hola. ¿En qué trámite o ayuda puedo orientarte hoy?"}
    ]

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Si el mensaje tiene fuentes asociadas, mostrarlas en un expansor
        if "sources" in message and message["sources"]:
             with st.expander("📚 Ver fuentes documentales consultadas"):
                for i, doc in enumerate(message["sources"]):
                    meta = doc.metadata
                    source_title = meta.get('title', meta.get('source_file', 'Documento sin título'))
                    source_type = meta.get('type', 'Documento').upper()
                    
                    st.markdown(f"**{i+1}. {source_title}** ({source_type})")
                    
                    # Mostrar un pequeño fragmento del texto usado (opcional, a veces ayuda a dar confianza)
                    # Limpiamos saltos de línea excesivos para que se vea mejor
                    clean_snippet = doc.page_content[:150].replace('\n', ' ')
                    st.caption(f"Fragmento: \"...{clean_snippet}...\"")
                    
                    if 'original_url' in meta and meta['original_url'] and meta['original_url'] != 'N/A':
                         st.markdown(f"🔗 [Acceder al documento original]({meta['original_url']})")
                    
                    if i < len(message["sources"]) - 1:
                        st.divider()

# --- Input del usuario ---
if prompt := st.chat_input("Escribe tu duda aquí (ej. ¿Qué pasos sigo para la Atención Temprana?)"):
    # 1. Mostrar pregunta usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta asistente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("🔍 Consultando la normativa oficial..."):
            try:
                # Llamada al motor RAG
                response_data = rag_engine.get_answer(prompt)
                full_response = response_data["answer"]
                source_docs = response_data["source_documents"]
                
                # Simulación de escritura (stream) - opcional pero queda bien
                displayed_response = ""
                for chunk in full_response.split():
                    displayed_response += chunk + " "
                    time.sleep(0.02) # Ajustar velocidad
                    message_placeholder.markdown(displayed_response + "▌")
                message_placeholder.markdown(full_response)
                
                # Mostrar fuentes usadas en esta respuesta inmediatamente
                if source_docs:
                    with st.expander("📚 Fuentes consultadas para esta respuesta"):
                        for i, doc in enumerate(source_docs):
                            meta = doc.metadata
                            # Usar título si existe, si no el nombre del archivo
                            source_title = meta.get('title', meta.get('source_file', 'Documento'))
                            source_type = meta.get('type', 'Info').upper()
                            
                            st.markdown(f"**[{i+1}] {source_title}**")
                            # Badge o etiqueta de tipo
                            st.caption(f"Tipo: {source_type}")
                            
                            if 'original_url' in meta and meta['original_url'] and meta['original_url'].startswith('http'):
                                 st.markdown(f"🔗 [Ver documento oficial]({meta['original_url']})")
                            
                            if i < len(source_docs) - 1:
                                st.divider()

            except Exception as e:
                full_response = f"😔 Lo siento, ha ocurrido un error técnico al procesar tu consulta. Por favor, inténtalo de nuevo en unos instantes.\n\nDetalle del error (para soporte): `{e}`"
                message_placeholder.error(full_response)
                source_docs = []

    # 3. Guardar respuesta en el historial
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response,
        "sources": source_docs
    })