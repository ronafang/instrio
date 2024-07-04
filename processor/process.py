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

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')

s3_client = boto3.client('s3', region_name=AWS_REGION)

model = pretrained.get_model('htdemucs_ft')

def wav_to_tensor(wav_data):
    wav_io = BytesIO(wav_data)
    waveform, sample_rate = sf.read(wav_io, dtype='float32')
    waveform = torch.tensor(waveform).transpose(0, 1)
    return waveform, sample_rate

def convert_tensor_to_wav(tensor, sample_rate):
    buffer = BytesIO()
    torchaudio.save(buffer, tensor, sample_rate, format='wav')    
    buffer.seek(0)
    return buffer

def upload_to_s3(buffer, s3_key):
    try:
        s3_client.upload_fileobj(buffer, S3_BUCKET, s3_key)
        print(f"Successfully uploaded to {s3_key}")
    except Exception as e:
        print(f"Failed to upload to {s3_key}: {e}")

def combine_audio_tensors(audio_tensors):
    combined_tensor = sum(audio_tensors)
    combined_tensor /= len(audio_tensors)
    
    return combined_tensor

def process(wav_data, task_key):
    task = task_key[len("input/"):-len(".wav")]
    tensor, fs = wav_to_tensor(wav_data)
    out = apply_model(model, tensor.unsqueeze(0))[0]
    instr = combine_audio_tensors(out[:-1])
    instr_buffer = convert_tensor_to_wav(instr, fs)
    upload_to_s3(instr_buffer, f"output/{task}.wav")