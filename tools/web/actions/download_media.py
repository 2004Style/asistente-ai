"""
Downloads media (YouTube music/videos) or generic files (PDFs, images) from a URL.
"""
import os
import re
import urllib.request
import urllib.parse
import subprocess
import shutil
import logging
import asyncio
from typing import Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("DownloadMediaTool")

class DownloadMediaInput(BaseModel):
    url: str = Field(..., description="The URL of the file, video, or music to download.")
    format: str = Field(
        "auto",
        description="The target format: 'auto' (detect based on URL/file), 'mp3' (audio), 'mp4' (video), or 'file' (generic document/file download)."
    )
    output_dir: Optional[str] = Field(None, description="The directory to save the file (e.g., 'descargas', 'documentos', or a full path).")
    filename: Optional[str] = Field(None, description="Optional custom filename to save the download as.")

def resolve_directory(dir_path: Optional[str], default_type: str = "downloads") -> Path:
    """Resolves Spanish folder names or relative paths to absolute Paths."""
    home = Path.home()
    if not dir_path:
        if default_type == "projects":
            # home/rbot/projects
            proj_dir = home / "rbot" / "projects"
            proj_dir.mkdir(parents=True, exist_ok=True)
            return proj_dir
        elif default_type == "music":
            music_dir = home / "Music"
            music_dir.mkdir(parents=True, exist_ok=True)
            return music_dir
        elif default_type == "videos":
            videos_dir = home / "Videos"
            videos_dir.mkdir(parents=True, exist_ok=True)
            return videos_dir
        else:
            downloads = home / "Downloads"
            downloads.mkdir(parents=True, exist_ok=True)
            return downloads
            
    dir_clean = dir_path.lower().strip()
    if dir_clean in ["descargas", "downloads", "download"]:
        target = home / "Downloads"
    elif dir_clean in ["documentos", "documents", "document"]:
        target = home / "Documents"
    elif dir_clean in ["escritorio", "desktop"]:
        target = home / "Desktop"
    elif dir_clean in ["música", "musica", "music"]:
        target = home / "Music"
    elif dir_clean in ["videos", "vídeos", "video"]:
        target = home / "Videos"
    else:
        target = Path(dir_path)
        if not target.is_absolute():
            target = home / dir_path
            
    target.mkdir(parents=True, exist_ok=True)
    return target

def download_generic_file(url: str, output_path: Path) -> str:
    """Downloads a generic file using urllib with custom user-agent."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        logger.info(f"Downloading generic file: {url} -> {output_path}")
        with urllib.request.urlopen(req, timeout=30) as response:
            # Check for redirect or suggested filename in headers
            content_disposition = response.headers.get("Content-Disposition", "")
            final_path = output_path
            
            if content_disposition and "filename=" in content_disposition:
                matches = re.findall(r'filename=["\']?([^"\';]+)["\']?', content_disposition)
                if matches:
                    final_path = output_path.parent / matches[0]
                    
            with open(final_path, "wb") as f:
                shutil.copyfileobj(response, f)
                
            return str(final_path)
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise e

def download_youtube_media(url: str, target_format: str, output_dir: Path, custom_filename: Optional[str] = None) -> str:
    """Downloads YouTube video or audio using system's yt-dlp."""
    yt_dlp_path = shutil.which("yt-dlp")
    if not yt_dlp_path:
        raise FileNotFoundError("yt-dlp is not installed on the system.")
        
    cmd = [yt_dlp_path]
    
    # Configure output template
    if custom_filename:
        # Force the extension to match format
        ext = "mp3" if target_format == "mp3" else "mp4"
        stem = Path(custom_filename).stem
        output_template = str(output_dir / f"{stem}.%(ext)s")
    else:
        output_template = str(output_dir / "%(title)s.%(ext)s")
        
    cmd += ["-o", output_template]
    
    if target_format == "mp3":
        # Extract audio and convert to mp3
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    else:
        # Download best mp4 video or merge
        cmd += ["-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]"]
        
    cmd.append(url)
    
    logger.info(f"Running yt-dlp command: {cmd}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
    
    if res.returncode != 0:
        logger.error(f"yt-dlp failed: {res.stderr}")
        raise RuntimeError(f"yt-dlp error: {res.stderr}")
        
    # Find the downloaded file
    # yt-dlp stdout usually contains: [ExtractAudio] Destination: /path/to/file.mp3 or [download] Destination: /path/to/file.mp4
    dest_match = re.findall(r'Destination:\s+(.+)', res.stdout)
    if dest_match:
        return dest_match[-1].strip()
        
    # Fallback search in directory
    # If custom filename was specified, look for it
    if custom_filename:
        stem = Path(custom_filename).stem
        for f in output_dir.iterdir():
            if f.stem == stem:
                return str(f)
                
    # Otherwise return output directory
    return str(output_dir)

class DownloadMediaTool(BaseTool):
    manifest = ToolManifest(
        name="download_media",
        description=(
            "Downloads media (music/videos from YouTube/Vimeo) or generic files (PDFs, docs, images) from a URL "
            "into a specified folder like 'descargas', 'documentos' or a custom folder."
        ),
        arguments_schema=DownloadMediaInput,
        permission_level="medium",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        url = kwargs.get("url")
        target_format = kwargs.get("format", "auto").lower().strip()
        output_dir_str = kwargs.get("output_dir")
        custom_filename = kwargs.get("filename")
        
        if not url:
            return {"error": "Missing parameter: url"}
            
        # Select default type based on format (video/music default directories)
        default_dir_type = "downloads"
        if not output_dir_str:
            if target_format == "mp3":
                default_dir_type = "music"
            elif target_format == "mp4":
                default_dir_type = "videos"
                
        output_dir = resolve_directory(output_dir_str, default_type=default_dir_type)
        
        # Detect if it is a YouTube URL
        is_youtube = "youtube.com" in url or "youtu.be" in url
        
        # Decide target format
        if target_format == "auto":
            if is_youtube:
                target_format = "mp3"  # Default to mp3 for YouTube links (most common for music/videos)
            else:
                target_format = "file"
                
        try:
            if is_youtube:
                logger.info(f"Downloading from YouTube: {url} as format: {target_format}")
                file_path = await asyncio.to_thread(
                    download_youtube_media, url, target_format, output_dir, custom_filename
                )
            else:
                # Regular HTTP download
                if not custom_filename:
                    # Extract filename from URL
                    parsed_url = urllib.parse.urlparse(url)
                    custom_filename = os.path.basename(parsed_url.path) or "downloaded_file"
                    
                target_path = output_dir / custom_filename
                logger.info(f"Downloading generic file: {url} to: {target_path}")
                file_path = await asyncio.to_thread(
                    download_generic_file, url, target_path
                )
                
            return {
                "status": "success",
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "output_dir": str(output_dir),
                "message": f"Archivo descargado correctamente en: {file_path}"
            }
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return {"error": f"Failed to download: {str(e)}"}
