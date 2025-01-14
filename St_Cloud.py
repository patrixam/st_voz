import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import speech_recognition as sr
import pyttsx3

# Clase para procesar audio
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.result = None

    def recv_queued(self, frames, sample_rate):
        # Combinar frames en un solo buffer
        audio_data = b"".join(frame.to_ndarray().tobytes() for frame in frames)

        # Procesar audio con speech_recognition
        audio = sr.AudioData(audio_data, sample_rate, 2)
        try:
            self.result = self.recognizer.recognize_google(audio, language="es-ES")
        except sr.UnknownValueError:
            self.result = "No se entendió lo que dijiste."
        except sr.RequestError as e:
            self.result = f"Error en el servicio de reconocimiento: {e}"

# Función para sintetizar texto a voz
def sintetizar_texto(texto):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    engine.say(texto)
    engine.runAndWait()
    engine.stop()

# Interfaz principal de Streamlit
st.title("Reconocimiento y Síntesis de Voz con Streamlit")

st.write("Pulsa el botón para hablar.")

# Streamer de WebRTC
state = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,  # Procesamiento asíncrono para evitar bloqueos
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

