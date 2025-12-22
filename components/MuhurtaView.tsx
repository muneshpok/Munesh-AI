
import React, { useState } from 'react';
import { findMuhurta } from '../services/gemini';
import { Clock, Loader2, Sparkles } from 'lucide-react';

const MuhurtaView: React.FC = () => {
  const [purpose, setPurpose] = useState('New House Inaugration');
  const [range, setRange] = useState('Baishakh 2081 - Jestha 2081');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const res = await findMuhurta(purpose, range);
      setResults(res.options);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <h2 className="font-cinzel text-3xl text-indigo-400 flex items-center gap-3">
        <Clock /> Auspicious Muhurta
      </h2>
      <div className="bg-[#0a0a2a]/60 p-8 rounded-3xl border border-indigo-900/30 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <input value={purpose} onChange={e => setPurpose(e.target.value)} className="bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3" placeholder="Purpose of Muhurta" />
          <input value={range} onChange={e => setRange(e.target.value)} className="bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3" placeholder="BS Date Range" />
        </div>
        <button onClick={handleSearch} disabled={loading} className="w-full bg-indigo-600 py-4 rounded-xl font-bold flex items-center justify-center gap-2">
          {loading ? <Loader2 className="animate-spin" /> : <Sparkles />} Find Best Timings
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {results?.map((opt: any, i: number) => (
          <div key={i} className="bg-[#0a0a2a] p-6 rounded-2xl border border-indigo-500/20 flex flex-col md:flex-row gap-6">
            <div className="md:w-1/3 border-b md:border-b-0 md:border-r border-white/5 pb-4 md:pb-0">
              <p className="text-amber-400 font-bold text-xl mb-1">{opt.time}</p>
              <p className="text-slate-500 text-xs">{opt.tithi} | {opt.nakshatra}</p>
            </div>
            <p className="flex-1 text-slate-300 italic">"{opt.reason}"</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MuhurtaView;
