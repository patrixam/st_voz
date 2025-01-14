import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import av
import io
import wave
import time
import queue
import speech_recognition as sr
from gtts import gTTS


# Configuración de los servidores ICE (STUN y TURN)
rtc_configuration = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {
            "urls": ["turn:relay1.expressturn.com:3478"],
            "username": "efBBNFJF1809NYOOA7",
            "credential": "mFYpag3yUL3bHv9j"
        }
    ]
}

st.title("Demo de Reconocimiento y Síntesis de Voz")
st.markdown("""
Esta aplicación captura audio en tiempo real a través de WebRTC, lo convierte a texto usando la API de Google Speech Recognition y genera una respuesta (con lógica básica) que se sintetiza con pyttsx3.
""")

# Definir la clase AudioProcessor
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        # Aunque en SENDONLY la acumulación directa en self.frames puede no usarse,
        # la dejamos para depuración o usos futuros.
        self.frames = []

    async def recv_queued(self) -> av.AudioFrame:
        frames = []
        while not self.queued_frames.empty():
            frame = await self.queued_frames.get()
            frames.append(frame)
        if frames:
            self.frames.extend(frames)
            # Retorna el último frame para mantener el stream actualizado (no se reproduce en SENDONLY)
            return frames[-1]
        return None

# Inicializar el componente de WebRTC en modo SENDONLY (sin reproducción local)
webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,
    rtc_configuration=rtc_configuration,
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
    audio_receiver_size=1024,
)

# Función para convertir los frames a un archivo WAV en memoria
def frames_to_wav(frames):
    try:
        # Convertir cada frame a un arreglo NumPy y concatenarlos a lo largo de la dimensión del tiempo.
        all_samples = np.concatenate([frame.to_ndarray() for frame in frames], axis=1)
    except Exception as e:
        st.error(f"Error al concatenar frames: {e}")
        return None

    # Obtener parámetros del primer frame (con valores por defecto en caso de fallo)
    sample_rate = frames[0].sample_rate if frames else 48000
    try:
        n_channels = frames[0].layout.channels
        if not n_channels or n_channels < 1:
            raise ValueError("Número de canales no válido")
    except Exception as e:
        st.warning("No se pudo obtener el número de canales, usando 2 por defecto.")
        n_channels = 2

    wav_bytes_io = io.BytesIO()
    try:
        with wave.open(wav_bytes_io, "wb") as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(2)  # 16 bits = 2 bytes
            wf.setframerate(sample_rate)
            # Asegurarse de que los datos sean int16
            if all_samples.dtype != np.int16:
                all_samples = all_samples.astype(np.int16)
            wf.writeframes(all_samples.tobytes())
        wav_bytes_io.seek(0)
        return wav_bytes_io
    except Exception as e:
        st.error(f"Error al crear el archivo WAV: {e}")
        return None

# Función para sintetizar respuesta utilizando pyttsx3 (se ejecuta en el servidor)
def responder(texto):
    # Lógica básica de respuesta:
    if "hola" in texto.lower():
        resp = "¡Hola! ¿Cómo puedo ayudarte?"
    elif "adiós" in texto.lower():
        resp = "Adiós, que tengas un buen día."
    else:
        resp = "No estoy seguro de cómo responder a eso."
    
    # Inicializar el motor de síntesis de voz
    tts = gTTS(resp, lang="es")
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
   # st.audio(audio_bytes, format="audio/mp3")
    # Convertir el audio a base64
    audio_base64 = base64.b64encode(audio_bytes.read()).decode("utf-8")
    # Construir el HTML con la etiqueta <audio> y atributo autoplay.
    html_code = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Tu navegador no soporta la reproducción automática.
        </audio>
    """
    st.markdown(html_code, unsafe_allow_html=True)
    return resp

# Función para procesar el audio y convertirlo a texto
def speech_to_text():
    # Esperar unos segundos para acumular audio (ajusta según necesidad)
    time.sleep(3)
    try:
        frames = webrtc_ctx.audio_receiver.get_frames(timeout=3)
    except queue.Empty:
        st.error("No se recibió audio en el tiempo esperado.")
        return None

    if not frames:
        st.error("No hay frames de audio para procesar.")
        return None

    # Crear archivo WAV a partir de los frames recibidos
    wav_file = frames_to_wav(frames)
    if not wav_file:
        st.error("Error al crear el archivo de audio.")
        return None

    # Usar SpeechRecognition para convertir el audio a texto
    reconocedor = sr.Recognizer()
    try:
        with sr.AudioFile(wav_file) as source:
            audio_data = reconocedor.record(source)
        texto = reconocedor.recognize_google(audio_data, language="es-ES")
        return texto
    except sr.UnknownValueError:
        st.error("No se entendió lo que dijiste.")
        return None
    except sr.RequestError as e:
        st.error(f"Error en el servicio de reconocimiento: {e}")
        return None



# Interfaz de usuario
st.markdown("### Controles de la Aplicación")
if st.button("Hablar"):
    st.info("Grabando audio... Por favor, habla ahora.")
    texto_dicho = speech_to_text()
    if texto_dicho:
        st.write(f"**Dijiste:** {texto_dicho}")
        respuesta_texto = responder(texto_dicho)
        st.write(f"**Respuesta:** {respuesta_texto}")
    else:
        st.error("No se pudo obtener texto del audio.")









