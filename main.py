from fastapi import FastAPI, Request
from starlette.responses import Response
from datetime import datetime, timezone, timedelta
import logging
import os
from dotenv import load_dotenv
import httpx
import json
import asyncio
from collections import Counter
import shutil

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
STATS_FILE = "stats.json"
DISCORD_STATS_WEBHOOK_URL = os.getenv("DISCORD_STATS_WEBHOOK_URL")
STATS_TOP_N = int(os.getenv("STATS_TOP_N", 5))
STATS_ARCHIVE_DIR = os.getenv("STATS_ARCHIVE_DIR", "stats_archive")
DEBUG_MODE = os.getenv("DEBUG_MODE", "0") == "1"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')

app = FastAPI()

stats = {
    "total_requests": 0,
    "countries": Counter(),
    "ips": Counter(),
    "user_agents": Counter(),
    "paths": Counter(),
    "methods": Counter(),
    "status_codes": Counter(),
}

def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

def load_stats():
    global stats
    try:
        with open(STATS_FILE, "r") as f:
            loaded = json.load(f)
            for k in stats:
                stats[k] = Counter(loaded.get(k, {})) if k != "total_requests" else loaded.get(k, 0)
    except Exception:
        pass

@app.on_event("startup")
async def startup_event():
    load_stats()
    asyncio.create_task(report_stats_periodically())

async def report_stats_periodically():
    while True:
        now = datetime.now(timezone.utc)
        if DEBUG_MODE:
            # Next full minute
            next_time = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        else:
            # Next full hour
            next_time = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        sleep_seconds = (next_time - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        save_stats()  # Ensure stats are up to date before archiving
        # Ensure archive directory exists before copying
        if not os.path.exists(STATS_ARCHIVE_DIR):
            os.makedirs(STATS_ARCHIVE_DIR)
        if DEBUG_MODE:
            archive_name = now.strftime("%Y-%m-%dT%H-%MZ.json")
        else:
            archive_name = now.strftime("%Y-%m-%dT%H00Z.json")
        archive_path = os.path.join(STATS_ARCHIVE_DIR, archive_name)
        shutil.copy2(STATS_FILE, archive_path)
        await send_stats_to_discord()
        reset_stats()
        save_stats()

def reset_stats():
    global stats
    stats = {
        "total_requests": 0,
        "countries": Counter(),
        "ips": Counter(),
        "user_agents": Counter(),
        "paths": Counter(),
        "methods": Counter(),
        "status_codes": Counter(),
    }

def get_top(counter):
    return counter.most_common(STATS_TOP_N)

def escape_discord(text):
    # Always wrap in code formatting for clarity and to prevent Discord unfurling
    safe = str(text).replace('`', '\u200b`')
    return f"`{safe}`"

async def send_stats_to_discord():
    if not DISCORD_STATS_WEBHOOK_URL:
        logging.warning("DISCORD_STATS_WEBHOOK_URL is not set. Stats will not be sent.")
        return
    def format_top(counter):
        items = get_top(counter)
        if not items:
            return "None"
        return "\n".join([f"{i+1}. {escape_discord(k)} — {escape_discord(v)}" for i, (k, v) in enumerate(items)])
    total_requests = stats["total_requests"]
    unique_ips = len(stats["ips"])
    unique_countries = len(stats["countries"])
    summary = f"**Requests:** `{total_requests}` | **Unique IPs:** `{unique_ips}` | **Unique Countries:** `{unique_countries}`"
    embed_fields = [
        {"name": "Summary", "value": summary, "inline": False},
        {"name": "Top Countries", "value": format_top(stats["countries"]), "inline": False},
        {"name": "Top IPs", "value": format_top(stats["ips"]), "inline": False},
        {"name": "Top User-Agents", "value": format_top(stats["user_agents"]), "inline": False},
        {"name": "Top Paths", "value": format_top(stats["paths"]), "inline": False},
        {"name": "Requests per Method", "value": "\n".join([f"{escape_discord(m)}: {escape_discord(n)}" for m, n in stats["methods"].items()]) or "None", "inline": False},
        {"name": "Requests per Status Code", "value": "\n".join([f"{escape_discord(s)}: {escape_discord(n)}" for s, n in stats["status_codes"].items()]) or "None", "inline": False},
    ]
    embed = {
        "title": "Honeypot Stats (last hour)",
        "color": 0xe67e22,
        "fields": embed_fields,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(DISCORD_STATS_WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        logging.error(f"Failed to send stats to Discord: {e}")

@app.middleware("http")
async def log_traffic(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    client_host = request.client.host
    log_params = {
        "request_method": request.method,
        "request_url": str(request.url),
        "request_size": request.headers.get("content-length"),
        "request_headers": dict(request.headers),
        "request_body": await request.body(),
        "response_status": response.status_code,
        "response_size": response.headers.get("content-length"),
        "response_headers": dict(response.headers),
        "process_time": process_time,
        "client_host": client_host
    }
    log_message = str(log_params)
    logging.info(log_message)
    # Send to Discord webhook as an embed if URL is set
    if DISCORD_WEBHOOK_URL:
        try:
            # Build embed fields from log_params
            embed_fields = []
            for key, value in log_params.items():
                # Pretty-print headers as JSON code blocks
                if key in ["request_headers", "response_headers"]:
                    display_value = f"```json\n{json.dumps(value, indent=2)}\n```" if value else "`None`"
                # Show URLs and bodies as code blocks
                elif key in ["request_url", "request_body"]:
                    display_value = f"`{value}`" if value else "`None`"
                else:
                    display_value = str(value)
                embed_fields.append({
                    "name": key,
                    "value": display_value,
                    "inline": False
                })
            embed = {
                "title": "Honeypot Log",
                "color": 0x3498db,
                "fields": embed_fields,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            async with httpx.AsyncClient() as client:
                await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
        except Exception as e:
            logging.error(f"Failed to send log to Discord: {e}")
    # Update stats
    stats["total_requests"] += 1
    stats["countries"][request.headers.get("cf-ipcountry", "??")] += 1
    stats["ips"][request.headers.get("cf-connecting-ip", request.client.host)] += 1
    stats["user_agents"][request.headers.get("user-agent", "")] += 1
    stats["paths"][request.url.path] += 1
    stats["methods"][request.method] += 1
    stats["status_codes"][response.status_code] += 1
    save_stats()
    return response

@app.api_route("/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(request: Request, rest_of_path: str):
    return Response(status_code=418, content="I'm a teapot")
