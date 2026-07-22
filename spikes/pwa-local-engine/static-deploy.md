# Static Deployment Notes - PWA Local-First

This milestone packages the local engine as a static PWA. It does not require
FastAPI for the default trace + DBC workflow.

## Build

```bash
node spikes/pwa-local-engine/build-browser.mjs
```

The deployable directory is:

```text
spikes/pwa-local-engine/site/
```

It contains `index.html`, `styles.css`, `manifest.webmanifest`, `sw.js`, static
assets, and browser modules.

## Caddy Example

For a dedicated subdomain:

```caddyfile
cantracediag.paulmondou.fr {
	encode zstd gzip
	root * /srv/sites/cantracediag
	file_server
	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains"
		X-Content-Type-Options "nosniff"
		X-Frame-Options "DENY"
		Referrer-Policy "strict-origin-when-cross-origin"
		Permissions-Policy "geolocation=(), microphone=(), camera=(), interest-cohort=()"
		Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; manifest-src 'self'; worker-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
		-Server
	}
}
```

Copy the contents of `spikes/pwa-local-engine/site/` into
`/srv/sites/cantracediag` on the VPS.

## Boundary

This is the static PWA path. The current FastAPI app remains the production
local-server architecture until the local-first UI and DBC coverage are promoted
out of spikes.
