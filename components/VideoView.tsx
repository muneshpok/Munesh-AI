
import React, { useState } from 'react';
import { generateAstroVideo } from '../services/gemini';
import { Video, Loader2, PlayCircle, Download, Sparkles, Layers, Zap } from 'lucide-react';

const STYLES = [
  { id: 'cinematic', label: 'Cinematic Vedic', description: 'Epic, grand, movie-like lighting', prompt: 'cinematic grand scale, epic lighting, vedic aesthetics, 8k resolution' },
  { id: 'nebula', label: 'Neon Nebula', description: 'Vibrant, glowing, deep space', prompt: 'vibrant neon colors, glowing gas clouds, hyper-detailed nebula, synthwave vibe' },
  { id: 'ancient', label: 'Ancient Scroll', description: 'Traditional, parchment, ink-wash', prompt: 'ancient nepalese scroll style, hand-drawn, ink wash, mystical parchment texture' },
  { id: 'surreal', label: 'Dreamy Astral', description: 'Soft, ethereal, surrealism', prompt: 'ethereal atmosphere, soft focus, dream-like surrealism, floating celestial bodies' }
];

const PRESETS = [
  { label: 'Lunar Eclipse', prompt: 'A blood moon rising slowly through the constellations of the zodiac' },
  { label: 'Saturn Return', prompt: 'The rings of Saturn glowing intensely as it returns to its birth position' },
  { label: 'Star Birth', prompt: 'Gaseous clouds collapsing into a brilliant new blue star within a nebula' },
  { label: 'Cosmic Dance', prompt: 'Planetary alignments dancing in a rhythmic celestial clockwork' }
];

const VideoView: React.FC = () => {
  const [userPrompt, setUserPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState(STYLES[0]);
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16'>('16:9');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

  const handlePresetClick = (presetPrompt: string) => {
    setUserPrompt(presetPrompt);
  };

  const handleGenerate = async () => {
    const hasKey = await (window as any).aistudio?.hasSelectedApiKey();
    if (!hasKey) {
      await (window as any).aistudio?.openSelectKey();
      return;
    }

    setLoading(true);
    setLoadingMessage('Initializing neural cosmic engines...');
    
    const messages = [
      'Painting the celestial canvas...',
      'Aligning planetary pixels...',
      'Rendering divine frames...',
      'Almost there, gathering starlight...',
      'Synthesizing astral harmonics...'
    ];
    let msgIdx = 0;
    const interval = setInterval(() => {
      setLoadingMessage(messages[msgIdx % messages.length]);
      msgIdx++;
    }, 12000);

    // Final prompt engineering
    const finalPrompt = `${userPrompt || 'Celestial events in space'}. Style: ${selectedStyle.prompt}. Aspect Ratio: ${aspectRatio}.`;

    try {
      const url = await generateAstroVideo(finalPrompt, aspectRatio);
      setVideoUrl(url);
    } catch (e) {
      console.error(e);
      alert('Video generation failed. Please ensure you have selected a valid paid API key and have sufficient quota.');
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 h-full pb-12 animate-in fade-in duration-700">
      <div className="bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-900/30 rounded-3xl p-6 md:p-8 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <h2 className="font-cinzel text-2xl text-amber-400 flex items-center gap-3">
            <Video className="w-7 h-7" />
            Manifest Cosmic Visions
          </h2>
          <div className="flex bg-[#020617] p-1 rounded-xl border border-indigo-900/50">
            <button 
              onClick={() => setAspectRatio('16:9')}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${aspectRatio === '16:9' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500'}`}
            >
              Landscape (16:9)
            </button>
            <button 
              onClick={() => setAspectRatio('9:16')}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${aspectRatio === '9:16' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500'}`}
            >
              Portrait (9:16)
            </button>
          </div>
        </div>
        
        <div className="space-y-8">
          {/* Presets */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-slate-400">
              <Zap size={14} className="text-amber-500" />
              <span className="text-xs font-bold uppercase tracking-widest">Astrological Presets</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((p) => (
                <button
                  key={p.label}
                  onClick={() => handlePresetClick(p.prompt)}
                  className="px-4 py-2 rounded-full bg-indigo-500/5 border border-indigo-500/20 text-xs font-medium text-indigo-300 hover:bg-indigo-500/10 hover:border-indigo-400/40 transition-all"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Styles Selection */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-slate-400">
              <Layers size={14} className="text-amber-500" />
              <span className="text-xs font-bold uppercase tracking-widest">Visual Style Architect</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {STYLES.map((style) => (
                <button
                  key={style.id}
                  onClick={() => setSelectedStyle(style)}
                  className={`p-3 rounded-2xl border text-left transition-all group ${
                    selectedStyle.id === style.id 
                      ? 'bg-amber-500/10 border-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.1)]' 
                      : 'bg-[#020617] border-indigo-900/50 hover:border-indigo-500/30'
                  }`}
                >
                  <p className={`text-sm font-bold mb-1 ${selectedStyle.id === style.id ? 'text-amber-400' : 'text-slate-300'}`}>{style.label}</p>
                  <p className="text-[10px] text-slate-500 leading-tight">{style.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Custom Prompt */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-slate-400">
              <Sparkles size={14} className="text-amber-500" />
              <span className="text-xs font-bold uppercase tracking-widest">Personalized Intent</span>
            </div>
            <textarea 
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="w-full h-28 bg-[#020617] border border-indigo-900/50 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-amber-500/50 transition-all text-slate-200 placeholder:text-slate-600"
              placeholder="Describe the cosmic manifestion... E.g., 'A golden thread weaving through the planets...'"
            />
          </div>

          <button 
            onClick={handleGenerate}
            disabled={loading}
            className="group relative w-full overflow-hidden bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-black font-bold py-5 rounded-2xl transition-all shadow-xl hover:shadow-amber-500/20"
          >
            <div className="relative flex items-center justify-center gap-3">
              {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : <PlayCircle className="w-6 h-6 transition-transform group-hover:scale-110" />}
              <span className="text-lg uppercase tracking-widest">{loading ? 'Synthesizing Vision...' : 'Manifest Video'}</span>
            </div>
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-24 animate-in fade-in zoom-in duration-500">
          <div className="relative w-32 h-32 mb-8">
            <div className="absolute inset-0 border-4 border-amber-500/10 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
            <div className="absolute inset-4 border-4 border-indigo-500/20 rounded-full animate-pulse"></div>
            <Video className="absolute inset-0 m-auto w-10 h-10 text-amber-500" />
          </div>
          <h3 className="text-2xl font-cinzel text-amber-400 mb-3">{loadingMessage}</h3>
          <p className="text-slate-500 text-sm text-center max-w-sm leading-relaxed px-4">
            Creating high-dimensional temporal textures using <span className="text-indigo-400 font-bold">Veo 3.1</span>. This usually takes 1 to 3 minutes. Please remain centered.
          </p>
        </div>
      )}

      {videoUrl && !loading && (
        <div className="animate-in slide-in-from-bottom duration-1000 bg-[#0a0a2a] rounded-[2.5rem] p-4 border border-amber-500/20 overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
          <video src={videoUrl} controls autoPlay loop className="w-full rounded-[2rem] shadow-2xl" />
          <div className="mt-6 flex flex-col md:flex-row justify-between items-center px-4 pb-4 gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <Sparkles className="text-amber-500 w-5 h-5" />
              </div>
              <div>
                <p className="text-slate-200 font-bold text-sm">Celestial Manifestation Successful</p>
                <p className="text-slate-500 text-[10px] uppercase tracking-widest">{selectedStyle.label} • {aspectRatio}</p>
              </div>
            </div>
            <a 
              href={videoUrl} 
              download="munesh-cosmic-vision.mp4"
              className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white px-6 py-2.5 rounded-xl border border-white/10 transition-all font-medium text-sm"
            >
              <Download className="w-4 h-4" />
              Download Vision
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoView;
