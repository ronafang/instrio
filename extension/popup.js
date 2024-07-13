document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-recording');
    const stopButton = document.getElementById('stop-recording');
    const volumeControl = document.getElementById('volume-control');
    const volumeLabel = document.getElementById('volume-label');


    startButton.addEventListener('click', function(event) {
        event.preventDefault(); 
        event.stopPropagation(); 
        chrome.runtime.sendMessage({ action: 'startRecording' });
    });

    stopButton.addEventListener('click', function(event) {
        event.preventDefault(); 
        event.stopPropagation(); 
        chrome.runtime.sendMessage({ action: 'stopRecording' });
    });


    volumeControl.oninput = () => {
        const volume = parseFloat(volumeControl.value);
        const percentage = Math.round(volume * 100);
        volumeLabel.textContent = `Volume: ${percentage}%`;
        chrome.runtime.sendMessage({ action: 'setVolume', volume: volume });
    };

    // Set initial volume label
    volumeLabel.textContent = 'Volume: 100%';


    // Request initial button state
    chrome.runtime.sendMessage({ action: 'getInitialState' });
});