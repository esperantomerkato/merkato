import asyncio
import json
import websockets

from merkato.merkato import Merkato

import logging
log = logging.getLogger("server")

# TODO: Translate incoming messages to Merkato method calls
# TODO: Security: restrict origins to localhost?


class Server(object):
    def __init__(self):
        self.initialized = False
        self.merkato = None

    async def _consume(self, ws, path):
        # Listen for incoming commands from client and translate them to method calls on Merkato.
        async for message in ws:
            data = json.loads(message)
            log.info("Received data: {}".format(data))
            if 'call' in data:
                name = data['call']
                args = data['args']
                rval = self.merkato.__dict__[name](*args)
                rmsg = {'return': name, 'value': rval}
                await ws.send(json.dumps(rmsg))

    async def _produce(self, ws, path):
        # Run merkato.update() in a loop and send results to client for rendering.
        while True:
            if self.merkato:
                data = self.merkato.update()
                msg = json.dumps(data)
                await ws.send(msg)
            await asyncio.sleep(1.0)

    async def on_connected(self, ws, path):
        log.info("Connected.")

        while True:
            msg = await ws.recv()
            msg = json.loads(msg)
            if 'merkato_params' in msg:
                merkato_params = msg['merkato_params']
                log.info("Received Merkato params: {}".format(merkato_params))
                self.merkato = Merkato(**merkato_params)
                self.initialized = True
                log.info("===> Initialized Merkato")
                break
            await asyncio.sleep(0.1)

    async def handler(self, ws, path):
        # Runs the consumer and producer concurrently.
        try:
            await self.on_connected(ws, path)
            log.info("Finished connecting.")

            producer = asyncio.ensure_future(self._produce(ws, path))
            consumer = asyncio.ensure_future(self._consume(ws, path))
            done, pending = await asyncio.wait([producer, consumer])
            for task in pending:
                task.cancel()
        except Exception as exc:
            # the websockets library swallows exceptions. In development, we don't want that:
            # if something breaks, we want to stop the server, and see a stack trace, so we can go fix it.
            log.exception(exc)
            exit(1)

    def serve(self, port=5678):
        return websockets.serve(self.handler, 'localhost', port)


if __name__ == "__main__":
    server = Server()
    asyncio.get_event_loop().run_until_complete(server.serve())
    asyncio.get_event_loop().run_forever()
