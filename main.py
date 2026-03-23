"""Tallest - ZIM source downloader."""

from threading import Event
import json
import signal
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
import os.path
from urllib.request import urlopen

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from parsers.zim import get_latest_source_link

TALLEST_PARSERS = {
    "zim": get_latest_source_link,
}


@dataclass
class Source:
    """Represents a download source."""
    name: str
    url: str
    target_pattern: str = ""
    download_dir: str = "./"
    type: str = "zim"


@dataclass
class Config:
    """Application configuration."""
    sources: list[Source]


progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)


done_event = Event()


def handle_sigint(_signum, _frame):
    """Handle SIGINT by setting the done event."""
    done_event.set()


signal.signal(signal.SIGINT, handle_sigint)


def copy_url(task_id: TaskID, url: str, path: str) -> None:
    """Copy data from a url to a local file."""
    if os.path.exists(path):
        progress.console.log(f"Skipping {path} (already exists)")
        return
    progress.console.log(f"Requesting {url}")
    try:
        response = urlopen(url)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        progress.console.log(f"Failed to download {url} to {path}: {e}")
        return

    # This will break if the response doesn't contain content length
    progress.console.log(f"Downloading to {path}")
    progress.update(task_id, total=int(response.info()["Content-length"]))
    try:
        with open(path, "wb") as dest_file, response as resp:
            progress.start_task(task_id)
            for data in iter(partial(resp.read, 32768), b""):
                dest_file.write(data)
                progress.update(task_id, advance=len(data))
                if done_event.is_set():
                    return
    # pylint: disable=broad-exception-caught
    except Exception as e:
        progress.console.log(f"Failed to write to {path}: {e}")
        return
    progress.console.log(f"Downloaded {path}")


def download(sources: list[Source]):
    """Download files from the source to the given directory."""

    with progress:
        max_workers = int(os.getenv("TALLEST_MAX_DOWNLOADS", "4"))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for item in sources:
                dest_path = os.path.join(item.download_dir, item.name)
                task_id = progress.add_task(
                    "download",
                    filename=item.name,
                    start=False)
                pool.submit(copy_url, task_id, item.url, dest_path)


if __name__ == "__main__":
    config_path = os.getenv("TALLEST_CONFIG_PATH", "./.tallest.config.json")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    for r in config["sources"]:
        config = Config(sources=[
            Source(
                name=r["name"],
                url=r["url"],
                target_pattern=r.get("targetPattern", ""),
                type=r["type"],
                download_dir=r.get("downloadDir", "./"),
            )
        ])

    target_sources = []

    for src in config.sources:
        if not src.url:
            raise ValueError("URL is required")
        if src.type not in TALLEST_PARSERS:
            raise ValueError(f"Error: Unknown source type: {src.type}")

        parser_fx = TALLEST_PARSERS[src.type]
        src_name, src_url = parser_fx(src.url, src.target_pattern)
        if not src_url or not src_name:
            raise ValueError(f"Could not parse {src_name} from {src_url}")

        target_sources.append(
            Source(
                name=src_name,
                url=src_url,
                type=src.type,
                download_dir=src.download_dir,
            )
        )

    download(target_sources)
