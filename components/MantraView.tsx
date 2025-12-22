
import React, { useState } from 'react';
import { generateMantraAudio, decodeBase64, decodeAudioData } from '../services/gemini';
import { Music, Play, Loader2, Volume2 } from 'lucide-react';

const MantraView: React.FC<{ report: any }> = ({ report }) => {
  const [loading, setLoading] = useState(false);

  const playMantra = async () => {
    if (!report) return alert("Calculate Profile First!");
    setLoading(true);
    try {
      const base64 = await generateMantraAudio(report.moonSign);
      if (base64) {
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
        const decoded = decodeBase64(base64);
        const buffer = await decodeAudioData(decoded, audioCtx, 24000, 1);
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(audioCtx.destination);
        source.start();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full space-y-8 py-12">
      <div className="bg-indigo-600/10 p-12 rounded-full border-2 border-indigo-500/20 animate-pulse">
        <Music className="w-24 h-24 text-indigo-400" />
      </div>
      <div className="text-center max-w-lg">
        <h2 className="font-cinzel text-4xl text-amber-400 mb-4">Mantra Siddhi</h2>
        <p className="text-slate-400 leading-relaxed">
          The vibrational resonance of specific Beej Mantras can realign your cosmic energy. 
          Generate a personalized audio remedy based on your Moon Sign.
        </p>
      </div>
      <button 
        onClick={playMantra} disabled={loading}
        className="px-12 py-5 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl font-bold flex items-center gap-4 text-xl shadow-2xl hover:scale-105 transition-all"
      >
        {loading ? <Loader2 className="animate-spin" /> : <><Volume2 /> Invoke Sacred Sound</>}
      </button>
      {report && <p className="text-xs text-indigo-500 font-bold tracking-widest uppercase">Tuned to {report.moonSign} Rashi</p>}
    </div>
  );
};

export default MantraView;
