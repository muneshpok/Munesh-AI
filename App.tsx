
import React, { useState } from 'react';
import Layout from './components/Layout';
import { AppView, BirthDetails, AstroReport } from './types';
import { calculateAstroProfile, speakText, decodeBase64, decodeAudioData } from './services/gemini';
import { Star, Loader2, Sparkles, Volume2, Calendar } from 'lucide-react';

import ChatView from './components/ChatView';
import VideoView from './components/VideoView';
import LiveView from './components/LiveView';
import AuraView from './components/AuraView';
import MapsView from './components/MapsView';
import ForecastView from './components/ForecastView';
import CompatibilityView from './components/CompatibilityView';
import MuhurtaView from './components/MuhurtaView';
import DreamView from './components/DreamView';
import MantraView from './components/MantraView';
import DailyAffirmation from './components/DailyAffirmation';

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<AppView>(AppView.PROFILE);
  const [birthDetails, setBirthDetails] = useState<BirthDetails>({
    bsDate: { year: 2050, month: 1, day: 1 },
    time: "12:00",
    place: "Kathmandu, Nepal"
  });
  const [report, setReport] = useState<AstroReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const res = await calculateAstroProfile(birthDetails);
      setReport(res);
      setTimeout(() => setActiveView(AppView.FORECAST), 800);
    } catch (error) {
      console.error(error);
      alert("Error calculating profile.");
    } finally {
      setLoading(false);
    }
  };

  const handleTTS = async (text: string) => {
    if (isSpeaking) return;
    setIsSpeaking(true);
    try {
      const audioBase64 = await speakText(text);
      if (audioBase64) {
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
        const decoded = decodeBase64(audioBase64);
        const buffer = await decodeAudioData(decoded, audioCtx, 24000, 1);
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(audioCtx.destination);
        source.onended = () => setIsSpeaking(false);
        source.start();
      }
    } catch (e) {
      setIsSpeaking(false);
    }
  };

  const renderProfile = () => (
    <div className="space-y-8 animate-in fade-in duration-500 pb-12">
      {/* Personalized Affirmation Section */}
      <DailyAffirmation moonSign={report?.moonSign} />

      <div className="bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-900/30 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        <h2 className="font-cinzel text-3xl mb-8 text-amber-400 flex items-center gap-3 relative">
          <Star className="w-8 h-8 fill-amber-400" />
          Birth Identity (Bikram Sambat)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Year (BS)</label>
            <input type="number" value={birthDetails.bsDate.year} onChange={(e) => setBirthDetails({...birthDetails, bsDate: {...birthDetails.bsDate, year: parseInt(e.target.value)}})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none transition-all" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Month (BS)</label>
            <select value={birthDetails.bsDate.month} onChange={(e) => setBirthDetails({...birthDetails, bsDate: {...birthDetails.bsDate, month: parseInt(e.target.value)}})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none transition-all">
              {['Baishakh', 'Jestha', 'Ashadh', 'Shrawan', 'Bhadra', 'Ashwin', 'Kartik', 'Mangshir', 'Poush', 'Magh', 'Falgun', 'Chaitra'].map((m, i) => (
                <option key={m} value={i + 1}>{i + 1}. {m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Day (BS)</label>
            <input type="number" value={birthDetails.bsDate.day} onChange={(e) => setBirthDetails({...birthDetails, bsDate: {...birthDetails.bsDate, day: parseInt(e.target.value)}})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none transition-all" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="group">
            <label className="block text-sm font-medium text-slate-400 mb-2">Time of Birth</label>
            <input type="time" value={birthDetails.time} onChange={(e) => setBirthDetails({...birthDetails, time: e.target.value})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none focus:ring-1 focus:ring-indigo-500" />
          </div>
          <div className="group">
            <label className="block text-sm font-medium text-slate-400 mb-2">Place of Birth</label>
            <input type="text" value={birthDetails.place} onChange={(e) => setBirthDetails({...birthDetails, place: e.target.value})} className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none focus:ring-1 focus:ring-indigo-500" placeholder="City, Country" />
          </div>
        </div>
        <button onClick={handleCalculate} disabled={loading} className="w-full bg-gradient-to-r from-indigo-600 via-purple-600 to-amber-600 py-5 rounded-2xl font-bold text-lg shadow-xl hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-3">
          {loading ? <Loader2 className="animate-spin w-6 h-6" /> : <Sparkles className="w-6 h-6" />}
          {loading ? 'Consulting the Heavens...' : 'Reveal Destiny & Path'}
        </button>
      </div>

      {report && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 animate-in slide-in-from-bottom duration-700">
          <div className="bg-[#0a0a2a]/60 border border-amber-500/20 rounded-3xl p-8 relative overflow-hidden group">
            <div className="absolute -bottom-12 -right-12 w-32 h-32 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-all"></div>
            <div className="flex justify-between items-start mb-6">
               <h3 className="text-amber-400 font-cinzel text-2xl">Moon: {report.moonSign}</h3>
               <button onClick={() => handleTTS(report.prediction)} className="p-2 bg-amber-500/10 rounded-lg text-amber-500 hover:bg-amber-500/20 transition-all">
                  <Volume2 size={20} />
               </button>
            </div>
            <p className="text-slate-300 italic leading-relaxed text-lg">"{report.prediction}"</p>
          </div>
          <div className="bg-[#0a0a2a]/60 border border-indigo-500/20 rounded-3xl p-8">
            <h3 className="text-indigo-400 font-cinzel text-2xl mb-6">Nakshatra: {report.nakshatra}</h3>
            <div className="space-y-4">
              {report.remedies.map((r, i) => (
                <div key={i} className="flex gap-3 text-sm text-slate-300 bg-indigo-500/5 border border-indigo-500/10 p-3 rounded-xl">
                  <span className="text-indigo-400 font-bold">{i + 1}.</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <Layout activeView={activeView} setActiveView={setActiveView}>
      {activeView === AppView.PROFILE && renderProfile()}
      {activeView === AppView.FORECAST && <ForecastView report={report} />}
      {activeView === AppView.COMPATIBILITY && <CompatibilityView />}
      {activeView === AppView.MUHURTA && <MuhurtaView />}
      {activeView === AppView.DREAMS && <DreamView report={report} />}
      {activeView === AppView.MANTRAS && <MantraView report={report} />}
      {activeView === AppView.CHAT && <ChatView />}
      {activeView === AppView.VIDEO && <VideoView />}
      {activeView === AppView.LIVE && <LiveView />}
      {activeView === AppView.AURA && <AuraView />}
      {activeView === AppView.MAPS && <MapsView />}
    </Layout>
  );
};

export default App;
