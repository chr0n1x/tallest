from dataclasses import dataclass
from parsers.zim import parse_zim_links
import json
import logging
import os

logger = logging.getLogger(__name__)

TALLEST_PARSERS: dict[str, callable] = {
    "zim": parse_zim_links,
}


@dataclass
class Source:
    name: str
    url: str
    target_pattern: str
    type: str = "zim"


@dataclass
class Config:
    sources: list[Source]


def main() -> None:
    config_path = os.getenv("TALLEST_CONFIG_PATH", "./.tallest.config.json")

    with open(config_path) as f:
        data = json.load(f)

    config = Config(sources=[
        Source(
            name=r["name"],
            url=r["url"],
            target_pattern=r.get("targetPattern", ""),
            type=r["type"]
        )
        for r in data["sources"]
    ])

    for source in config.sources:
        logger.info(f"Name: {source.name}")
        logger.info(f"URL: {source.url}")
        logger.info(f"TargetPattern: {source.target_pattern}")
        logger.info(f"Type: {source.type}")
        logger.info("---")
        if not source.url:
            raise ValueError("URL is required")
        if source.type not in TALLEST_PARSERS:
            logger.error(f"Error: Unknown source type: {source.type}")
        else:
            parser = TALLEST_PARSERS[source.type]
            parser(source.url, source.target_pattern)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
