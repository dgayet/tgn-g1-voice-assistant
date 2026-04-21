#!/usr/bin/env python3
import argparse
import sys
import time
import pyaudio
import asyncio
import socket

FORMAT = pyaudio.paInt16
CHANNELS = 1
IP_ADDR = "192.168.123.164"
PORT = 10001
CHUNK = 1024
RATE = 16000
INPUT_DEV = 0

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

async def capture_audio(stream):
    loop = asyncio.get_running_loop()

    while True:
        data = await loop.run_in_executor(
            None,  # thread pool default
            stream.read,
            CHUNK
        )
        await queue.put(data)

async def send_audio(socket):
    loop = asyncio.get_running_loop() 
    while True:
        data = await queue.get()
        await loop.run_in_executor(None, sock.send, data)



async def main():
    p = pyaudio.PyAudio()
    #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #sock.connect((IP_ADDR, PORT))
    try:
        in_stream = open_streams(p, RATE, CHUNK, INPUT_DEV)
    except Exception as e:
        print("\nFailed to open streams with these settings:", e)
        print("Try a different --rate (common: 48000) or pick devices with --in-dev/--out-dev after running --list.")
        return 2

    #asyncio.create_task(capture_audio(in_stream))
    #asyncio.create_task(send_audio(sock))
    while True:
        try:
            pass
        except KeyboardInterrupt:
            print("Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
