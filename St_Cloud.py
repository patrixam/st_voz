import streamlit as st
import numpy as np
import io
import wave
import av
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode

st.title("Captura y Reconocimiento de Audio con streamlit-webrtc")
st.markdown("""
Esta aplicación captura audio en tiempo real desde el navegador.  
Usa **Nueva Grabación** para reiniciar la captura y **Procesar Audio** para obtener la transcripción.
""")

# Inicializar contador en session_state para la llave del componente, si aún no existe.
if "record_count" not in st.session_state:
    st.session_state.record_count = 0

# Clase que procesa el audio recibido
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.reconocedor = sr.Recognizer()

    def recv(self, frame):
        # Convertir el audio capturado a formato compatible con speech_recognition
        audio_data = sr.AudioData(frame.to_ndarray().tobytes(), frame.sample_rate, 2)
        try:
            texto = self.reconocedor.recognize_google(audio_data, language="es-ES")
            st.success(f"Reconocido: **{texto}**")
        except sr.UnknownValueError:
            st.error("No se entendió lo que dijiste.")
        except sr.RequestError as e:
            st.error(f"Error en el servicio de reconocimiento: {e}")
        return frame

# Mostrar dos columnas para los botones
col1, col2 = st.columns(2)

with col1:
    if st.button("Nueva Grabación"):
        # Incrementa el contador, provocando que se asigne un nuevo key
        st.session_state.record_count += 1

with col2:
    process_clicked = st.button("Procesar Audio")

# Inicializa (o reinicializa) el componente de captura de audio usando un key dinámico
webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
)

if process_clicked:
    if "texto" in st.session_state:
        st.write(f"Dijiste: {st.session_state['texto']}")
        
        # Generar respuesta
        if "hola" in st.session_state["texto"].lower():
            respuesta = "¡Hola! ¿Cómo estás?"
        elif "adiós" in st.session_state["texto"].lower():
            respuesta = "Adiós, que tengas un buen día."
        else:
            respuesta = "No estoy seguro de cómo responder a eso."
        
        st.write(f"Respuesta: {respuesta}")
        
        # Generar síntesis de voz y reproducir
        archivo_respuesta = sintetizar_texto(respuesta)
        st.audio(archivo_respuesta)
    
        # Eliminar archivo temporal después de reproducir
        if os.path.exists(archivo_respuesta):
            os.remove(archivo_respuesta)
    else:
        st.warning("La recepción de audio no está disponible.")





