import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import speech_recognition as sr
import pyttsx3
import os
from pydub import AudioSegment

# Inicializar el motor de síntesis de voz
def sintetizar_texto(texto):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    
    # Crear archivo temporal
    archivo_temporal = "respuesta.mp3"
    engine.save_to_file(texto, archivo_temporal)
    engine.runAndWait()
    
    return archivo_temporal

# Procesador de audio personalizado para usar speech_recognition
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def recv(self, frame):
        # Convertir el audio capturado a formato compatible con speech_recognition
        audio_data = sr.AudioData(frame.to_ndarray().tobytes(), frame.sample_rate, 2)
        try:
            texto = self.recognizer.recognize_google(audio_data, language="es-ES")
            st.session_state["texto"] = texto
        except sr.UnknownValueError:
            st.session_state["texto"] = "No se entendió lo que dijiste."
        except sr.RequestError as e:
            st.session_state["texto"] = f"Error en el servicio: {e}"
        return frame

# Configuración de Streamlit
st.title("Demo Reconocimiento y Síntesis de Voz en la Nube")

# Captura de audio
webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

# Mostrar resultados y manejar respuesta
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
