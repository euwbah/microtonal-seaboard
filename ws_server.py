"""
Websocket server for the purpose of sending out microtonal note info
"""
import asyncio
from asyncio import get_event_loop, new_event_loop, set_event_loop
from threading import Thread
from time import sleep

import janus
import websockets


message_queue = {}


async def handler(websocket, path):
    global message_queue
    await websocket.send('hello')

    print('new connection')
    q = janus.Queue()
    message_queue['sync'] = q.sync_q
    message_queue['async'] = q.async_q

    while True:
        message = await message_queue['async'].get()
        await websocket.send(message)


def start_ws_server():
    print('starting websocket server at 127.0.0.1:8765')

    def ws_thread():
        loop = new_event_loop()
        set_event_loop(loop)
        server = websockets.serve(handler, '127.0.0.1', 8765)
        loop.run_until_complete(server)
        loop.run_forever()

    Thread(target=ws_thread).start()


def send_note_on(edosteps_from_a4, velocity):
    if 'sync' in message_queue:
        message_queue['sync'].put(f'on:{edosteps_from_a4}:{velocity}')


def send_note_off(edosteps_from_a4, velocity):
    if 'sync' in message_queue:
        message_queue['sync'].put(f'off:{edosteps_from_a4}:{velocity}')


def send_cc(cc, value):
    # assumes single channel mode so channel doesn't matter-
    if 'sync' in message_queue:
        message_queue['sync'].put(f'cc:{cc}:{value}')


if __name__ == '__main__':
    # run this file to test web socket without seaboard
    start_ws_server()

    sleep(1)

    count = 0
    while True:
        print('ping sent')
        send_note_on(0, count)
        send_note_off(0, count)
        send_cc(64, count)
        count += 1
        sleep(1)
