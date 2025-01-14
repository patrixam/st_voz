import streamlit as st
import numpy as np
import io
import wave
import av
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings

# Configuración de la conexión WebRTC (usamos un STUN server público)
client_settings = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
)

# Clase que procesa el audio recibido
class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        super().__init__()
        # Aquí acumularemos los _frames_ de audio
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        # Convierte el frame a un arreglo numpy
        frame_data = frame.to_ndarray()
        # Guarda una copia del frame para su procesamiento posterior
        self.frames.append(frame_data.copy())
        # Retorna el mismo frame sin modificar para seguir mostrando el stream
        return frame

st.title("Captura y Reconocimiento de Audio con streamlit-webrtc")

st.markdown("""
Esta aplicación captura audio en tiempo real a través del navegador y, una vez que presionas **Procesar Audio**, combina los datos y ejecuta el reconocimiento de voz usando la API de Google.
""")

# Inicializa el componente de captura de audio
webrtc_ctx = webrtc_streamer(
    key="audio",
    client_settings=client_settings,
    audio_processor_factory=AudioProcessor,
    # Indicamos que el componente debe capturar audio
    mode="sendrecv",
)

# Botón para procesar el audio capturado
if st.button("Procesar Audio"):
    if webrtc_ctx.audio_receiver is not None:
        # Se obtienen los _frames_ de audio recibidos
        audio_frames = webrtc_ctx.audio_receiver.get_frames()
        if audio_frames:
            # Combina los datos de audio (en el eje temporal)
            # Cada frame tiene forma (n_channels, n_samples)
            all_samples = np.concatenate(
                [frame.to_ndarray() for frame in audio_frames], axis=1
            )
            # Usamos el sample_rate y la cantidad de canales del primer frame
            sample_rate = audio_frames[0].sample_rate
            n_channels = audio_frames[0].layout.channels

            # Creamos un archivo WAV en memoria
            wav_bytes_io = io.BytesIO()
            with wave.open(wav_bytes_io, "wb") as wf:
                wf.setnchannels(n_channels)
                # Establecemos el width en 2 bytes (16 bits) asumiendo datos en int16
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                # Aseguramos que los datos sean tipo int16
                if all_samples.dtype != np.int16:
                    all_samples = all_samples.astype(np.int16)
                wf.writeframes(all_samples.tobytes())
            wav_bytes_io.seek(0)

            # Iniciar el reconocedor de voz
            reconocedor = sr.Recognizer()
            with sr.AudioFile(wav_bytes_io) as source:
                audio_data = reconocedor.record(source)
            try:
                # Reconocimiento de voz usando la API de Google (en español)
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


