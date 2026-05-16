"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const bodyPayload = isLogin ? { email, password } : { name: name || email.split("@")[0], email, password };
      const res = await fetch(`${apiUrl}/auth/${isLogin ? 'login' : 'register'}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bodyPayload)
      });
      const data = await res.json();
      localStorage.setItem("user_id", data.user_id);
      if (data.name) localStorage.setItem("user_name", data.name);
      router.push("/dashboard");
    } catch (err) {
      alert("Auth failed");
    } finally { setLoading(false); }
  };

  return (
    <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="card" style={{ width: "400px" }}>
        <h1 style={{ marginBottom: "0.5rem" }}>Zero2Offer</h1>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>Premium Career Optimization</p>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {!isLogin && (
            <>
              <label className="label">Full Name</label>
              <input className="input-field" type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Atharva Gupta" required={!isLogin} />
            </>
          )}
          <label className="label">Email</label>
          <input className="input-field" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@domain.com" required />
          <label className="label">Password</label>
          <input className="input-field" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
          <button type="submit" className="btn-primary" disabled={loading}>
            {isLogin ? "Sign In" : "Sign Up"}
          </button>
        </form>
        <button onClick={() => setIsLogin(!isLogin)} style={{ marginTop: "1rem", background: "none", border: "none", color: "var(--accent-color)", cursor: "pointer" }}>
          {isLogin ? "Need an account? Sign up" : "Have an account? Sign in"}
        </button>
      </div>
    </main>
  );
}
