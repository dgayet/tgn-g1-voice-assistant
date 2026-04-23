import asyncio
import socket
import struct
import time

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient


IFACE='eth0'
PORT=10001

MAX_BYTES=2048
QUEUE_MAX_SIZE = 100

async def send_to_speaker(queue: asyncio.Queue):
    ChannelFactoryInitialize(0, IFACE)
    client = AudioClient()
    client.SetTimeout(10.0)
    client.Init()

    _, old_volume = client.GetVolume()
    client.SetVolume(100)
    
    stream_id = str(time.time())

    try:
        while True:
            data = await queue.get()

            try:
                if data is None:
                    break

                ret_code, _ = await asyncio.to_thread(client.PlayStream, 'talking', stream_id, data)
                if ret_code != 0:
                    print(f"[ERROR] Failed to send chunk, return code: {ret_code}")
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        print("[INFO] Stopping audio sender...")
    finally:
        client.SetVolume(old_volume['volume'])



async def receive_audio(queue: asyncio.Queue):
    loop = asyncio.get_running_loop()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.bind(('', PORT))
        print(f'[INFO] Bound to 0.0.0.0/{PORT}')

        while True:
            try:
                data = await loop.sock_recv(sock, MAX_BYTES)

                if not data:
                    continue

                await queue.put(data)
            except asyncio.CancelledError:
                print("[INFO] Stopping audio receiver...")
                break


async def main():
    queue = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)

    receive_task = asyncio.create_task(receive_audio(queue))
    send_task = asyncio.create_task(send_to_speaker(queue))

    try:
        await asyncio.gather(receive_task, send_task)
    except asyncio.CancelledError:
        print("[INFO] Shutting down...")
    finally:
        receive_task.cancel()

        while True:
            try:
                queue.put_nowait(None)
                break
            except asyncio.QueueFull:
                await asyncio.sleep(0.01)

        await send_task


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
