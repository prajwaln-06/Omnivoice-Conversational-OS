import pyaudio
import array

pa = pyaudio.PyAudio()
print('Available Audio Input Devices:')
for i in range(pa.get_device_count()):
    dev = pa.get_device_info_by_index(i)
    if dev.get('maxInputChannels', 0) > 0:
        print(f" [{i}] {dev.get('name')}")

print('\nTesting default microphone... Make some noise!')
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=3200)
try:
    for _ in range(10):
        chunk = stream.read(3200, exception_on_overflow=False)
        samples = array.array('h', chunk)
        peak = max(abs(s) for s in samples) if samples else 0
        
        # Simple volume bar
        bar = '|' * int((peak / 32768.0) * 50)
        print(f'Peak: {peak:5d} {bar}')
except Exception as e:
    print(f"Error reading from mic: {e}")
finally:
    stream.stop_stream()
    stream.close()
    pa.terminate()
