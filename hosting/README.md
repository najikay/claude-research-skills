# Hosting the reference checker

The same checker that runs locally in Claude Code can be served over HTTP so citation-check verifies references on Claude.ai too. `servers/reference_lookup/remote.py` wraps the checker in MCP's Streamable HTTP transport (stateless: one JSON-RPC message per POST to `/mcp`).

- Standard library only; one process; nothing stored.
- `GET /health` for the platform's health check; `GET /` describes the service.
- A per-address rate limit (60 messages a minute, bursts of 20) protects OpenAlex and arXiv; a client over it gets `429` with `Retry-After`.
- The log carries the method and tool name, the status and the time; never the reference text.

## Run it anywhere

```
python3 servers/reference_lookup/remote.py --port 8080
docker build -f hosting/Dockerfile -t research-desk-checker . && docker run -p 8080:8080 research-desk-checker
```

## Fly.io (the hosted copy)

```
fly apps create research-desk-checker   # once
fly deploy -c hosting/fly.toml          # from the repo root
curl https://research-desk-checker.fly.dev/health
```

`hosting/fly.toml` keeps one shared-CPU machine running (no cold starts). Logs: `fly logs`.

## Point the plugin at it

`.mcp.json` lists the hosted server beside the local one:

```json
"reference-lookup-hosted": { "type": "http", "url": "https://research-desk-checker.fly.dev/mcp" }
```

The directory asks for a remote server to be submitted as an MCP connector as well, even when a plugin references it.
