import asyncio
import json
import websockets

from merkato.merkato import Merkato

# TODO: Run initial config when the client connects
# TODO: write simple ws client

class Server(object):
    def __init__(self, *m_args, **m_kwargs):
        self.merkato = Merkato(*m_args, **m_kwargs)

    async def _consume(self, ws, path):
        # Listen for incoming commands from client and translate them to method calls on Merkato.
        async for message in ws:
            data = json.loads(message)

    async def _produce(self, ws, path):
        # Run merkato.update() in a loop and send results to client for rendering.
        while True:
            data = self.merkato.update()
            msg = json.dumps(data)
            await ws.send(msg)

    async def handler(self, ws, path):
        # Runs the consumer and producer concurrently.
        # TODO: I think here is where we put on-connected logic.
        producer = asyncio.ensure_future(self._produce(ws, path))
        consumer = asyncio.ensure_future(self._consume(ws, path))
        done, pending = await asyncio.wait([producer, consumer])
        for task in pending:
            task.cancel()

    def serve(self, port=5678):
        return websockets.serve(self.handler, 'localhost', port)


if __name__ == "__main__":
    server = Server()
    asyncio.get_event_loop().run_until_complete(server.serve())
    asyncio.get_event_loop().run_forever()