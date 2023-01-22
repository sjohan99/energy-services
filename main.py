import aiohttp

from webtextscraper import WebTextScraper
import asyncio
import excel


def create_scraper_objects():
    scrapers = []
    for websiteInfo in excel.extract_values_excel():
        org_number, name, url = websiteInfo
        if url.endswith('/'):
            url = url[:-1]
        if 'skurup' in name.lower() or 'energi & design' in name.lower():
            pass
        else:
            scrapers.append(WebTextScraper(url, org_number, name))
    return scrapers


async def gather_with_concurrency(n, *coros):
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro
    return await asyncio.gather(*(sem_coro(c) for c in coros))


# create tasks
async def main(scrapers):
    # From excel to objects
    connector = aiohttp.TCPConnector(force_close=True, limit=50)
    aio_session = aiohttp.ClientSession(
        connector=connector,
        raise_for_status=True,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30'}
    )

    for scraper in scrapers:
        scraper.aio_session = aio_session

    ensured_future_sites = [asyncio.ensure_future(scraper.start()) for scraper in scrapers]

    await gather_with_concurrency(50, *ensured_future_sites)

    return scrapers, aio_session

if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

    scrapers = create_scraper_objects()
    n = 25
    scraper_batches = [scrapers[i * n:(i + 1) * n] for i in range((len(scrapers) + n - 1) // n)]

    for batch in scraper_batches:
        scrapers, session = asyncio.run(main(batch))
        session.close()
