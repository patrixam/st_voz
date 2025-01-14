import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import speech_recognition as sr
import pyttsx3
import logging

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)

# Clase para procesar audio
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        logging.info("AudioProcessor iniciado")
        self.recognizer = sr.Recognizer()
        self.result = None

    def recv(self, frame):
        # Procesar un solo frame de audio
        logging.debug("Procesando frame de audio...")
        audio_data = frame.to_ndarray().tobytes()
        audio = sr.AudioData(audio_data, frame.sample_rate, 2)
        try:
            self.result = self.recognizer.recognize_google(audio, language="es-ES")
        except sr.UnknownValueError:
            self.result = "No se entendió lo que dijiste."
        except sr.RequestError as e:
            self.result = f"Error en el servicio de reconocimiento: {e}"

# Función para sintetizar texto a voz
def sintetizar_texto(texto):
    logging.info("Sintetizando texto a voz")
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    engine.say(texto)
    engine.runAndWait()
    engine.stop()

# Interfaz principal de Streamlit
st.title("Reconocimiento y Síntesis de Voz con Streamlit")
st.write("Pulsa el botón para hablar.")

logging.info("App iniciada")

# Streamer de WebRTC
state = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=False,  # Procesamiento síncrono para evitar problemas de contexto
    key_params={"reset_connection": True}  # Reinicia correctamente la conexión
)

# Mostrar resultados del reconocimiento y responder
if state and state.audio_processor and state.audio_processor.result:
    texto_dicho = state.audio_processor.result
    st.write(f"Dijiste: **{texto_dicho}**")

    # Lógica de respuesta
    if "hola" in texto_dicho.lower():
        respuesta = "¡Hola! ¿Cómo puedo ayudarte?"
    elif "adiós" in texto_dicho.lower():
        respuesta = "Adiós, que tengas un buen día."
    else:
        respuesta = "No estoy seguro de cómo responder a eso."

    st.write(f"Respuesta: **{respuesta}**")

    # Sintetizar respuesta
    sintetizar_texto(respuesta)

    # Limpiar el resultado para permitir nuevas grabaciones
    state.audio_processor.result = None


