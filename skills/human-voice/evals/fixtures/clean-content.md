# Deploy Script

The deploy script runs in about 30 seconds. It pushes to staging first,
runs the smoke tests, then promotes to production if everything passes.

I wrote this after the third time a bad deploy cost us two hours of downtime.
The script catches the three most common mistakes: missing env vars, schema
drift, and stale Docker images.

## Usage

```bash
./deploy.sh staging
./deploy.sh production --confirm
```

Pass `--dry-run` to see what would happen without actually deploying.

## Requirements

- Docker 24+
- AWS CLI configured with deploy role
- Access to the staging VPN
