# Live Audio Stream Waterfall Analyzer

This repository contains a Python application designed to fetch and analyze live audio streams, generating a real-time waterfall spectrogram display accessible via a web interface. It was initially developed with potential applications for SAAO IO (South African Astronomical Observatory Internet Observatory/Input-Output) monitoring in mind but can be adapted for various audio stream sources.

The application uses Flask for the web server, Flask-SocketIO for real-time communication, Matplotlib for plotting, NumPy/SciPy for signal processing, and Requests for fetching the audio stream.

![Placeholder Screenshot](https://via.placeholder.com/800x400.png?text=Add+Screenshot+Here)
*(Suggestion: Replace the placeholder above with an actual screenshot or GIF of the running application)*

## Features

*   **Live Audio Streaming:** Fetches audio data from a specified URL.
*   **Real-time Spectrogram:** Generates a waterfall plot (spectrogram) updated in real-time.
*   **Web Interface:** Provides a browser-based dashboard using Flask and SocketIO to view the waterfall display.
*   **Configurable:** Settings for audio stream parameters, FFT processing, and display options are managed via a `config.ini` file.
*   **Interactive Controls:** Adjust visualization parameters directly from the web interface:
    *   FFT Window Size
    *   Frequency Range (Min/Max)
    *   Color Scheme
    *   Contrast
    *   Time Window (duration displayed)
    *   Refresh Rate
*   **Optional Audio Playback:** Can play the incoming audio stream locally using `sounddevice` (toggleable via UI).
*   **Dynamic Plot Scaling:** Automatically adjusts the color intensity range based on the data.
*   **Configuration Update via UI:** Allows updating core stream settings (URL, Sample Rate) via the UI (requires application restart).

## Requirements

*   Python 3.x
*   Flask
*   Flask-SocketIO
*   NumPy
*   Matplotlib
*   SciPy
*   Requests
*   SoundDevice (Optional, only needed for audio playback feature)
*   A web browser supporting WebSockets.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    Flask
    Flask-SocketIO
    numpy
    matplotlib
    scipy
    requests
    sounddevice  # Optional: remove if you don't need audio playback
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```
    *Note:* `sounddevice` might require system libraries like `portaudio`. Refer to the [SoundDevice documentation](https://python-sounddevice.readthedocs.io/en/latest/installation.html) for platform-specific installation instructions if you encounter issues.

4.  **Prepare `index.html`:**
    This application requires an HTML template file for the web interface. Ensure you have a `templates` directory in the root of the project containing an `index.html` file that interacts with the Flask/SocketIO backend (setting up SocketIO connection, displaying the image, providing controls). The Python script uses `render_template('index.html')`.

## Configuration

The application uses a `config.ini` file to manage settings. Create this file in the root directory of the project.

```ini
[audio_stream]
url = http://your-audio-stream-url:port/path ; Replace with your actual stream URL
sample_rate = 44100
channels = 1
format = S16_LE ; Currently format/channels are read but not strictly enforced by requests fetcher
buffer_size = 4096

[waterfall]
fft_window_size = 2048
min_freq = 100
max_freq = 10000
color_scheme = viridis
contrast = 1.0

[display]
default_time_window = 30.0  ; Time duration shown in seconds
default_refresh_rate = 0.5  ; Update interval in seconds
max_time_window = 300.0     ; Max allowed time window via UI
min_refresh_rate = 0.1      ; Fastest allowed refresh via UI
max_refresh_rate = 5.0      ; Slowest allowed refresh via UI
