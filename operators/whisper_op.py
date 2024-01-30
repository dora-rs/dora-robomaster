# Run this in the consol first :

# pip install sounddevice numpy scipy pydub keyboard

# Don't forget to install whisper


import pyarrow as pa
import whisper

from dora import DoraStatus


model = whisper.load_model("base")


class Operator:
    """
    Infering object from images
    """

    def on_event(
        self,
        dora_event,
        send_output,
    ) -> DoraStatus:
        if dora_event["type"] == "INPUT":
            audio = dora_event["value"].to_numpy()
            audio = whisper.pad_or_trim(audio)

            ## make log-Mel spectrogram and move to the same device as the model
            # mel = whisper.log_mel_spectrogram(audio).to(model.device)

            ## decode the audio
            # result = whisper.decode(model, mel, options)
            result = model.transcribe(audio, language="en")
            text = result["text"]

            send_output("text", pa.array([text]), dora_event["metadata"])
        return DoraStatus.CONTINUE
