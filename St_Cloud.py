import streamlit as st
import numpy as np
import io
import wave
import av
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

st.title("Captura y Reconocimiento de Audio con streamlit-webrtc")
st.markdown("""
Esta aplicación captura audio en tiempo real desde el navegador y, al pulsar **Procesar Audio**, lo combina para ejecutar el reconocimiento de voz usando la API de Google.
""")

# Clase que procesa el audio recibido
class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        super().__init__()
        # Acumulamos los frames de audio
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # Convertir el frame a un arreglo numpy
        frame_data = frame.to_ndarray()
        # Guardamos una copia del frame para procesarlo posteriormente
        self.frames.append(frame_data.copy())
        # Retornamos el frame sin modificar para seguir mostrando el stream
        return frame

# Inicializa el componente de captura de audio usando la nueva sintaxis
webrtc_ctx = webrtc_streamer(
    key="audio",
    mode="sendrecv",
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
)

if st.button("Procesar Audio"):
    if webrtc_ctx.audio_receiver is not None:
        # Se obtienen los frames de audio recibidos
        audio_frames = webrtc_ctx.audio_receiver.get_frames()
        if audio_frames:
            # Se concatenan los datos de audio (en eje temporal)
            all_samples = np.concatenate(
                [frame.to_ndarray() for frame in audio_frames], axis=1
            )
            sample_rate = audio_frames[0].sample_rate
            n_channels = audio_frames[0].layout.channels

            # Crear un archivo WAV en memoria
            wav_bytes_io = io.BytesIO()
            with wave.open(wav_bytes_io, "wb") as wf:
                wf.setnchannels(n_channels)
                wf.setsampwidth(2)  # 16 bits = 2 bytes
                wf.setframerate(sample_rate)
                if all_samples.dtype != np.int16:
                    all_samples = all_samples.astype(np.int16)
                wf.writeframes(all_samples.tobytes())
            wav_bytes_io.seek(0)

            # Reconocimiento de voz
            reconocedor = sr.Recognizer()
            with sr.AudioFile(wav_bytes_io) as source:
                audio_data = reconocedor.record(source)
            try:
                texto = reconocedor.recognize_google(audio_data, language="es-ES")
                st.success(f"Reconocido: **{texto}**")
            except sr.UnknownValueError:
                st.error("No se entendió lo que dijiste.")
            except sr.RequestError as e:
                st.error(f"Error en el servicio de reconocimiento: {e}")
        else:
            st.warning("No se recibieron datos de audio. Por favor, graba algo antes de procesar.")
    else:
        st.warning("La recepción de audio no está disponible.")



