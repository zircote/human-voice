# Project Overview

This platform processes team data and turns it into dashboards, alerts, and reports
without requiring a dedicated data engineering team. It runs on Postgres and Redis,
deploys in about 15 minutes, and handles datasets up to 500GB on a single node.

## Key Features

The query engine resolves most dashboard queries in under 200ms. Access controls
are role-based, so you can lock down sensitive metrics by team. The plugin system
supports custom data connectors: we ship with connectors for MySQL, BigQuery, and
S3 out of the box.

## Getting Started

Install the CLI, point it at your database, and run the init command:

```
project-tool init --db postgres://localhost:5432/mydb
project-tool serve
```

Configuration lives in a single YAML file. The defaults work for most setups.
Check the config reference if you need to tune connection pooling or cache TTLs.
