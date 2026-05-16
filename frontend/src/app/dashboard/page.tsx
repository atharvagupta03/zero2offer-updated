"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function Dashboard() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("User");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [extraDetails, setExtraDetails] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [onboardingLoading, setOnboardingLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = localStorage.getItem("user_id");
    const name = localStorage.getItem("user_name");
    if (!id) {
      router.push("/");
    } else {
      setUserId(id);
      if (name) setUserName(name);
      fetchHistory(id);
      
      const savedAnalysis = localStorage.getItem(`analysis_${id}`);
      if (savedAnalysis) setAnalysisResult(savedAnalysis);
    }
  }, [router]);

  const fetchHistory = async (id: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const res = await fetch(`${apiUrl}/api/history/${id}`);
      const data = await res.json();
      if (data.history && data.history.length > 0) {
        setMessages(data.history.map((m: any) => ({ role: m.role, content: m.content })));
      } else {
        setMessages([{ role: "assistant", content: `Welcome to Zero2Offer, ${localStorage.getItem("user_name") || "Friend"}. Please use the sidebar to upload your details, and I will generate your complete Readiness Report!` }]);
      }
    } catch (err) { console.error("Failed to fetch history", err); }
  };

  useEffect(() => {
    if (userId && analysisResult) {
      localStorage.setItem(`analysis_${userId}`, analysisResult);
    }
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, analysisResult, userId]);

  const handleOnboard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !targetRole || !userId) return;
    setOnboardingLoading(true);
    console.log("[API Debug] Initiating onboarding analysis for role:", targetRole);
    setMessages(prev => [...prev, { role: "user", content: `[Initiating analysis for ${targetRole}]` }]);
    
    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("target_role", targetRole);
    formData.append("extra_details", extraDetails);
    formData.append("file", file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const res = await fetch(`${apiUrl}/api/onboard`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) {
        console.error("[API Error] Onboarding failed:", data.detail);
        setMessages(prev => [...prev, { role: "assistant", content: `Analysis Failed: ${data.detail || "Unknown error"}` }]);
        return;
      }
      console.log("[API Success] Onboarding analysis complete:", data.analysis.substring(0, 50) + "...");
      setAnalysisResult(data.analysis);
      setMessages(prev => [...prev, { role: "assistant", content: "Analysis complete. Data rendered in preview window. I've broken down your Strengths, Weaknesses, and provided a Roadmap." }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Error connecting to service." }]);
    } finally { setOnboardingLoading(false); }
  };

  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || !userId) return;
    const userMessage = input;
    setInput("");
    const context = messages.slice(-4).map(m => `${m.role}: ${m.content}`).join("\n");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);
    console.log("[API Debug] Sending chat message payload:", { user_id: userId, message: userMessage });

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, message: `Context:\n${context}\n\nUser (${userName}): ${userMessage}` })
      });
      const data = await res.json();
      if (!res.ok) {
        console.error("[API Error] Chat request failed:", data.detail);
        setMessages(prev => [...prev, { role: "assistant", content: `Request Failed: ${data.detail || "Unknown error"}` }]);
        return;
      }
      console.log("[API Success] Chat response received:", data.response);
      setMessages(prev => [...prev, { role: "assistant", content: data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Error sending message." }]);
    } finally { setLoading(false); }
  };

  const handleLogout = () => {
    localStorage.removeItem("user_id");
    localStorage.removeItem("user_name");
    if (userId) {
      localStorage.removeItem(`messages_${userId}`);
      localStorage.removeItem(`analysis_${userId}`);
    }
    router.push("/");
  };

  if (!userId) return null;

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <div style={{ width: "320px", borderRight: "1px solid var(--border-color)", padding: "2rem", backgroundColor: "var(--surface-color)", display: "flex", flexDirection: "column" }}>
        <h2 style={{ marginBottom: "2rem" }}>Configuration</h2>
        <form onSubmit={handleOnboard} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <label className="label">Target Role</label>
          <input className="input-field" value={targetRole} onChange={e => setTargetRole(e.target.value)} placeholder="e.g., Frontend Intern" required />
          
          <label className="label">Extra Details (Skills, constraints, etc.)</label>
          <textarea 
            className="input-field" 
            style={{ height: "100px", resize: "none" }}
            value={extraDetails} 
            onChange={e => setExtraDetails(e.target.value)} 
            placeholder="I know JS, React, Node. Looking for remote roles."
          />

          <label className="label">Resume (PDF/TXT)</label>
          <input type="file" className="input-field" onChange={e => setFile(e.target.files?.[0] || null)} required />
          <button type="submit" className="btn-primary" disabled={onboardingLoading}>
            {onboardingLoading ? "Analyzing..." : "Initialize Analysis"}
          </button>
        </form>

        <div style={{ marginTop: "auto", paddingTop: "2rem" }}>
          <p style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>{userName}</p>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>ID: {userId?.substring(0, 12)}</p>
          <button onClick={handleLogout} className="btn-primary" style={{ width: "100%", backgroundColor: "var(--surface-color)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}>
            Sign Out
          </button>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <header style={{ padding: "1.5rem 2rem", borderBottom: "1px solid var(--border-color)", backgroundColor: "var(--surface-color)" }}>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Zero2Offer Career Portal</h1>
        </header>
        <div style={{ flex: 1, display: "flex", padding: "2rem", gap: "2rem", overflow: "hidden" }}>
          <div style={{ flex: 1, overflowY: "auto" }}>
            <div className="card" style={{ minHeight: "100%" }}>
              <h3>Analysis Preview</h3>
              <div className="markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysisResult || "Awaiting document analysis..."}</ReactMarkdown>
              </div>
            </div>
          </div>
          <div className="card" style={{ width: "400px", display: "flex", flexDirection: "column" }}>
            <h3>Terminal</h3>
            <div style={{ flex: 1, overflowY: "auto", margin: "1rem 0" }}>
              {messages.map((m, i) => (
                <div key={i} style={{ marginBottom: "1rem", textAlign: m.role === "user" ? "right" : "left" }}>
                  <div style={{ display: "inline-block", padding: "0.5rem 1rem", borderRadius: "8px", backgroundColor: m.role === "user" ? "var(--accent-color)" : "#f0f0f0", color: m.role === "user" ? "#fff" : "#000" }}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
            <form onSubmit={handleChat} style={{ display: "flex", gap: "0.5rem" }}>
              <input className="input-field" value={input} onChange={e => setInput(e.target.value)} placeholder="Type a message..." />
              <button type="submit" className="btn-primary">Send</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
