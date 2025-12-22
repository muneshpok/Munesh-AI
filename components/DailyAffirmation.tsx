
import React, { useState, useEffect } from 'react';
import { getDailyAffirmation, speakText, decodeBase64, decodeAudioData } from '../services/gemini';
import { Quote, Volume2, Loader2, Sparkles, Copy, Check } from 'lucide-react';

interface DailyAffirmationProps {
  moonSign?: string;
}

const DailyAffirmation: React.FC<DailyAffirmationProps> = ({ moonSign }) => {
  const [affirmation, setAffirmation] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [speaking, setSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchAffirmation = async () => {
      setLoading(true);
      try {
        const text = await getDailyAffirmation(moonSign);
        setAffirmation(text || '');
      } catch (e) {
        setAffirmation("Today, I align my actions with the rhythm of the cosmos.");
      } finally {
        setLoading(false);
      }
    };
    fetchAffirmation();
  }, [moonSign]);

  const handleSpeak = async () => {
    if (speaking || !affirmation) return;
    setSpeaking(true);
    try {
      const audioBase64 = await speakText(affirmation);
      if (audioBase64) {
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
        const decoded = decodeBase64(audioBase64);
        const buffer = await decodeAudioData(decoded, audioCtx, 24000, 1);
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(audioCtx.destination);
        source.onended = () => setSpeaking(false);
        source.start();
      }
    } catch (e) {
      setSpeaking(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(affirmation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative overflow-hidden group">
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-amber-500/10 rounded-3xl blur-xl"></div>
      <div className="relative bg-[#0a0a2a]/60 backdrop-blur-xl border border-white/10 rounded-3xl p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 shadow-2xl transition-all hover:border-indigo-500/30">
        <div className="flex-shrink-0 w-16 h-16 bg-indigo-600/20 rounded-2xl flex items-center justify-center text-indigo-400 border border-indigo-500/20 group-hover:scale-110 transition-transform duration-500">
          <Quote size={32} />
        </div>
        
        <div className="flex-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
            <Sparkles size={14} className="text-amber-400" />
            <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Daily Celestial Blessing</span>
            {moonSign && <span className="text-[10px] bg-amber-500/20 text-amber-500 px-2 py-0.5 rounded-full uppercase font-bold tracking-tighter">For {moonSign}</span>}
          </div>
          
          {loading ? (
            <div className="h-6 w-3/4 bg-white/5 animate-pulse rounded"></div>
          ) : (
            <p className="text-xl md:text-2xl font-cinzel text-white leading-snug">
              {affirmation}
            </p>
          )}
        </div>

        <div className="flex gap-2 shrink-0">
          <button 
            onClick={handleSpeak}
            disabled={loading || speaking}
            className={`p-3 rounded-xl border transition-all ${speaking ? 'bg-amber-500 border-amber-400 text-white animate-pulse' : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white'}`}
            title="Hear Affirmation"
          >
            {speaking ? <Loader2 size={20} className="animate-spin" /> : <Volume2 size={20} />}
          </button>
          <button 
            onClick={handleCopy}
            disabled={loading}
            className="p-3 rounded-xl border bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white transition-all"
            title="Copy to Clipboard"
          >
            {copied ? <Check size={20} className="text-green-400" /> : <Copy size={20} />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DailyAffirmation;
