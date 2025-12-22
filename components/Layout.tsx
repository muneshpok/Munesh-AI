
import React from 'react';
import { AppView } from '../types';
import { 
  Moon, MessageSquare, Video, Mic, Camera, MapPin, Star, 
  LineChart, Heart, Clock, Sparkles, Music 
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeView: AppView;
  setActiveView: (view: AppView) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, activeView, setActiveView }) => {
  const navItems = [
    { id: AppView.PROFILE, icon: Star, label: 'Profile' },
    { id: AppView.FORECAST, icon: LineChart, label: 'Timeline' },
    { id: AppView.COMPATIBILITY, icon: Heart, label: 'Gun Milan' },
    { id: AppView.MUHURTA, icon: Clock, label: 'Muhurta' },
    { id: AppView.DREAMS, icon: Sparkles, label: 'Dream Oracle' },
    { id: AppView.MANTRAS, icon: Music, label: 'Mantra' },
    { id: AppView.CHAT, icon: MessageSquare, label: 'Guru Chat' },
    { id: AppView.VIDEO, icon: Video, label: 'Vision' },
    { id: AppView.LIVE, icon: Mic, label: 'Live' },
    { id: AppView.AURA, icon: Camera, label: 'Aura' },
    { id: AppView.MAPS, icon: MapPin, label: 'Temples' },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-[#020617] text-slate-200">
      <nav className="w-20 md:w-64 bg-[#0a0a2a] border-r border-indigo-900/30 flex flex-col items-center py-6 overflow-y-auto no-scrollbar">
        <div className="flex items-center gap-3 mb-10 px-4 shrink-0">
          <Moon className="w-8 h-8 text-amber-400 fill-amber-400" />
          <div className="hidden md:flex flex-col">
            <h1 className="font-cinzel text-sm font-bold tracking-widest text-amber-400 leading-none">MUNESH AI</h1>
            <span className="font-cinzel text-[10px] tracking-[0.2em] text-indigo-400 mt-1 uppercase">Celestial</span>
          </div>
        </div>
        <ul className="w-full space-y-1 px-2">
          {navItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => setActiveView(item.id)}
                className={`w-full flex items-center justify-center md:justify-start gap-4 px-4 py-2.5 rounded-xl transition-all ${
                  activeView === item.id 
                    ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-[0_0_15px_rgba(79,70,229,0.1)]' 
                    : 'hover:bg-indigo-900/10 text-slate-400'
                }`}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                <span className="hidden md:block text-sm font-medium">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <main className="flex-1 overflow-y-auto bg-gradient-to-br from-[#020617] via-[#050b1d] to-[#0a0a2a]">
        <div className="max-w-6xl mx-auto p-4 md:p-8 h-full">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;