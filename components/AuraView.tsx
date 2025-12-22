
import React, { useState, useRef } from 'react';
import { analyzeAura, editAura } from '../services/gemini';
import { Camera, Upload, Sparkles, Wand2, Loader2, Image as ImageIcon } from 'lucide-react';

const AuraView: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [editPrompt, setEditPrompt] = useState('Add a mystical golden aura around the subject and cosmic nebulae in the background');
  const [loading, setLoading] = useState<'analyzing' | 'editing' | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const base64 = ev.target?.result as string;
        setImage(base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = async () => {
    if (!image) return;
    setLoading('analyzing');
    try {
      const base64Data = image.split(',')[1];
      const res = await analyzeAura(base64Data, "Analyze this person's 'aura' based on their expression and colors. Suggest a spiritual path or celestial alignment for them.");
      setAnalysis(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(null);
    }
  };

  const handleEdit = async () => {
    if (!image) return;
    setLoading('editing');
    try {
      const base64Data = image.split(',')[1];
      const newUrl = await editAura(base64Data, editPrompt);
      if (newUrl) setImage(newUrl);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
      <div className="bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-900/30 rounded-3xl p-8 flex flex-col h-fit">
        <h2 className="font-cinzel text-2xl text-amber-400 mb-6 flex items-center gap-3">
          <Camera className="w-7 h-7" />
          Aura Vision
        </h2>
        
        <div className="relative aspect-square w-full bg-[#020617] rounded-2xl border-2 border-dashed border-indigo-900/50 flex items-center justify-center overflow-hidden mb-6 group">
          {image ? (
            <>
              <img src={image} alt="Target" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button onClick={() => fileInputRef.current?.click()} className="p-4 bg-white/20 backdrop-blur rounded-full">
                  <Upload className="w-8 h-8 text-white" />
                </button>
              </div>
            </>
          ) : (
            <button onClick={() => fileInputRef.current?.click()} className="flex flex-col items-center gap-3 text-slate-500 hover:text-indigo-400 transition-colors">
              <ImageIcon className="w-16 h-16 opacity-30" />
              <span className="font-medium">Upload Birth Photo or Portrait</span>
            </button>
          )}
          <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept="image/*" />
        </div>

        <div className="flex gap-4">
          <button 
            disabled={!image || loading !== null}
            onClick={handleAnalyze}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
          >
            {loading === 'analyzing' ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
            Analyze Aura
          </button>
        </div>
      </div>

      <div className="space-y-8">
        {analysis && (
          <div className="bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-500/30 rounded-3xl p-8 animate-in slide-in-from-right duration-500">
            <h3 className="font-cinzel text-xl text-indigo-400 mb-4">Celestial Reading</h3>
            <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">{analysis}</p>
          </div>
        )}

        <div className="bg-[#0a0a2a]/60 backdrop-blur-xl border border-amber-500/20 rounded-3xl p-8">
          <h3 className="font-cinzel text-xl text-amber-400 mb-4 flex items-center gap-2">
            <Wand2 className="w-5 h-5" />
            Transmute Image
          </h3>
          <div className="space-y-4">
            <input 
              type="text" 
              value={editPrompt}
              onChange={(e) => setEditPrompt(e.target.value)}
              className="w-full bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none focus:ring-1 focus:ring-amber-500"
              placeholder="E.g., Make the background look like deep space..."
            />
            <button 
              disabled={!image || loading !== null}
              onClick={handleEdit}
              className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold py-3 rounded-xl flex items-center justify-center gap-2"
            >
              {loading === 'editing' ? <Loader2 className="w-5 h-5 animate-spin" /> : <Wand2 className="w-5 h-5" />}
              Apply Transformation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuraView;
