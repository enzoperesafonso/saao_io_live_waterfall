import configparser
import os
import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import logging
from scipy import signal
import sounddevice as sd
import requests

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Audio Stream Configuration
AUDIO_STREAM_URL = config.get('audio_stream', 'url')
SAMPLE_RATE = config.getint('audio_stream', 'sample_rate')
CHANNELS = config.getint('audio_stream', 'channels')
FORMAT = config.get('audio_stream', 'format')
BUFFER_SIZE = config.getint('audio_stream', 'buffer_size')

# Waterfall Configuration
FFT_WINDOW_SIZE = config.getint('waterfall', 'fft_window_size')
MIN_FREQ = config.getint('waterfall', 'min_freq')
MAX_FREQ = config.getint('waterfall', 'max_freq')
COLOR_SCHEME = config.get('waterfall', 'color_scheme')
CONTRAST = config.getfloat('waterfall', 'contrast')

# Display Configuration
DEFAULT_TIME_WINDOW = config.getfloat('display', 'default_time_window')
DEFAULT_REFRESH_RATE = config.getfloat('display', 'default_refresh_rate')
MAX_TIME_WINDOW = config.getfloat('display', 'max_time_window')
MIN_REFRESH_RATE = config.getfloat('display', 'min_refresh_rate')
MAX_REFRESH_RATE = config.getfloat('display', 'max_refresh_rate')

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# Global state
audio_buffer = np.array([])
spectrogram_data = None
is_streaming = False
current_max_time = DEFAULT_TIME_WINDOW
current_refresh_rate = DEFAULT_REFRESH_RATE
spectrogram_length = int(DEFAULT_TIME_WINDOW / DEFAULT_REFRESH_RATE)
color_scheme = COLOR_SCHEME
contrast = CONTRAST
min_freq = MIN_FREQ
max_freq = MAX_FREQ
audio_playback_enabled = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_spectrogram():
    """Initialize spectrogram with current settings"""
    global spectrogram_data, spectrogram_length
    n_freq_bins = FFT_WINDOW_SIZE // 2 + 1
    spectrogram_length = int(current_max_time / current_refresh_rate)
    spectrogram_data = np.zeros((n_freq_bins, spectrogram_length))
    logger.info(f"Spectrogram initialized: {n_freq_bins} bins, {spectrogram_length} time points")


def create_placeholder_image():
    """Create placeholder when no data is available"""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.5, 'Waiting for audio data...',
            ha='center', va='center', fontsize=12)
    ax.axis('off')
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def fetch_audio_stream():
    """Fetch audio stream using requests library"""
    global audio_buffer, is_streaming

    session = requests.Session()
    buffer = bytearray()
    retry_count = 0
    max_retries = 3

    while is_streaming and retry_count < max_retries:
        try:
            logger.info(f"Connecting to stream: {AUDIO_STREAM_URL}")
            with session.get(AUDIO_STREAM_URL, stream=True, timeout=5) as response:
                if response.status_code != 200:
                    logger.error(f"HTTP {response.status_code}")
                    retry_count += 1
                    time.sleep(1)
                    continue

                logger.info("Stream connected, receiving data...")
                for chunk in response.iter_content(chunk_size=BUFFER_SIZE * 2):
                    if not is_streaming:
                        break

                    if chunk:
                        buffer.extend(chunk)

                        while len(buffer) >= BUFFER_SIZE * 2:
                            frame = buffer[:BUFFER_SIZE * 2]
                            del buffer[:BUFFER_SIZE * 2]

                            try:
                                audio_data = np.frombuffer(frame, dtype=np.int16)
                                audio_buffer = audio_data
                                audio_float = audio_data.astype(np.float32) / 32768.0
                                process_audio_for_spectrogram(audio_float)

                                if audio_playback_enabled:
                                    sd.play(audio_float, samplerate=SAMPLE_RATE, blocking=False)

                            except Exception as e:
                                logger.error(f"Processing error: {str(e)}")

                if is_streaming:
                    logger.warning("Stream ended unexpectedly")
                    retry_count += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Stream error: {str(e)}")
            retry_count += 1
            time.sleep(1)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            retry_count += 1
            time.sleep(1)

    logger.info("Audio stream stopped")
    session.close()


def process_audio_for_spectrogram(audio_data):
    """Process audio frame into spectrogram"""
    global spectrogram_data

    if len(audio_data) > FFT_WINDOW_SIZE:
        audio_data = audio_data[:FFT_WINDOW_SIZE]
    elif len(audio_data) < FFT_WINDOW_SIZE:
        audio_data = np.pad(audio_data, (0, FFT_WINDOW_SIZE - len(audio_data)))

    # Compute FFT
    freqs = np.fft.rfftfreq(FFT_WINDOW_SIZE, 1 / SAMPLE_RATE)
    fft_data = np.abs(np.fft.rfft(audio_data * np.hanning(len(audio_data))))
    fft_db = 20 * np.log10(fft_data + 1e-12)

    if spectrogram_data is None:
        initialize_spectrogram()

    # Update spectrogram (newest data at top)
    spectrogram_data = np.roll(spectrogram_data, -1, axis=1)
    spectrogram_data[:, -1] = fft_db


def generate_waterfall_image():
    """Generate waterfall image with time flowing downward"""
    if spectrogram_data is None or spectrogram_data.size == 0:
        return create_placeholder_image()

    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        # Calculate frequency mask
        freqs = np.fft.rfftfreq(FFT_WINDOW_SIZE, 1 / SAMPLE_RATE)
        freq_mask = (freqs >= min_freq) & (freqs <= max_freq)

        # Prepare data (newest at top)
        display_data = spectrogram_data[freq_mask, :].T[::-1]  # Transpose and flip vertically
        display_freqs = freqs[freq_mask]

        # Dynamic scaling
        vmin = np.percentile(display_data, 5)
        vmax = np.percentile(display_data, 95)
        vmin = max(vmin * contrast, -100)
        vmax = min(vmax * contrast, 0)

        # Create axes
        time_axis = np.linspace(0, current_max_time, spectrogram_length)
        X, Y = np.meshgrid(display_freqs, time_axis)

        # Create plot (time flows downward)
        mesh = ax.pcolormesh(X, Y, display_data,
                             shading='auto',
                             cmap=color_scheme,
                             vmin=vmin,
                             vmax=vmax)

        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label('Intensity (dB)')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Time (s)')
        ax.set_title(f'Waterfall Display ({min_freq}-{max_freq} Hz)')
        ax.set_ylim(current_max_time, 0)  # Newest at top

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error generating waterfall: {str(e)}")
        return create_placeholder_image()


def background_thread():
    """Background thread to send updates to clients"""
    while True:
        try:
            if is_streaming:
                image_data = generate_waterfall_image()
                socketio.emit('waterfall_update', {'image': image_data})
            time.sleep(current_refresh_rate)
        except Exception as e:
            logger.error(f"Background thread error: {str(e)}")
            time.sleep(1)


@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')


@app.route('/start_stream', methods=['POST'])
def start_stream():
    """Start the audio stream"""
    global is_streaming, audio_thread

    if not is_streaming:
        is_streaming = True
        audio_thread = threading.Thread(target=fetch_audio_stream)
        audio_thread.daemon = True
        audio_thread.start()
        logger.info("Stream started")
        return jsonify({'status': 'started'})
    return jsonify({'status': 'already_running'})


@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    """Stop the audio stream"""
    global is_streaming

    if is_streaming:
        is_streaming = False
        logger.info("Stream stopped")
        return jsonify({'status': 'stopped'})
    return jsonify({'status': 'not_running'})


@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Update visualization settings"""
    global FFT_WINDOW_SIZE, color_scheme, contrast, audio_playback_enabled, min_freq, max_freq

    data = request.json
    if 'fft_window_size' in data:
        FFT_WINDOW_SIZE = int(data['fft_window_size'])
        initialize_spectrogram()
    if 'color_scheme' in data:
        color_scheme = data['color_scheme']
    if 'contrast' in data:
        contrast = float(data['contrast'])
    if 'audio_playback_enabled' in data:
        audio_playback_enabled = bool(data['audio_playback_enabled'])
    if 'min_freq' in data:
        min_freq = int(data['min_freq'])
    if 'max_freq' in data:
        max_freq = int(data['max_freq'])

    # Validate frequency range
    min_freq = max(0, min(min_freq, SAMPLE_RATE // 2 - 1))
    max_freq = min(SAMPLE_RATE // 2, max(max_freq, min_freq + 100))

    logger.info(f"Settings updated: {data}")
    return jsonify({'status': 'updated'})


@app.route('/update_timing', methods=['POST'])
def update_timing():
    """Update time window and refresh rate"""
    global current_max_time, current_refresh_rate

    data = request.json
    if 'max_time' in data:
        current_max_time = float(data['max_time'])
        initialize_spectrogram()
    if 'refresh_rate' in data:
        current_refresh_rate = float(data['refresh_rate'])

    logger.info(f"Timing updated: {current_max_time}s window, {current_refresh_rate}s refresh")
    return jsonify({'status': 'updated'})


@app.route('/get_config')
def get_config():
    """Return current configuration"""
    return jsonify({
        'audio_stream': {
            'url': AUDIO_STREAM_URL,
            'sample_rate': SAMPLE_RATE,
            'channels': CHANNELS,
            'format': FORMAT,
            'buffer_size': BUFFER_SIZE
        },
        'waterfall': {
            'fft_window_size': FFT_WINDOW_SIZE,
            'min_freq': min_freq,
            'max_freq': max_freq,
            'color_scheme': color_scheme,
            'contrast': contrast
        },
        'display': {
            'current_time_window': current_max_time,
            'current_refresh_rate': current_refresh_rate,
            'max_time_window': MAX_TIME_WINDOW,
            'min_refresh_rate': MIN_REFRESH_RATE,
            'max_refresh_rate': MAX_REFRESH_RATE
        }
    })


@app.route('/update_config', methods=['POST'])
def update_config():
    """Update stream configuration"""
    data = request.json

    # Write updates to config file
    config.set('audio_stream', 'url', data['url'])
    config.set('audio_stream', 'sample_rate', str(data['sample_rate']))

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    logger.info("Configuration updated - restart required")
    return jsonify({'status': 'updated', 'message': 'Please restart the application'})


@socketio.on('connect')
def handle_connect():
    """Handle new client connection"""
    logger.info("Client connected")
    emit('status', {'data': 'Connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    logger.info("Client disconnected")


if __name__ == '__main__':
    initialize_spectrogram()
    threading.Thread(target=background_thread, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5001, debug=True,
                 use_reloader=False, allow_unsafe_werkzeug=True)
