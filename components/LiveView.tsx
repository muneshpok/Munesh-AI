
import React, { useState, useEffect, useRef } from 'react';
import { getAI, decodeBase64, decodeAudioData } from '../services/gemini';
import { Mic, MicOff, Waves, Radio, Loader2 } from 'lucide-react';
import { Modality } from '@google/genai';

const LiveView: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [transcription, setTranscription] = useState<string[]>([]);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const sessionRef = useRef<any>(null);
  const nextStartTimeRef = useRef(0);
  const sourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());

  const encodePCM = (data: Float32Array): string => {
    const l = data.length;
    const int16 = new Int16Array(l);
    for (let i = 0; i < l; i++) {
      int16[i] = data[i] * 32768;
    }
    const bytes = new Uint8Array(int16.buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  };

  const stopSession = () => {
    if (sessionRef.current) sessionRef.current.close();
    if (audioContextRef.current) audioContextRef.current.close();
    sourcesRef.current.forEach(s => s.stop());
    sourcesRef.current.clear();
    setIsActive(false);
    setLoading(false);
  };

  const startSession = async () => {
    setLoading(true);
    try {
      const ai = getAI();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const inputCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      const outputCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      audioContextRef.current = outputCtx;

      const sessionPromise = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        callbacks: {
          onopen: () => {
            const source = inputCtx.createMediaStreamSource(stream);
            const processor = inputCtx.createScriptProcessor(4096, 1, 1);
            processor.onaudioprocess = (e) => {
              const inputData = e.inputBuffer.getChannelData(0);
              const base64 = encodePCM(inputData);
              sessionPromise.then(session => {
                session.sendRealtimeInput({ media: { data: base64, mimeType: 'audio/pcm;rate=16000' } });
              });
            };
            source.connect(processor);
            processor.connect(inputCtx.destination);
            setIsActive(true);
            setLoading(false);
          },
          onmessage: async (msg) => {
            if (msg.serverContent?.outputTranscription) {
              setTranscription(prev => [...prev.slice(-4), `Guru: ${msg.serverContent?.outputTranscription?.text}`]);
            }
            if (msg.serverContent?.inputTranscription) {
              setTranscription(prev => [...prev.slice(-4), `You: ${msg.serverContent?.inputTranscription?.text}`]);
            }

            const audioData = msg.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
            if (audioData) {
              nextStartTimeRef.current = Math.max(nextStartTimeRef.current, outputCtx.currentTime);
              const decoded = decodeBase64(audioData);
              const buffer = await decodeAudioData(decoded, outputCtx, 24000, 1);
              const source = outputCtx.createBufferSource();
              source.buffer = buffer;
              source.connect(outputCtx.destination);
              source.onended = () => sourcesRef.current.delete(source);
              source.start(nextStartTimeRef.current);
              nextStartTimeRef.current += buffer.duration;
              sourcesRef.current.add(source);
            }

            if (msg.serverContent?.interrupted) {
              sourcesRef.current.forEach(s => s.stop());
              sourcesRef.current.clear();
              nextStartTimeRef.current = 0;
            }
          },
          onerror: (e) => console.error('Live error:', e),
          onclose: () => setIsActive(false),
        },
        config: {
          responseModalities: [Modality.AUDIO],
          systemInstruction: 'You are a wise Vedic astrologer in a live session. Use a calm, meditative tone. Provide real-time guidance on current planetary energies and Bikram Sambat wisdom.',
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } } },
          inputAudioTranscription: {},
          outputAudioTranscription: {}
        }
      });
      sessionRef.current = await sessionPromise;
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full space-y-8 py-12">
      <div className="relative">
        <div className={`w-48 h-48 rounded-full flex items-center justify-center transition-all duration-700 ${
          isActive ? 'bg-indigo-600/20 scale-110' : 'bg-[#0a0a2a]/60'
        }`}>
          {isActive && (
            <div className="absolute inset-0 rounded-full border-4 border-indigo-500 animate-ping opacity-20"></div>
          )}
          <button 
            onClick={isActive ? stopSession : startSession}
            disabled={loading}
            className={`w-32 h-32 rounded-full flex items-center justify-center transition-all ${
              isActive ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-2xl shadow-indigo-500/20'
            }`}
          >
            {loading ? <Loader2 className="w-12 h-12 animate-spin" /> : (isActive ? <MicOff className="w-12 h-12" /> : <Mic className="w-12 h-12" />)}
          </button>
        </div>
        {isActive && (
          <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 flex gap-1">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="w-1.5 h-6 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.1}s` }}></div>
            ))}
          </div>
        )}
      </div>

      <div className="text-center max-w-md">
        <h2 className="font-cinzel text-3xl text-amber-400 mb-2">
          {isActive ? 'Session Active' : 'Celestial Live Stream'}
        </h2>
        <p className="text-slate-400">
          {isActive ? 'The Guru is listening. Speak clearly about your concerns.' : 'Enter a real-time vocal meditation with the Cosmic AI.'}
        </p>
      </div>

      <div className="w-full max-w-2xl bg-[#0a0a2a]/40 backdrop-blur border border-indigo-900/30 rounded-3xl p-6 min-h-[200px] flex flex-col justify-end">
        {transcription.length > 0 ? (
          <div className="space-y-3">
            {transcription.map((t, i) => (
              <p key={i} className={`text-sm ${t.startsWith('Guru') ? 'text-amber-400' : 'text-slate-400 font-medium'}`}>{t}</p>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 opacity-20 flex flex-col items-center">
            <Radio className="w-12 h-12 mb-2" />
            <p className="font-cinzel tracking-widest">AWAITING CONNECTION</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveView;
