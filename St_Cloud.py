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
status_indicator = st.empty()

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
            self.frames.extend(frames)
            print(f"Se han recibido {len(frames)} frames en esta tanda.")
            return frames[-1]
        return None


webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,
    rtc_configuration=rtc_configuration,
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
    audio_receiver_size=1024,
)

if st.button("Mostrar Frames Capturados"):
    status_indicator.write("Loading...")
    if webrtc_ctx.audio_receiver:
        try:
            audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
        except queue.Empty:
            time.sleep(0.1)
            status_indicator.write("No frame arrived.")
            continue
            
        if audio_processor and hasattr(audio_processor, 'frames'):
            st.write(f"Frames capturados: {len(audio_processor.frames)}")
        else:
            st.write("No se capturaron frames.")
    else:
        st.write("No hay recepción de audio disponible.")


if st.button("Ver Estado del Receptor de Audio"):
    st.write("Audio Receiver:", webrtc_ctx.audio_receiver)
    st.write("Frames:", webrtc_ctx.audio_processor.frames)
    st.write("Frames2:",audio_frames)
    st.write("Atributos disponibles:", dir(webrtc_ctx))









