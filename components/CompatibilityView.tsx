
import React, { useState } from 'react';
import { checkCompatibility } from '../services/gemini';
import { Heart, Loader2, MinusCircle, PlusCircle } from 'lucide-react';

const CompatibilityView: React.FC = () => {
  const [p1, setP1] = useState({ year: 2050, month: 1, day: 1, time: '12:00', place: 'Kathmandu' });
  const [p2, setP2] = useState({ year: 2052, month: 1, day: 1, time: '12:00', place: 'Kathmandu' });
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCheck = async () => {
    setLoading(true);
    try {
      const res = await checkCompatibility(p1, p2);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <h2 className="font-cinzel text-3xl text-pink-400 flex items-center gap-3">
        <Heart className="fill-pink-400" /> Gun Milan Compatibility
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-[#0a0a2a]/60 p-6 rounded-3xl border border-indigo-900/30">
          <h3 className="text-slate-400 mb-4 font-bold uppercase tracking-widest text-xs">Person One</h3>
          <div className="space-y-4">
             <input type="number" value={p1.year} onChange={e => setP1({...p1, year: +e.target.value})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-2" placeholder="Year" />
             <input type="text" value={p1.place} onChange={e => setP1({...p1, place: e.target.value})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-2" placeholder="Place" />
          </div>
        </div>
        <div className="bg-[#0a0a2a]/60 p-6 rounded-3xl border border-indigo-900/30">
          <h3 className="text-slate-400 mb-4 font-bold uppercase tracking-widest text-xs">Person Two</h3>
          <div className="space-y-4">
             <input type="number" value={p2.year} onChange={e => setP2({...p2, year: +e.target.value})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-2" placeholder="Year" />
             <input type="text" value={p2.place} onChange={e => setP2({...p2, place: e.target.value})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-2" placeholder="Place" />
          </div>
        </div>
      </div>
      <button onClick={handleCheck} disabled={loading} className="w-full bg-pink-600 py-4 rounded-xl font-bold flex items-center justify-center gap-2">
        {loading ? <Loader2 className="animate-spin" /> : "Check Harmony Score"}
      </button>

      {result && (
        <div className="bg-[#0a0a2a] p-8 rounded-3xl border border-pink-500/20">
          <div className="text-center mb-8">
            <p className="text-slate-500 uppercase tracking-widest text-sm">Harmony Score</p>
            <h4 className="text-6xl font-bold text-pink-400">{result.score}<span className="text-2xl text-slate-600">/36</span></h4>
          </div>
          <p className="text-slate-300 italic mb-8 border-l-4 border-pink-500 pl-4">{result.analysis}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-3">
              <h5 className="text-green-400 flex items-center gap-2"><PlusCircle size={18} /> Divine Alignments</h5>
              {result.pros.map((p: string, i: number) => <p key={i} className="text-sm text-slate-400">• {p}</p>)}
            </div>
            <div className="space-y-3">
              <h5 className="text-red-400 flex items-center gap-2"><MinusCircle size={18} /> Potential Friction</h5>
              {result.cons.map((c: string, i: number) => <p key={i} className="text-sm text-slate-400">• {c}</p>)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompatibilityView;
