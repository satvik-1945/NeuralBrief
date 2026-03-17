# NeuralBrief Web

Landing page and subscribe form for the newsletter. Deploy to Vercel.

## Setup

1. Copy `.env.example` to `.env.local`
2. Set `DATABASE_URL` to your Postgres connection string (from Render)

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Deploy to Vercel

1. Push the repo and connect to Vercel
2. Set root directory to `web`
3. Add environment variable: `DATABASE_URL` = your Postgres URL from Render
4. Deploy

The subscribe form POSTs to `/api/subscribe`, which inserts into the `people` table.
