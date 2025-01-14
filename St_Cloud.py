import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import av

rtc_configuration = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},  # Servidor STUN (público)
        {
            "urls": ["turn:relay1.expressturn.com:3478"],  # Tu servidor TURN
            "username": "efBBNFJF1809NYOOA7",
            "credential": "mFYpag3yUL3bHv9j"
        }
    ]
}

st.title("Prueba de Captura de Audio")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        self.frames = []

    async def recv_queued(self) -> av.AudioFrame:
        """
        Esta función se encarga de consumir todos los frames disponibles en la cola
        y acumularlos en self.frames. Se retorna el último frame recibido para mantener
        el stream visible.
        """
        frames = []
        while not self.queued_frames.empty():
            frame = await self.queued_frames.get()
            frames.append(frame)
        if frames:
            # Acumula todos los frames recibidos en esta tanda
            self.frames.extend(frames)
            # Retorna el último frame para la actualización del stream en la interfaz
            return frames[-1]
        # Si no hay frames, retornamos None
        return None

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








