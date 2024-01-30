from datetime import datetime
import os
import time
import logging


import pyaudio
import yaml
import wave

from pprint import pprint

FORMAT = pyaudio.paInt16
update_interval = 5

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def load_config(path: str = "config.yaml"):
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        logging.info("Configuration loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise
    return config


def list_audio_devices(index: int = None):
    audio = pyaudio.PyAudio()
    try:
        for i in range(audio.get_device_count()):
            if index is not None and index != i:
                continue
            dev = audio.get_device_info_by_index(i)
            logging.info(
                f"{i}: {dev['name']} (Input Channels: {dev['maxInputChannels']})"
            )
    except Exception as e:
        logging.error(f"Error listing audio devices: {e}")
    finally:
        audio.terminate()


def show_audio_info(input_device_index: int = None):
    audio = pyaudio.PyAudio()
    try:
        info = audio.get_device_info_by_index(input_device_index)
        logging.info("-" * 80)
        logging.info("Device info:")
        for key, value in info.items():
            logging.info(f"{key:25}\t{value}")
        logging.info("-" * 80)
    except Exception as e:
        logging.error(f"Error showing audio device info: {e}")
    finally:
        audio.terminate()


def main():
    start_time = time.time()  # Capture the start time

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.wav")

    save_file = os.path.join("recordings", now)

    try:
        config = load_config()
    except Exception as e:
        logging.error(f"Failed to start due to configuration error: {e}")
        return

    config_audio = config["Audio"]

    channels = config_audio["channels"]
    rate = config_audio["rate"]
    input_device_index = config_audio["input_device_index"]
    frames_per_buffer = config_audio["frames_per_buffer"]
    debug = config_audio["debug"]

    list_audio_devices(input_device_index if not debug else None)
    show_audio_info(input_device_index if not debug else None)

    audio = pyaudio.PyAudio()

    # Open the stream for recording
    stream = audio.open(
        format=FORMAT,
        channels=channels,
        rate=rate,
        input=True,
        input_device_index=input_device_index,  # Default input device
        frames_per_buffer=frames_per_buffer,
    )

    logging.info("Recording started.")

    with wave.open(save_file, "wb") as wf:
        logging.info("Press Ctrl+C to stop recording...")
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(rate)
        try:
            # Open the stream for recording
            stream = audio.open(
                format=FORMAT,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=frames_per_buffer,
            )

            with wave.open(save_file, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(rate)
                try:
                    while True:
                        elapsed_time = time.time() - start_time
                        print(
                            f"Recording... Elapsed time: {elapsed_time:.2f} seconds",
                            end="\r",
                        )
                        data = stream.read(frames_per_buffer)

                        if len(data) == 0:
                            logging.warning("No data received.")
                            break

                        wf.writeframes(data)

                        time.sleep(0.01)

                except KeyboardInterrupt:
                    print()
                    logging.info(f"Finished recording. Saved to {save_file}.")

        except Exception as e:
            logging.error(f"Error during recording: {e}")
        finally:
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            audio.terminate()


if __name__ == "__main__":
    main()
