"""The websocket handler for connecting with the User Interface.
Runs until killed or crashes.
"""
#!/usr/bin/env python

# pip3 install WebSockets
import websockets
import os
import asyncio
import sys
from mbam import MbamUI
import json

mbamui = MbamUI()

async def time(websocket, path):
    path = os.path.realpath(__file__)
    index = path.find(__file__)
    path = path[:index]
    while True:
        # cmd = None
        # t = await websocket.recv()
        # cmd = json.loads(t)
        try:
            # Waiting for commands from UI
            cmd = json.loads(await websocket.recv())
        except:
            # will break if page is refreshed
            print("connection reset")
            break
        if cmd['type'] == "save":
            mbamui.save_model(cmd['md'])
            await websocket.send(mbamui.send_save_done())
            if mbamui.scripts_ready():
                await websocket.send(mbamui.send_scripts())

        elif cmd['type'] == "load-model-id":
            print(cmd["id"])
            send = mbamui.load_model_id(cmd['id'])
            if 'model' in send:
                await websocket.send(mbamui.send_model_load_done())
                await websocket.send(mbamui.send_save_done())
            if 'data' in send:
                await websocket.send(mbamui.send_data_done())
            if mbamui.scripts_ready():
                await websocket.send(mbamui.send_scripts())

        elif cmd['type'] == "hdf5":
            print("GETTING DATA")
            mbamui.read_model_data(await websocket.recv())
            await websocket.send(mbamui.send_data_done())
            print("DATA DONE")
            if mbamui.scripts_ready():
                await websocket.send(mbamui.send_scripts())

        elif cmd['type'] == "geo-options":
            send = mbamui.update_geo_options(cmd['options'])
            await websocket.send(send)

        elif cmd['type'] == "geo-update":
            mbamui.update_geo_script(cmd['script'])

        elif cmd['type'] == "julia-update":
            mbamui.update_julia_script(cmd['script'])

        elif cmd['type'] == "julia-options":
            send = mbamui.update_julia_options(cmd['options'])
            await websocket.send(send)

        elif cmd['type'] == "geo-start":
            mbamui.start_geodesic()

        elif cmd['type'] == "geo-done":
            mbamui.kill_geodesic()

        elif cmd['type'] == "collect":
            await websocket.send(mbamui.query_geo())

        elif cmd['type'] == "simplify":
            send = mbamui.simplify_eq(cmd['eq'])
            await websocket.send(send)

        elif cmd['type'] == "epsilon":
            send = mbamui.eval_epsilon(cmd['eq'])
            await websocket.send(send)

        elif cmd['type'] == "apply-theta":
            if mbamui.load_ftheta(cmd['data']):
                print("SUBSTITUTION SUCCESS")
                await websocket.send(mbamui.iterate())
            else:
                print("SUBSTITUTION FAILED")

        elif cmd['type'] == "ftheta":
            mbamui.load_ftheta(cmd['data'])

        elif cmd['type'] == "substitute":
            send = mbamui.sub_ftildes(cmd['eq'])
            await websocket.send(send)

        elif cmd['type'] == "manual-iter":
            send = mbamui.manual_iterate(cmd['model'])
            await websocket.send(send)
            if mbamui.scripts_ready():
                await websocket.send(mbamui.send_scripts())

            """
            elif cmd == "find-params":
                data = await websocket.recv()
                data = json.loads(data)
                #print(data)
                to_send = model.check_parameters(data)
                #to_send["testing"] = model.get_latex_model()
                await websocket.send(json.dumps(to_send))
            """

        else:
            print("INVALID COMMAND", cmd)
            pass


if __name__ == "__main__":
    try:
        start_server = websockets.serve(time, '127.0.0.1', 9000)
        print("Ready for Connection")
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    finally:
        asyncio.get_event_loop().stop()
