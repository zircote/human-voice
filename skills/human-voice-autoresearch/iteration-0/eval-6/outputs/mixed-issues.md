# Release Notes: v3.0

This release ships a rebuilt caching layer, a refactored auth module, and faster builds.

## What's New

We redesigned the caching system from scratch, replacing the LRU cache with
a two-tier strategy that cut p95 latency from 120ms to 15ms. The new
architecture handles 10x more concurrent connections without adding hardware.

Build times dropped 40%. Error messages now include the originating module
and a suggested fix. The logging pipeline writes structured JSON, and the
monitoring dashboard tracks cache hit rates in real time. Deploys finish
in under 90 seconds.

We also refactored the authentication module to support OAuth2 PKCE,
upgraded the API gateway to handle gRPC alongside REST, and optimized
the database layer with connection pooling. Together, these changes
reduced average API response time by 35%.

See the full changelog below for specifics.

"The new caching layer saved us two hours of debugging per week," noted one developer.
