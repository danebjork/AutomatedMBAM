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
import logging

# Setup logging
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt = '%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger("MBAM")
logger.setLevel(logging.INFO)
debug_handler = logging.FileHandler("debug.log", 'w')
debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s', datefmt = '%m/%d/%Y %I:%M:%S %p'))
logger.addHandler(debug_handler)
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
            logger.info("Connection reset")
            break
        if cmd['type'] == "save":
            logger.info("Saving model")
            mbamui.save_model(cmd['md'], cmd["options"])
            await websocket.send(mbamui.send_save_done())
            if mbamui.scripts_ready():
                await websocket.send(mbamui.send_scripts())

        elif cmd['type'] == "load-model-id":
            logger.info("Loading model %s" %cmd["id"])
            send = mbamui.load_model_id(cmd['id'])
            if 'model' in send:
                await websocket.send(mbamui.send_model_load_done())
                await websocket.send(mbamui.send_save_done())
            if 'data' in send:
                await websocket.send(mbamui.send_data_done())
            if mbamui.scripts_ready():
                await websocket.send(mbamui.send_scripts())

        elif cmd['type'] == "hdf5":
            logger.info("Getting data")
            mbamui.read_model_data(await websocket.recv())
            await websocket.send(mbamui.send_data_done())
            logger.info("Data processed")
            if mbamui.scripts_ready():
                await websocket.send(mbamui.send_scripts())

        elif cmd['type'] == "geo-options":
            logger.info("Updating geodesic options")
            send = mbamui.update_geo_options(cmd['options'])
            await websocket.send(send)

        elif cmd['type'] == "geo-update":
            logger.info("Updating geodesic script")
            mbamui.update_geo_script(cmd['script'])

        elif cmd['type'] == "julia-update":
            logger.info("Updating julia script")
            mbamui.update_julia_script(cmd['script'])

        elif cmd['type'] == "geo-start":
            logger.info("Starting geodesic")
            mbamui.start_geodesic()

        elif cmd['type'] == "geo-done":
            logger.info("Killing geodesic")
            mbamui.kill_geodesic()

        elif cmd['type'] == "collect":
            logger.debug("Collecting geodesic")
            await websocket.send(mbamui.query_geo())

        elif cmd['type'] == "simplify":
            logger.info("Simplifying expression")
            send = mbamui.simplify_eq(cmd['eq'])
            await websocket.send(send)

        elif cmd['type'] == "epsilon":
            logger.info("Evaluating limit epsilon -> zero")
            send = mbamui.eval_epsilon(cmd['eq'])
            await websocket.send(send)

        elif cmd['type'] == "apply-theta":
            logger.info("Applying substitutions")
            if mbamui.load_ftheta(cmd['data']):
                logger.info("Substitution success")
                await websocket.send(mbamui.iterate())
            else:
                logger.warning("Substitution failed")

        elif cmd['type'] == "ftheta":
            logger.info("Loading ftheta")
            mbamui.load_ftheta(cmd['data'])

        elif cmd['type'] == "substitute":
            logger.info("Substituting ftilde")
            send = mbamui.sub_ftildes(cmd['eq'])
            await websocket.send(send)

        elif cmd['type'] == "manual-iter":
            logger.info("Manual iteration")
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
            logger.warning("Invalid command received", cmd)
            pass


if __name__ == "__main__":
    try:
        start_server = websockets.serve(time, '127.0.0.1', 9000)
        logger.info("Ready for Connection")
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    finally:
        asyncio.get_event_loop().stop()
