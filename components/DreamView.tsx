
import React, { useState } from 'react';
import { interpretDream } from '../services/gemini';
import { Sparkles, Loader2, Moon } from 'lucide-react';

const DreamView: React.FC<{ report: any }> = ({ report }) => {
  const [desc, setDesc] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleInterpret = async () => {
    if (!report) return alert("Calculate Profile First!");
    setLoading(true);
    try {
      const res = await interpretDream(desc, report.moonSign);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <h2 className="font-cinzel text-3xl text-purple-400 flex items-center gap-3">
        <Moon className="fill-purple-400" /> Dream Oracle
      </h2>
      <div className="bg-[#0a0a2a]/60 p-8 rounded-3xl border border-purple-900/30 space-y-4">
        <textarea 
          value={desc} onChange={e => setDesc(e.target.value)}
          className="w-full h-32 bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none"
          placeholder="Describe your dream in detail..."
        />
        <button onClick={handleInterpret} disabled={loading} className="w-full bg-purple-600 py-4 rounded-xl font-bold flex items-center justify-center gap-2">
          {loading ? <Loader2 className="animate-spin" /> : "Decode Celestial Message"}
        </button>
      </div>
      {result && (
        <div className="bg-purple-900/10 p-8 rounded-3xl border border-purple-500/20 animate-in slide-in-from-bottom">
           <p className="text-slate-200 leading-relaxed text-lg italic">"{result.interpretation}"</p>
        </div>
      )}
    </div>
  );
};

export default DreamView;
