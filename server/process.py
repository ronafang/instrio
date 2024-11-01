from demucs.apply import apply_model
from demucs import pretrained
from io import BytesIO
import random
import torch
import torchaudio
import soundfile as sf
import os
import boto3
from dotenv import load_dotenv
import time
import gc

load_dotenv()

model = pretrained.get_model('hdemucs_mmi')
if torch.cuda.is_available():
    model = model.to("cuda")

def ogg_to_tensor(ogg_data):
    waveform, sample_rate = sf.read(ogg_data, dtype='float32')
    waveform = torch.tensor(waveform).transpose(0, 1)
    if torch.cuda.is_available():
        waveform = waveform.to('cuda')
    return waveform, sample_rate

def convert_tensor_to_ogg(tensor, sample_rate):
    buffer = BytesIO()
    torchaudio.save(buffer, tensor, sample_rate, format='ogg')    
    buffer.seek(0)
    return buffer

def combine_audio_tensors(audio_tensors):
    combined_tensor = sum(audio_tensors)
    combined_tensor /= len(audio_tensors)
    return combined_tensor

def process(ogg_data):
    with torch.no_grad():
        tensor, fs = ogg_to_tensor(ogg_data)
        start_time = time.time()
        out = apply_model(model, tensor.unsqueeze(0))[0]
        end_time = time.time()
        print("took", end_time-start_time, "seconds")
        instr = combine_audio_tensors(out[:-1])
        instr2 = instr.cpu()
        instr_buffer = convert_tensor_to_ogg(instr2, fs)

        del tensor
        del out
        del instr
        del instr2
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        gc.collect()

    return instr_buffer