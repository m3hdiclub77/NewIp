import asyncio
import time
from core.retry import retry

class TCPWorker:
    def __init__(self, timeout, cb=None, cache=None):
        self.timeout = timeout
        self.cb = cb
        self.cache = cache

    async def probe_port(self, ip, port):
        async def run():
            start = time.perf_counter()

            r, w = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )

            w.close()
            await w.wait_closed()

            return (ip, port, (time.perf_counter() - start) * 1000)

        return await retry(run, 2, 120)

    async def probe(self, ip, ports):
        if self.cache:
            cached = self.cache.get(ip)
            if cached:
                return cached

        tasks = [self.probe_port(ip, p) for p in ports]
        res = await asyncio.gather(*tasks, return_exceptions=True)

        results = [x for x in res if x and not isinstance(x, Exception)]

        if self.cache:
            self.cache.set(ip, results)

        return results
