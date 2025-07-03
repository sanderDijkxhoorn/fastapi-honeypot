# FastAPI Traffic Logger

This is a FastAPI application designed to log all incoming HTTP traffic. It captures and logs a wide range of details for each request and response, such as the HTTP method, URL, headers, body content, and more.

The log information is stored in a local file named `app.log`.

## Key Features

- Logs request method, URL, size, headers, and body.
- Logs response status code, size, headers.
- Logs client's IP address.
- Logs the processing time of each request.
- Sends logs to a Discord webhook as a rich embed (if `DISCORD_WEBHOOK_URL` is set), with pretty-printed headers and code-formatted URLs/bodies to prevent Discord from fetching links.
- Returns HTTP status code 418 ("I'm a teapot") for all requests, as a playful honeypot response.
- Periodic stats are sent to Discord as a rich embed (if `DISCORD_STATS_WEBHOOK_URL` is set), including top countries, IPs, user-agents, paths, methods, and status codes.
- Stats are archived after each report in a folder (default: `stats_archive`) with timestamped filenames for historical tracking.
- The number of top items in stats is configurable via the `STATS_TOP_N` environment variable.
- The archive folder can be changed with the `STATS_ARCHIVE_DIR` environment variable.
- Set `DEBUG_MODE=1` to send and archive stats every minute (for testing); by default, stats are sent and archived every hour.

## Setup & Usage

### 1. Create and Activate a Virtual Environment (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root (see example below) or set the variables in your shell.

Example `.env` file:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_log_webhook_url_here
DISCORD_STATS_WEBHOOK_URL=https://discord.com/api/webhooks/your_stats_webhook_url_here
LOG_FILE=app.log
STATS_TOP_N=5
STATS_ARCHIVE_DIR=stats_archive
DEBUG_MODE=1
```

- `STATS_TOP_N`: Number of top items to show in stats (default: 5)
- `STATS_ARCHIVE_DIR`: Directory to store archived stats (default: `stats_archive`)
- `DEBUG_MODE`: Set to `1` to send/archive stats every minute for testing (default: hourly)

### 4. Run the Application

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- The app will be available at [http://localhost:8000](http://localhost:8000)
- All incoming HTTP requests will be logged to `app.log`.

## Discord Webhook Integration

If you want to receive logs in a Discord channel, set the `DISCORD_WEBHOOK_URL` environment variable to your Discord webhook URL. The logs will be sent as a Discord embed, with headers formatted as pretty JSON and URLs/bodies shown as code blocks to prevent Discord from fetching them.

If you want to receive periodic stats (top countries, IPs, user-agents, etc.) in a different Discord channel, set the `DISCORD_STATS_WEBHOOK_URL` environment variable to your stats Discord webhook URL. Stats are sent every hour as a Discord embed (or every minute in debug mode). Archived stats are saved in the `stats_archive` folder by default.

## Teapot Response

All requests to the server will receive a playful HTTP 418 (I'm a teapot) response, making it clear this is a honeypot.
