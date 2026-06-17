"""
Standard periodic or background jobs, such as download tasks.
"""
import urllib.request
import logging
from pathlib import Path
from app.container import Container

logger = logging.getLogger("BackgroundJobs")

async def download_file_job(url: str, dest_path: str, session_id: str = "default") -> bool:
    """Download a file in the background and publish progress events."""
    event_bus = Container.resolve("event_bus")
    logger.info(f"Starting file download: {url} -> {dest_path}")
    
    await event_bus.publish("job_start", {"job": "download", "url": url, "dest": dest_path})
    
    def _download():
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(dest))
        
    try:
        import asyncio
        await asyncio.to_thread(_download)
        logger.info(f"Download completed successfully: {dest_path}")
        await event_bus.publish("job_success", {"job": "download", "url": url, "dest": dest_path})
        return True
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        await event_bus.publish("job_error", {"job": "download", "url": url, "error": str(e)})
        return False
