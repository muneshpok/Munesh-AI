
import React, { useState, useRef, useEffect } from 'react';
import { chatWithGuru } from '../services/gemini';
import { Send, User, Bot, Loader2 } from 'lucide-react';

const ChatView: React.FC = () => {
  const [messages, setMessages] = useState<{role: 'user' | 'bot', text: string}[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const botResponse = await chatWithGuru(userMsg, messages);
      setMessages(prev => [...prev, { role: 'bot', text: botResponse }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'bot', text: "The stars are cloudy right now. Please try again later." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[80vh]">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <Bot className="w-16 h-16 text-indigo-400 mx-auto mb-4 opacity-50" />
            <h3 className="font-cinzel text-2xl text-slate-300">Ask the Guru</h3>
            <p className="text-slate-500">Inquire about your destiny, planetary alignments, or spiritual growth.</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl flex gap-3 ${
              m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-[#0a0a2a] border border-indigo-900/30 text-slate-200 rounded-tl-none'
            }`}>
              {m.role === 'bot' && <Bot className="w-5 h-5 shrink-0 text-amber-400" />}
              <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
              {m.role === 'user' && <User className="w-5 h-5 shrink-0 opacity-50" />}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#0a0a2a] p-4 rounded-2xl flex gap-3 animate-pulse">
              <Loader2 className="w-5 h-5 animate-spin text-amber-400" />
              <p className="text-slate-400">Consulting the heavens...</p>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      <div className="p-4 bg-[#0a0a2a]/60 backdrop-blur-xl border border-indigo-900/30 rounded-2xl">
        <div className="flex gap-2">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your question..."
            className="flex-1 bg-[#020617] border border-indigo-900/50 rounded-xl px-4 py-3 outline-none focus:ring-1 focus:ring-amber-500"
          />
          <button 
            onClick={handleSend}
            disabled={loading}
            className="bg-amber-500 hover:bg-amber-600 text-black font-bold px-6 py-3 rounded-xl transition-all"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatView;
