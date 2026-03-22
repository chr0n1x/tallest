# tallest

![the tallest](docs/img/the-TALLEST.png?raw=true)

Continuously downloads ZIM files for consumption (e.g., Kiwix archives).

## Features

- **Multi-source support**: Download from multiple ZIM index URLs simultaneously
- **Pattern filtering**: Select specific files using regex patterns
- **Parallel downloads**: Uses ThreadPoolExecutor for concurrent downloads
- **Progress visualization**: Rich progress bars with speed and time estimates

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.tallest.config.json` file in your project directory:

```json
{
  "sources": [
    {
      "name": "Wikipedia ZIM Archive",
      "url": "https://dumps.wikimedia.org/kiwix/zim/wikipedia/",
      "type": "zim",
      "targetPattern": ".*wikipedia_en_all_maxi_.*",
      "download_dir": "./downloads"
    }
  ]
}
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `name` | string | Display name for the downloaded file |
| `url` | string | Base URL of the ZIM index to parse |
| `type` | string | Source type (currently only `zim` is supported) |
| `targetPattern` | string | Regex pattern to match files (optional) |
| `downloadDir` | string | Directory to store downloaded files (default: `./`) |


## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TALLEST_CONFIG_PATH` | Path to the configuration JSON file | `./.tallest.config.json` |
| `TALLEST_MAX_DOWNLOADS` | Maximum number of concurrent downloads | `4` |


## Usage
```bash
TALLEST_CONFIG_PATH=./.tallest.config.json python main.py
```

Or simply:
```bash
python main.py
```

The configuration file path can be overridden via the `TALLEST_CONFIG_PATH` environment variable.

## How It Works

1. **Parse Index**: Fetches the ZIM index page and extracts available files
2. **Filter**: Applies regex pattern to select specific files
3. **Download**: Downloads files in parallel (up to 4 concurrent downloads)
4. **Resume**: If interrupted, partial downloads are preserved for resumption
5. **Complete**: Shows progress with file name, percentage, speed, and ETA

## License

See [LICENSE](LICENSE)
