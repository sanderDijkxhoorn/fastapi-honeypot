from fastapi import FastAPI, Request
from starlette.responses import Response
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import httpx

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LOG_FILE = os.getenv("LOG_FILE", "app.log")

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')

app = FastAPI()

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
    # Send to Discord webhook if URL is set
    if DISCORD_WEBHOOK_URL:
        try:
            content = f"```\n{log_message}\n```"
            async with httpx.AsyncClient() as client:
                await client.post(DISCORD_WEBHOOK_URL, json={"content": content})
        except Exception as e:
            logging.error(f"Failed to send log to Discord: {e}")
    return response

@app.api_route("/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(request: Request, rest_of_path: str):
    return Response(status_code=200)
