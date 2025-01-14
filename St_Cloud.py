import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import numpy as np
import av
import time
import queue

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

st.title("Prueba de Captura de Audio")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        self.frames = []

    async def recv_queued(self) -> av.AudioFrame:
        frames = []
        while not self.queued_frames.empty():
            frame = await self.queued_frames.get()
            frames.append(frame)
        if frames:
            # Opcional: para debug, imprime en la terminal
            print(f"Se han recibido {len(frames)} frames en esta tanda.")
            self.frames.extend(frames)
            return frames[-1]
        return None

webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,  # O prueba SENDRECV para comparar
    rtc_configuration=rtc_configuration,
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
    audio_receiver_size=1024,
)

if st.button("Ver Estado del Receptor de Audio"):
    try:
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
    except queue.Empty:
        time.sleep(0.1)
        st.write("No frame arrived.")
        audio_frames = []
    st.write("Frames obtenidos de audio_receiver.get_frames():", audio_frames)
    # Muestra la cantidad de frames acumulados en tu AudioProcessor
    if webrtc_ctx.audio_processor and hasattr(webrtc_ctx.audio_processor, "frames"):
        st.write(f"Frames acumulados en audio_processor.frames: {len(webrtc_ctx.audio_processor.frames)}")
    else:
        st.write("No se han acumulado frames en audio_processor.")









