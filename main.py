from webtextscraper import WebTextScraper
import asyncio


# small websites for testing
site1 = WebTextScraper('https://koieramen.no', '1', 'Koie')
site2 = WebTextScraper('https://sjohan99.github.io', '2', 'JohanSelin')


# create tasks
async def main():
    await asyncio.gather(
        asyncio.ensure_future(site1.start()),
        asyncio.ensure_future(site2.start())
    )

# run tasks in main() until all are completed
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

# write results to disk
site1.save()
site2.save()
