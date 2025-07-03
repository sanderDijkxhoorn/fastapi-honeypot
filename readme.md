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

## Code Overview

The application is primarily comprised of a middleware function `log_traffic` and a catch-all API route.

The `log_traffic` middleware function is responsible for processing each request and response, extracting relevant details, and logging them.

The catch-all route `{rest_of_path:path}` is a wildcard route that matches any path and HTTP method, allowing the application to handle and log all incoming requests, regardless of the endpoint or method used.

## How to Run

Ensure you have Python 3.6 or later installed.

1. First, you'll need to install FastAPI and Uvicorn (the ASGI server used to run FastAPI applications). If you haven't done so already, install them using pip:

```bash
pip install fastapi uvicorn
```

2. To start the server, navigate to the directory containing your FastAPI application file (named `main.py` by default), and run the following command:

```bash
uvicorn main:app --reload
```

The `--reload` flag enables hot reloading, which means the server will automatically update whenever you make changes to your code.

Your FastAPI application should now be running at `http://localhost:8000`. Any incoming HTTP requests will be logged and their details stored in `app.log`.

Please note that as this is a basic application for demonstration purposes, it does not include features you would typically find in a production-ready application, such as authentication, error handling, and tests.

## Discord Webhook Integration

If you want to receive logs in a Discord channel, set the `DISCORD_WEBHOOK_URL` environment variable to your Discord webhook URL. The logs will be sent as a Discord embed, with headers formatted as pretty JSON and URLs/bodies shown as code blocks to prevent Discord from fetching them.

Example `.env` file:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url_here
LOG_FILE=app.log
```

## Teapot Response

All requests to the server will receive a playful HTTP 418 (I'm a teapot) response, making it clear this is a honeypot.