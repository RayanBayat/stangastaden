# Stångåstaden MCP

A remote [Model Context Protocol](https://modelcontextprotocol.io) server that wraps the [Stångåstaden](https://www.stangastaden.se) tenant portal so Claude (or any MCP client) can do the things you'd normally open the app for — check your profile, see laundry slots, book one, cancel one, read area news.

## Demo

https://github.com/RayanBayat/stangastaden/raw/main/demo.mp4

<video src="https://github.com/RayanBayat/stangastaden/raw/main/demo.mp4" controls width="720"></video>

## What it does

Stångåstaden's tenant site (`stangastaden.se` + `boendeappbackend.stangastaden.se`) doesn't expose a public API. The server logs in as a guest user, swaps the WordPress session for the booking-backend JWT the mobile app uses, caches it, and exposes the underlying endpoints as MCP tools.

Tools:

| Tool | What it does |
| --- | --- |
| `get_user_profile` | Your name, address, contact info, settings |
| `list_my_bookings` | Current and upcoming bookings across all categories |
| `list_booking_categories` | Booking categories available to you (usually Laundry) |
| `list_available_slots` | Free laundry slots between two dates |
| `book_slot` | Book a laundry slot |
| `cancel_booking` | Cancel a booking by ID |
| `list_booking_menu` | Booking menu items shown in the lokalbokning UI |
| `area_contacts` | Property manager / emergency contacts for your area |
| `area_news` | Recent news and notices for your area |

Every tool takes `username` + `password` (your Stångåstaden guest credentials, e.g. `28E0400A021`). Sessions are cached in-memory for ~58 minutes.

## Architecture

```
Claude (MCP client)
      │  streamable HTTP
      ▼
API Gateway  ──►  Lambda (Docker image)
                      │
                      ▼
              AWS Lambda Web Adapter
                      │
                      ▼
              FastMCP server (Python)
                      │
                      ▼
    stangastaden.se  +  boendeappbackend.stangastaden.se
```

- **[src/stangastaden/server.py](src/stangastaden/server.py)** — FastMCP server with the tool definitions and the auth shuffle (WP guest login → external token → booking-backend JWT).
- **[Dockerfile](Dockerfile)** — `uv`-based multi-stage build, bundles the [AWS Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter) so the HTTP server runs unchanged inside Lambda.
- **[stangastaden_infra/stacks/mcp_stack.py](stangastaden_infra/stacks/mcp_stack.py)** — CDK stack: `DockerImageFunction` + `LambdaRestApi`, region `eu-north-1`.

## Run locally

```bash
uv sync
uv run stangastaden-server
# server on http://localhost:8000/mcp
```

## Deploy

```bash
uv sync --group cdk
npx cdk deploy
```

The stack outputs `McpUrl` — paste that into Claude under **Settings → Connectors → Add custom connector**.

## Disclaimer

Unofficial. Not affiliated with Stångåstaden. Uses the same private endpoints their mobile app uses — if they change them, this breaks. Use your own credentials.
