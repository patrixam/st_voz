import streamlit as st
import numpy as np
import io
import wave
import av
import speech_recognition as sr
from gtts import gTTS
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode

st.title("Captura y Reconocimiento de Audio con streamlit-webrtc")
st.markdown("""
Esta aplicación captura audio en tiempo real desde el navegador.
- Usa **Nueva Grabación** para reiniciar la captura.
- Usa **Procesar Audio** para obtener la transcripción y generar una respuesta de voz.
""")

# --- Función para sintetizar texto y retornar un objeto BytesIO con audio MP3 ---
def sintetizar_texto_bytes(texto):
    tts = gTTS(texto, lang="es")
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

# --- Inicializar un contador en session_state para generar un key dinámico ---
if "record_count" not in st.session_state:
    st.session_state.record_count = 0

# --- Clase que acumula los frames de audio ---
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        self.frames = []  # Acumula los frames de audio

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # Convertir el frame a un array numpy y acumularlo
        self.frames.append(frame.to_ndarray())
        return frame

# --- Área de botones en dos columnas ---
col1, col2 = st.columns(2)

with col1:
    if st.button("Nueva Grabación"):
        # Incrementa el contador para generar un nuevo key (reinicia el componente)
        st.session_state.record_count += 1

with col2:
    process_clicked = st.button("Procesar Audio")

# --- Inicializar (o reinicializar) el componente de captura de audio con un key dinámico ---
webrtc_ctx = webrtc_streamer(
    key=f"speech-to-text_{st.session_state.record_count}",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
)

# --- Al pulsar "Procesar Audio", se procesa el audio acumulado ---
if process_clicked:
    if webrtc_ctx.audio_receiver is not None:
        # Obtener todos los frames acumulados
        audio_frames = webrtc_ctx.audio_receiver.get_frames()
        if audio_frames:
            # Combinar los datos de audio a lo largo del eje temporal
            # Cada frame es un array; se concatenan horizontalmente.
            all_samples = np.concatenate(
                [frame.to_ndarray() for frame in audio_frames], axis=1
            )
            sample_rate = audio_frames[0].sample_rate
            n_channels = audio_frames[0].layout.channels

            # Crear un archivo WAV en memoria con los datos combinados
            wav_bytes_io = io.BytesIO()
            with wave.open(wav_bytes_io, "wb") as wf:
                wf.setnchannels(n_channels)
                wf.setsampwidth(2)  # 16 bits => 2 bytes
                wf.setframerate(sample_rate)
                if all_samples.dtype != np.int16:
                    all_samples = all_samples.astype(np.int16)
                wf.writeframes(all_samples.tobytes())
            wav_bytes_io.seek(0)

            # Reconocimiento de voz usando SpeechRecognition y Google Speech API
            reconocedor = sr.Recognizer()
            with sr.AudioFile(wav_bytes_io) as source:
                audio_data = reconocedor.record(source)
            try:
                texto = reconocedor.recognize_google(audio_data, language="es-ES")
                st.session_state["texto"] = texto
                st.success(f"Texto reconocido: **{texto}**")
            except sr.UnknownValueError:
                st.error("No se entendió lo que dijiste.")
                st.session_state["texto"] = ""
            except sr.RequestError as e:
                st.error(f"Error en el servicio de reconocimiento: {e}")
                st.session_state["texto"] = ""
        else:
            st.warning("No se recibieron datos de audio. Asegúrate de grabar correctamente.")
    else:
        st.warning("La recepción de audio no está disponible.")

# --- Si se obtuvo texto reconocido, generar respuesta y síntesis de voz ---
if "texto" in st.session_state and st.session_state["texto"]:
    st.write(f"**Dijiste:** {st.session_state['texto']}")
    
    # Lógica básica de respuesta según el texto reconocido
    if "hola" in st.session_state["texto"].lower():
        respuesta = "¡Hola! ¿Cómo estás?"
    elif "adiós" in st.session_state["texto"].lower():
        respuesta = "Adiós, que tengas un buen día."
    else:
        respuesta = "No estoy seguro de cómo responder a eso."
    
    st.write(f"**Respuesta:** {respuesta}")
    
    # Realizar la síntesis de voz en memoria
    audio_bytes = sintetizar_texto_bytes(respuesta)
    st.audio(audio_bytes, format="audio/mp3")






