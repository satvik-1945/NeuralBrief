import { NextRequest, NextResponse } from "next/server";
import { Pool } from "pg";

function getPool() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    throw new Error("DATABASE_URL is not set");
  }
  return new Pool({
    connectionString: url,
    ssl: { rejectUnauthorized: false },
  });
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const email = typeof body?.email === "string" ? body.email.trim() : "";
    const name = typeof body?.name === "string" ? body.name.trim() : null;
    const interests =
      Array.isArray(body?.interests) && body.interests.length > 0
        ? body.interests.map((i: unknown) => String(i).trim()).filter(Boolean)
        : null;

    if (!email) {
      return NextResponse.json(
        { error: "Email is required." },
        { status: 400 }
      );
    }

    if (!isValidEmail(email)) {
      return NextResponse.json(
        { error: "Please enter a valid email address." },
        { status: 400 }
      );
    }

    const interestsStr = interests ? JSON.stringify(interests) : null;

    const pool = getPool();
    await pool.query(
      `INSERT INTO people (email, name, interests) VALUES ($1, $2, $3)
       ON CONFLICT (email) DO UPDATE SET name = COALESCE(EXCLUDED.name, people.name), interests = COALESCE(EXCLUDED.interests, people.interests)`,
      [email, name || null, interestsStr]
    );
    await pool.end();

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Subscribe error:", err);

    const message = err instanceof Error ? err.message : "Unknown error";
    if (message.includes("DATABASE_URL") || message.includes("connect")) {
      return NextResponse.json(
        { error: "Service temporarily unavailable. Please try again later." },
        { status: 503 }
      );
    }

    return NextResponse.json(
      { error: "Could not subscribe. Please try again." },
      { status: 500 }
    );
  }
}
