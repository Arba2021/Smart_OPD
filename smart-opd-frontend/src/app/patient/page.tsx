// smart-opd-frontend/app/patient/page.tsx
"use client";
import { useState, useEffect } from "react";
import SmsSimulator from "../../components/SmsSimulator";

const API_BASE = "http://localhost:8000";

export default function PatientPage() {
  const [queueCount, setQueueCount] = useState(0);
  const [formData, setFormData] = useState({ name: "", phone: "", symptom: "", doctor_id: "orth-002" });
  const [smsMessage, setSmsMessage] = useState<string | null>(null);
  const [triageReason, setTriageReason] = useState("");
  const [journeySaved, setJourneySaved] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/public-queue-count?doctor_id=${formData.doctor_id}`)
      .then(res => res.json())
      .then(data => setQueueCount(data.count))
      .catch(() => {});
  }, [formData.doctor_id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTriageReason("");
    setJourneySaved(null);

    try {
      const res = await fetch(`${API_BASE}/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });

      const data = await res.json();

      if (!res.ok) {
        if (data.detail && data.detail.type === "CUTOFF") {
          setJourneySaved(data.detail);
        } else {
          alert(data.detail || "Booking failed");
        }
      } else {
        setSmsMessage(data.ai_message);
        if (data.ai_triage_reason) {
          setTriageReason(data.ai_triage_reason);
        }
        setFormData({ ...formData, name: "", phone: "" });
      }
    } catch {
      alert("Network error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white p-8 font-sans">
      {journeySaved && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-white p-10 rounded-2xl shadow-2xl text-center max-w-md border-4 border-green-500">
            <div className="text-6xl mb-4">🛑</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-2">JOURNEY PREVENTED</h2>
            <p className="text-gray-500 mb-4">AI detected Doctor capacity is full.</p>
            <div className="bg-green-50 p-4 rounded-lg mb-6 border border-green-200">
              <p className="text-sm text-gray-600">Patient: {journeySaved.patient}</p>
              <p className="text-2xl font-bold text-green-600 mt-2">💰 Estimated ₹1000 Wage Saved</p>
              <p className="text-xs text-gray-500 mt-1">(Aligns with UN SDG 1: No Poverty)</p>
            </div>
            <div className="bg-gray-50 p-3 rounded text-sm text-left italic text-gray-700 border">
              <span className="font-bold text-blue-600">AI Message:</span> {journeySaved.ai_message}
            </div>
            <button onClick={() => setJourneySaved(null)} className="mt-6 bg-gray-800 text-white px-8 py-3 rounded-lg font-bold">Close</button>
          </div>
        </div>
      )}

      <div className="max-w-3xl mx-auto">
        <div className="bg-blue-50 border-l-8 border-blue-600 p-6 mb-8 rounded-r-lg">
          <h1 className="text-2xl font-bold text-blue-900">Do not visit the hospital yet</h1>
          <p className="text-blue-700 mt-1">You will receive an SMS with instructions on when to start walking to the hospital.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="border border-gray-200 p-6 rounded-lg shadow-sm">
            <h2 className="text-xl font-bold mb-4 text-gray-800">Generate Token</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">What is the primary problem?</label>
              <select value={formData.symptom} onChange={(e) => setFormData({...formData, symptom: e.target.value})} className="w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none">
                <option value="">Select symptom...</option>
                <option value="Leg, Joint Pain or Fracture">Leg, Joint Pain or Fracture</option>
                <option value="Severe Chest Pain and Breathing issue">Severe Chest Pain / Breathing issue</option>
                <option value="Common Cold and Fever">Common Cold and Fever</option>
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Patient Full Name</label>
              <input type="text" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Enter name" />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">Mobile Number</label>
              <input type="tel" value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} className="w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none" placeholder="10 digit number" />
              <p className="text-xs text-gray-500 mt-1">We will send an SMS to this number</p>
            </div>

            <button onClick={handleSubmit} disabled={loading || !formData.name || !formData.phone || !formData.symptom} className="w-full bg-blue-600 text-white p-4 rounded-lg font-bold text-lg hover:bg-blue-700 disabled:bg-gray-300 transition">
              {loading ? "AI Analyzing..." : "Generate Token"}
            </button>

            {triageReason && (
              <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-xs font-bold text-purple-800 mb-1">🤖 AI MEDICAL ASSISTANT TRIAGE:</p>
                <p className="text-sm text-purple-700">{triageReason}</p>
              </div>
            )}
          </div>

          <div className="flex flex-col items-center justify-center bg-gray-50 p-8 rounded-lg border border-gray-100">
            <p className="text-gray-500 uppercase tracking-widest text-sm mb-2">Current Live Queue</p>
            <p className="text-8xl font-bold text-gray-800 mb-2">{queueCount}</p>
            <p className="text-gray-500">people currently in queue</p>
          </div>
        </div>
      </div>

      <SmsSimulator message={smsMessage} onClose={() => setSmsMessage(null)} />
    </div>
  );
}