import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import av

rtc_configuration = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},  # Servidor STUN (público)
        {
            "urls": ["turn:tu.turn.server:3478"],      # Servidor TURN
            "username": "tu_usuario",
            "credential": "tu_credencial"
        }
    ]
}

st.title("Prueba de Captura de Audio")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        data = frame.to_ndarray()
        self.frames.append(data)
        return frame

webrtc_ctx = webrtc_streamer(
    key="audio_test",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=rtc_configuration,
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
)

if st.button("Mostrar Frames Capturados"):
    if webrtc_ctx.audio_receiver:
        audio_processor = webrtc_ctx.audio_processor
        if audio_processor and hasattr(audio_processor, 'frames'):
            st.write(f"Frames capturados: {len(audio_processor.frames)}")
        else:
            st.write("No se capturaron frames.")
    else:
        st.write("No hay recepción de audio disponible.")








