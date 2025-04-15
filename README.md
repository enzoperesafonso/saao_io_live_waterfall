# Live Audio Stream Waterfall Analyzer

This repository contains a Python application designed to fetch and analyze live audio streams, generating a real-time waterfall spectrogram display accessible via a web interface. 

The application uses Flask for the web server, Flask-SocketIO for real-time communication, Matplotlib for plotting, NumPy/SciPy for signal processing, and Requests for fetching the audio stream.

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
    git clone https://github.com/enzoperesafonso/saao_io_live_waterfall.git
    cd saao_io_live_waterfall
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    
    ```bash
    pip install -r requirements.txt
    ```

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
```

Markdown
Key Parameters:

url: The full URL of the live audio stream.

sample_rate: Expected sample rate of the audio stream.

fft_window_size: Number of samples used for each FFT calculation. Affects frequency resolution.

min_freq, max_freq: The frequency range (Hz) to display on the waterfall plot.

color_scheme: Matplotlib colormap name (e.g., viridis, plasma, inferno, magma, gray).

contrast: Multiplier applied to dynamic range scaling (adjust for visual clarity).

default_time_window: Initial duration (in seconds) shown on the time axis of the waterfall.

default_refresh_rate: Initial update frequency (in seconds) for the waterfall plot.

Note: Most changes in config.ini require restarting the Python application to take effect. The Stream URL and Sample Rate can be updated via the UI but also require a restart as indicated by the application. Visualization settings (fft_window_size, frequencies, color, contrast, time window, refresh rate) can be changed live via the web UI without restarting.

## Usage

Follow these steps to run the Live Audio Stream Waterfall Analyzer:

1.  **Configure the Application:**
    *   Ensure you have created and correctly configured the `config.ini` file in the project's root directory. Pay special attention to the `[audio_stream]` section, particularly the `url` and `sample_rate`.
    *   Make sure the `templates` directory exists in the project root and contains the necessary `index.html` file for the web interface.

2.  **Activate Virtual Environment (if used):**
    *   If you set up a Python virtual environment during installation, activate it:
        ```bash
        # Linux/macOS
        source venv/bin/activate

        # Windows
        venv\Scripts\activate
        ```

3.  **Run the Python Script:**
    *   Execute the main Python script from your terminal:
        ```bash
        python app.py
        ```

    *   The script will start the Flask web server. You should see output indicating the server is running, often mentioning it's serving on `http://0.0.0.0:5001/`. Note that `allow_unsafe_werkzeug=True` is used, which is suitable for development but should be reviewed for production deployment.

4.  **Access the Web Interface:**
    *   Open your web browser (Chrome, Firefox, Edge, Safari, etc.).
    *   Navigate to the following URL:
        `http://localhost:5001`
    *   If you are accessing the application from a different computer on the same network, replace `localhost` with the IP address of the machine running the Python script (e.g., `http://192.168.1.100:5001`).

5.  **Interact with the Dashboard:**
    *   Once the page loads, you should see the dashboard interface.
    *   Click the **"Start Stream"** button to begin fetching audio data and generating the waterfall plot.
    *   The waterfall display will appear and update periodically based on the configured refresh rate. The newest data appears at the top, scrolling downwards.
    *   Use the **controls** provided on the page (sliders, dropdowns, input fields) to adjust visualization settings like Frequency Range, Time Window, Refresh Rate, Color Scheme, Contrast, and FFT Window Size in real-time.
    *   If `sounddevice` is installed and working, you can toggle **"Audio Playback"** to listen to the incoming stream through your computer's default audio output.
    *   Click the **"Stop Stream"** button to pause fetching audio data. The display will freeze with the last received data.

You can start and stop the stream multiple times without restarting the Python script. However, changes made to the `config.ini` file (or stream settings updated via the UI) generally require you to stop the script (Ctrl+C in the terminal) and restart it.
