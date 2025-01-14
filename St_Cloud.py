import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import av
import io
import wave
import time
import queue
import speech_recognition as sr

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

st.title("Speech-to-Text usando streamlit-webrtc")
st.markdown("""
Esta aplicación captura audio en tiempo real (modo **SENDONLY**) y utiliza los frames recibidos para
convertir el audio a texto mediante la API de Google Speech Recognition.
""")

# --- Clase de AudioProcessor (aunque en SENDONLY los frames se reciben mediante audio_receiver)
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        # Aunque en modo SENDONLY puede no acumularse en este atributo,
        # lo dejamos por si en algún futuro se necesita.
        self.frames = []

    async def recv_queued(self) -> av.AudioFrame:
        frames = []
        while not self.queued_frames.empty():
            frame = await self.queued_frames.get()
            frames.append(frame)
        if frames:
            self.frames.extend(frames)
            # Retorna el último frame para actualizar el stream (aunque no se reproduzca)
            return frames[-1]
        return None

# Inicializamos el componente con SENDONLY (sin reproducción de audio local)
webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,
    rtc_configuration=rtc_configuration,
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
    audio_receiver_size=1024,
)

st.markdown("### Controles")

if st.button("Ver Estado de Audio"):
    # Intentamos obtener frames del receptor
    try:
        # Esperamos unos segundos para acumular audio
        time.sleep(2)
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=2)
    except queue.Empty:
        st.write("No se recibieron frames en el tiempo esperado.")
        audio_frames = []

    st.write("Frames (audio_receiver.get_frames()):", audio_frames)
    st.write("Total de frames recibidos:", len(audio_frames))

# Botón para ejecutar el Speech-to-Text
if st.button("Convertir Audio a Texto"):
    try:
        # Esperamos unos segundos para asegurarnos de haber acumulado audio
        time.sleep(2)
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=2)
    except queue.Empty:
        st.error("No se recibió audio en el tiempo esperado.")
        audio_frames = []

    if audio_frames:
        try:
            # Concatenar todos los frames a lo largo del eje 1.
            all_samples = np.concatenate([frame.to_ndarray() for frame in audio_frames], axis=1)
        except Exception as e:
            st.error(f"Error al concatenar frames: {e}")
            all_samples = None
    
        if all_samples is not None:
            # Obtener el sample_rate del primer frame y tratar de obtener los canales.
            sample_rate = audio_frames[0].sample_rate if audio_frames else 48000
            
            # Intentamos extraer el número de canales. 
            # Si no está definido o es 0, usamos 2 como valor por defecto.
            try:
                n_channels = audio_frames[0].layout.channels
                if not n_channels or n_channels < 1:
                    raise ValueError("Número de canales no válido")
            except Exception as e:
                st.warning("No se pudo obtener el número de canales, usando 2 canales por defecto.")
                n_channels = 2
    
            # Crear un archivo WAV en memoria
            wav_bytes_io = io.BytesIO()
            try:
                with wave.open(wav_bytes_io, "wb") as wf:
                    wf.setnchannels(n_channels)
                    wf.setsampwidth(2)  # 16 bits => 2 bytes
                    wf.setframerate(sample_rate)
                    if all_samples.dtype != np.int16:
                        all_samples = all_samples.astype(np.int16)
                    wf.writeframes(all_samples.tobytes())
                wav_bytes_io.seek(0)
                st.success("Archivo WAV generado con éxito.")
            except Exception as e:
                st.error(f"Error al crear el archivo WAV: {e}")
                wav_bytes_io = None

            if wav_bytes_io:
                # Reconocimiento de voz con SpeechRecognition
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_bytes_io) as source:
                    audio_data = recognizer.record(source)
                try:
                    # Ajusta el parámetro 'language' según sea necesario (por ejemplo, "es-ES" para español)
                    text = recognizer.recognize_google(audio_data, language="es-ES")
                    st.success("Texto reconocido:")
                    st.write(text)
                except sr.UnknownValueError:
                    st.error("No se pudo entender el audio.")
                except sr.RequestError as e:
                    st.error(f"Error en el servicio de reconocimiento: {e}")
    else:
        st.error("No hay frames de audio para procesar.")








