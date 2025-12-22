
import React, { useState } from 'react';
import { findSpiritualPlaces } from '../services/gemini';
import { MapPin, Search, Loader2, ExternalLink } from 'lucide-react';

const MapsView: React.FC = () => {
  const [query, setQuery] = useState('Find historical temples near Kathmandu dedicated to Lord Shiva');
  const [results, setResults] = useState<{text: string, chunks: any[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      // In a real app, we'd use navigator.geolocation
      const res = await findSpiritualPlaces(query);
      setResults(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 h-full">
      <div className="bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-900/30 rounded-3xl p-8">
        <h2 className="font-cinzel text-2xl text-amber-400 mb-6 flex items-center gap-3">
          <MapPin className="w-7 h-7" />
          Pilgrimage Finder
        </h2>
        
        <div className="flex gap-2">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none focus:ring-1 focus:ring-amber-500"
            placeholder="Search for temples, ashrams, or astrologers..."
          />
          <button 
            onClick={handleSearch}
            disabled={loading}
            className="bg-amber-500 hover:bg-amber-600 text-black font-bold px-6 py-3 rounded-xl transition-all"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {results && (
        <div className="space-y-6">
          <div className="bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-900/30 rounded-3xl p-8">
            <h3 className="font-cinzel text-xl text-indigo-400 mb-4">Divine Destinations</h3>
            <p className="text-slate-300 whitespace-pre-wrap leading-relaxed mb-8">{results.text}</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.chunks.map((chunk, idx) => chunk.maps && (
                <a 
                  key={idx}
                  href={chunk.maps.uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-[#020617] border border-indigo-900/50 p-4 rounded-2xl flex items-center justify-between hover:border-amber-500/50 transition-all group"
                >
                  <div>
                    <p className="font-bold text-slate-200">{chunk.maps.title || 'Spiritual Landmark'}</p>
                    <p className="text-xs text-slate-500 truncate max-w-[200px]">{chunk.maps.uri}</p>
                  </div>
                  <ExternalLink className="w-5 h-5 text-indigo-400 group-hover:text-amber-500" />
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapsView;
