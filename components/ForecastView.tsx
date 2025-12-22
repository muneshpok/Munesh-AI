
import React, { useState } from 'react';
import { AstroReport, ForecastItem } from '../types';
import { Calendar, Clock, BarChart3, Star, AlertCircle } from 'lucide-react';

interface ForecastViewProps {
  report: AstroReport | null;
}

const ForecastView: React.FC<ForecastViewProps> = ({ report }) => {
  const [tab, setTab] = useState<'daily' | 'monthly' | 'yearly'>('daily');

  if (!report) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4 text-center">
        <div className="p-6 bg-indigo-500/10 rounded-full">
          <Calendar className="w-12 h-12 text-indigo-400" />
        </div>
        <h2 className="font-cinzel text-2xl text-slate-300">No Cosmic Data</h2>
        <p className="text-slate-500 max-w-sm">Please calculate your Moon Sign in the Profile tab first to reveal your future timeline.</p>
      </div>
    );
  }

  const getForecastData = () => {
    if (tab === 'daily') return report.dailyForecast;
    if (tab === 'monthly') return report.monthlyForecast;
    return report.yearlyForecast;
  };

  const getIntensityColor = (intensity: number) => {
    if (intensity >= 8) return 'bg-amber-500';
    if (intensity >= 5) return 'bg-indigo-500';
    return 'bg-slate-600';
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <h2 className="font-cinzel text-3xl text-amber-400 flex items-center gap-3">
          <BarChart3 className="w-8 h-8" />
          Celestial Timeline
        </h2>

        <div className="flex bg-[#0a0a2a] p-1 rounded-xl border border-indigo-900/30 self-stretch md:self-auto">
          {(['daily', 'monthly', 'yearly'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 md:flex-none px-6 py-2 rounded-lg text-sm font-bold transition-all capitalize ${
                tab === t 
                  ? 'bg-indigo-600 text-white shadow-lg' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {getForecastData().map((item, idx) => (
          <div key={idx} className="group bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-900/30 rounded-3xl p-6 hover:border-indigo-500/30 transition-all flex flex-col md:flex-row gap-6 relative overflow-hidden">
            <div className="md:w-48 shrink-0 flex flex-col justify-center border-b md:border-b-0 md:border-r border-indigo-900/20 pb-4 md:pb-0">
              <span className="text-xs uppercase tracking-widest font-bold text-slate-500 mb-1">
                {tab === 'daily' ? 'Day' : tab === 'monthly' ? 'Month' : 'Year'}
              </span>
              <p className="text-2xl font-cinzel text-white group-hover:text-amber-400 transition-colors">{item.period}</p>
              <div className="mt-3 flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold text-white uppercase ${getIntensityColor(item.intensity)}`}>
                  LVL {item.intensity}
                </span>
                <span className="text-xs text-indigo-400 font-medium">#{item.theme}</span>
              </div>
            </div>

            <div className="flex-1 space-y-3">
              <div className="flex items-start gap-3">
                <Star className="w-5 h-5 text-amber-400 shrink-0 mt-1" />
                <p className="text-slate-300 leading-relaxed italic">"{item.prediction}"</p>
              </div>
            </div>

            {/* Intensity Progress Bar */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-indigo-900/20">
              <div 
                className={`h-full ${getIntensityColor(item.intensity)} transition-all duration-1000`} 
                style={{ width: `${item.intensity * 10}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="bg-amber-500/5 border border-amber-500/10 rounded-2xl p-6 flex gap-4 items-center">
        <AlertCircle className="w-6 h-6 text-amber-500 shrink-0" />
        <p className="text-sm text-slate-400 italic">
          Cosmic energies are calculated based on your unique transit path for the next 5 years (2081-2086 BS). These forecasts are intended for spiritual guidance and should be used alongside personal intuition.
        </p>
      </div>
    </div>
  );
};

export default ForecastView;
