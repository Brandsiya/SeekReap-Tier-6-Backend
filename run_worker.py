#!/usr/bin/env python3
"""Worker wrapper with health check server for Cloud Run."""
import os
import threading
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def health_check(request):
    return web.Response(text="OK", status=200)

def start_worker_thread():
    import pg_worker
    logger.info("Starting worker thread...")
    pg_worker.main()

async def main():
    # Start the polling worker in a background thread
    t = threading.Thread(target=start_worker_thread, daemon=True)
    t.start()
    logger.info("Worker thread started")

    # Start health check HTTP server
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/readiness', health_check)
    app.router.add_get('/', health_check)

    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Health check server on port {port}")

    # Keep running forever
    import asyncio
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
