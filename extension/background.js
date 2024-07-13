let mediaStream;
let recorder;
let currentSourceNode = null;
let audioBuffers = [];
let playback = false;
let audioContext;
let gainNode;
let volume = 1;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'startRecording') {
        if (playback) {
            stopRecordingHandler(); // stop current stream
        }
        startRecordingHandler();
    } else if (message.action === 'stopRecording') {
        stopRecordingHandler();
    } else if (message.action === 'setVolume') {
        setVolume(message.volume);
    }
});

async function startRecordingHandler() {
    try {
        playback = true;
        chrome.tabCapture.capture({ video: true, audio: true }, (stream) => {
            if (chrome.runtime.lastError) {
                console.error(chrome.runtime.lastError);
                return;
            }
            mediaStream = stream;

            const audioTracks = mediaStream.getAudioTracks();
            if (audioTracks.length === 0) {
                console.error("No audio track found in screen capture");
                return;
            }
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            gainNode = audioContext.createGain();
            gainNode.connect(audioContext.destination);
            setVolume(volume);

            startRecording(mediaStream);
        });

    } catch (error) {
        console.error("Error capturing tab audio:", error);
    }
}

function playBuffer() {
    if (audioBuffers.length > 0 && playback) {
        const buffer = audioBuffers.shift();
        const sourceNode = audioContext.createBufferSource();
        sourceNode.buffer = buffer;
        sourceNode.connect(gainNode);

        const currentTime = audioContext.currentTime;
        sourceNode.start(currentTime);
        currentSourceNode = sourceNode;

        sourceNode.onended = () => {
            currentSourceNode = null;
            playBuffer();
        };
    }
}

function startRecording(stream) {
    recorder = new RecordRTC(stream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: StereoAudioRecorder,
        timeSlice: 5000,
        ondataavailable: async (blob) => {
            try {
                console.log("new audio")
                processAudio(blob);
            } catch (error) {
                console.error('Error processing audio:', error);
            }
        }
    });
    recorder.startRecording();
}

async function stopRecordingHandler() {
    playback = false;
    console.log("stop playback");
    if (recorder) {
        recorder.stopRecording(() => {
            let blob = recorder.getBlob();
        });
    }
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
    }
}

async function processAudio(blob) {
    console.log("calling process audio")
    try {
        const formData = new FormData();
        formData.append('file', blob, 'audio.wav');
        const response = await fetch('https://api.instr.io:8000/convert', {
            method: 'PUT',
            body: formData
        });

        if (response.ok) {
            console.log('Processed audio retrieved.');
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

            audioBuffers.push(audioBuffer);

            if (!currentSourceNode) {
                playBuffer();
            }
        } else {
            console.error('Failed to process audio.');
        }

    } catch (error) {
        console.error('Error during the processing', error);
    }
}

function setVolume(newVolume) {
    volume = newVolume;
    if (gainNode) {
        gainNode.gain.setValueAtTime(volume, audioContext.currentTime);
    }
}

function blobToArrayBuffer(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsArrayBuffer(blob);
    });
}