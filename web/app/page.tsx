"use client";

import { useState } from "react";

const INTEREST_OPTIONS = [
  "Skincare",
  "Makeup",
  "Hair",
  "Wellness",
  "Fashion",
  "Fitness",
  "Nutrition",
  "Mental health",
  "Self-care",
  "Sustainability",
  "Fragrance",
  "Nails",
  "Anti-aging",
  "Natural beauty",
  "Haircare",
  "Body care",
  "Lifestyle",
  "Celebrities",
  "Routines",
  "Reviews",
];

export default function Home() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  function toggleInterest(interest: string) {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;

    setStatus("loading");
    setMessage("");

    try {
      const res = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          name: name.trim() || undefined,
          interests: selectedInterests.length > 0 ? selectedInterests : undefined,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setStatus("error");
        setMessage(data.error || "Something went wrong.");
        return;
      }

      setStatus("success");
      setMessage("Thank you! You're subscribed.");
      setEmail("");
      setName("");
      setSelectedInterests([]);
    } catch {
      setStatus("error");
      setMessage("Could not subscribe. Please try again.");
    }
  }

  return (
    <main className="container">
      <h1>NeuralBrief</h1>
      <p className="subtitle">
        Beauty & wellness digest. Curated articles and videos delivered to your inbox.
      </p>

      <form onSubmit={handleSubmit} className="form">
        <input
          type="email"
          placeholder="Your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="input"
          required
          disabled={status === "loading"}
        />
        <input
          type="text"
          placeholder="Your name (optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="input"
          disabled={status === "loading"}
        />

        <div className="interests-section">
          <label className="interests-label">Choose your interests</label>
          <p className="interests-hint">Click to add or remove</p>
          <div className="interests-palette">
            {INTEREST_OPTIONS.map((interest) => (
              <button
                key={interest}
                type="button"
                className={`interest-chip ${selectedInterests.includes(interest) ? "selected" : ""}`}
                onClick={() => toggleInterest(interest)}
                disabled={status === "loading"}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          className="button"
          disabled={status === "loading"}
        >
          {status === "loading" ? "Subscribing…" : "Subscribe"}
        </button>
      </form>

      {message && (
        <p className={`message ${status === "success" ? "success" : "error"}`}>
          {message}
        </p>
      )}
    </main>
  );
}
