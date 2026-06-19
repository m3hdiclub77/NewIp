import aiohttp
import asyncio

class Downloader:
    @staticmethod
    async def fetch(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return (await resp.text()).splitlines()

    @staticmethod
    async def fetch_all(urls):
        results = {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                tasks.append(Downloader._fetch_one(session, url))
            responses = await asyncio.gather(*tasks)
            for url, data in zip(urls, responses):
                results[url] = data
        return results

    @staticmethod
    async def _fetch_one(session, url):
        try:
            async with session.get(url) as resp:
                return [line.strip() for line in (await resp.text()).splitlines() if line.strip()]
        except:
            return []
