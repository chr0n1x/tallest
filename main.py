from dataclasses import dataclass
from parsers.zim import get_latest_source_link
import json
import os.path
from concurrent.futures import ThreadPoolExecutor
import signal
from functools import partial
from threading import Event
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


TALLEST_PARSERS = {
    "zim": get_latest_source_link,
}


@dataclass
class Source:
    name: str
    url: str
    target_pattern: str = ""
    download_dir: str = "./"
    type: str = "zim"


@dataclass
class Config:
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


def handle_sigint(signum, frame):
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
    except Exception as e:
        progress.console.log(f"Failed to download {url} to {path}: {e}")
        return

    # This will break if the response doesn't contain content length
    progress.update(task_id, total=int(response.info()["Content-length"]))
    with open(path, "wb") as dest_file:
        progress.start_task(task_id)
        for data in iter(partial(response.read, 32768), b""):
            dest_file.write(data)
            progress.update(task_id, advance=len(data))
            if done_event.is_set():
                return
    progress.console.log(f"Downloaded {path}")


def download(source: Source):
    """Download files from the source to the given directory."""

    with progress:
        max_workers = int(os.getenv("TALLEST_MAX_DOWNLOADS", "4"))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for url in [source.url]:
                dest_path = os.path.join(source.download_dir, source.name)
                task_id = progress.add_task(
                    "download",
                    filename=source.name,
                    start=False)
                pool.submit(copy_url, task_id, url, dest_path)


if __name__ == "__main__":
    config_path = os.getenv("TALLEST_CONFIG_PATH", "./.tallest.config.json")

    with open(config_path) as f:
        data = json.load(f)

    config = Config(sources=[
        Source(
            name=r["name"],
            url=r["url"],
            target_pattern=r.get("targetPattern", ""),
            type=r["type"],
            download_dir=r.get("download_dir", "./"),
        )
        for r in data["sources"]
    ])

    for source in config.sources:
        if not source.url:
            raise ValueError("URL is required")
        if source.type not in TALLEST_PARSERS:
            raise ValueError(f"Error: Unknown source type: {source.type}")

        parser_fx = TALLEST_PARSERS[source.type]
        name, url = parser_fx(source.url, source.target_pattern)
        if not url or not name:
            raise ValueError(f"Could not parse {name} from {url}")

        target_source = Source(
            name=name,
            url=url,
            type=source.type,
            download_dir=source.download_dir,
        )
        download(target_source)
