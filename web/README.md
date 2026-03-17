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

1. Push the repo to GitHub (or GitLab/Bitbucket)
2. Go to [vercel.com](https://vercel.com) and sign in
3. Click **Add New** > **Project** and import your repo
4. Configure the project:
   - **Root Directory**: Set to `web` (click Edit, then set)
   - **Framework Preset**: Next.js (auto-detected)
5. Add environment variable:
   - **Name**: `DATABASE_URL`
   - **Value**: Render Postgres **external** URL (from Render Dashboard: Postgres service → Connect → External URL)
6. Click **Deploy**
7. After deploy, your landing page is live at `https://your-project.vercel.app`

**Note**: Use the **external** URL for `DATABASE_URL` because Vercel runs outside Render's network. The internal URL only works for services on Render.

The subscribe form POSTs to `/api/subscribe`, which inserts into the `people` table.
