#!/usr/bin/env python3
import argparse
import sys
import time
import pyaudio
import asyncio
import socket
import numpy as np

FORMAT = pyaudio.paInt16
CHANNELS = 1
IP_ADDR = "10.117.179.29"
PORT = 10001
CHUNK = 1024
RATE = 16000
INPUT_DEV = 24
THRESHOLD = 0.01

queue = asyncio.Queue()

def open_streams(p: pyaudio.PyAudio, rate: int, chunk: int, in_dev: int):
    in_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=rate,
        input=True,
        input_device_index=in_dev,
        frames_per_buffer=chunk,
    )
    return in_stream

async def capture_audio(stream, threshold):
    loop = asyncio.get_running_loop()

    while True:
        try:
            data = await loop.run_in_executor(
                None,  # thread pool default
                stream.read,
                CHUNK
            )
            data_int = np.frombuffer(data, dtype=np.int16)/65535
            rms = np.sqrt(np.mean(data_int**2))
            if rms > threshold:
                await queue.put(data)
        except Exception as e:
            print(f"[CAPTURE] Mori: {e}")
            return

async def send_audio(socket):
    loop = asyncio.get_running_loop() 
    while True:
        try:
            data = await queue.get()
            await loop.run_in_executor(None, socket.send, data)
        except Exception as e:
            print(f"[SEND] Mori: {e}")
            return

async def main():
    p = pyaudio.PyAudio()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((IP_ADDR, PORT))
    try:
        in_stream = open_streams(p, RATE, CHUNK, INPUT_DEV)
    except Exception as e:
        print("\nFailed to open streams with these settings:", e)
        print("Try a different --rate (common: 48000) or pick devices with --in-dev/--out-dev after running --list.")
        return 2

    capture_task = asyncio.create_task(capture_audio(in_stream, THRESHOLD))
    send_task = asyncio.create_task(send_audio(sock))
    
    await asyncio.Future()
    while True:
        try:
            await asyncio.gather(capture_task, send_task) 
        except:
            print("Exiting...")
        finally:
            p.terminate()

if __name__ == "__main__":
    asyncio.run(main())
