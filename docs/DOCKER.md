# Docker deployment (VPS)

Production image: **Next.js standalone** + **Prisma** + **SQLite** (`better-sqlite3`).  
SQLite data should live on a **volume** or **bind mount** so it survives container recreation.

## Build

```bash
docker build -t your-registry/dps-web:latest .
```

## Run (single container)

```bash
docker run -d \
  --name dps \
  -p 3000:3000 \
  -e DATABASE_URL=file:/data/dev.db \
  -e GEMINI_API_KEY=... \
  -e OPENAI_API_KEY=... \
  -v dps_sqlite:/data \
  --restart unless-stopped \
  your-registry/dps-web:latest
```

On **first start**, if `/data/dev.db` is missing, the entrypoint copies a **schema-only** database from the image. Then run seed or restore your own `dev.db` if you need data.

## Compose (recommended)

From the repo root:

```bash
docker compose up -d --build
```

Pass secrets (example):

```bash
docker compose --env-file .env.production up -d --build
```

Ensure `.env.production` includes `GEMINI_API_KEY`, `OPENAI_API_KEY`, etc., and that `DATABASE_URL` in compose stays `file:/data/dev.db` unless you change the volume layout.

## Bring your existing SQLite file

1. Stop the stack.
2. Copy `prisma/dev.db` from your machine to the host path that is mounted at `/data/dev.db` (e.g. into the named volume or bind mount directory).
3. Start the container again.

Example with bind mount:

```yaml
volumes:
  - ./sqlite-data:/data
```

Place `dev.db` at `./sqlite-data/dev.db` on the host.

## Push image to a registry (then pull on VPS)

```bash
docker tag your-registry/dps-web:latest your-registry/dps-web:v1
docker push your-registry/dps-web:v1
```

On the VPS:

```bash
docker pull your-registry/dps-web:v1
docker run ... your-registry/dps-web:v1
```

## Notes

- **Platform:** Build for the VPS CPU (`linux/amd64` vs `linux/arm64`), e.g.  
  `docker build --platform linux/amd64 -t ... .`
- **HTTPS:** Put **Caddy** or **nginx** in front on the host for TLS; this container serves HTTP on port 3000.
- **Migrations:** Schema is applied at **image build** (`prisma db push`). For new migrations after deploy, run Prisma against the same `DATABASE_URL` / volume (e.g. one-off container with the app image and `npx prisma db push`).
