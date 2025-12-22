
import { GoogleGenAI, Type, Modality } from "@google/genai";

const API_KEY = process.env.API_KEY || '';
export const getAI = () => new GoogleGenAI({ apiKey: API_KEY });

export async function getDailyAffirmation(moonSign?: string) {
  const ai = getAI();
  const prompt = moonSign 
    ? `Generate a single, powerful spiritual affirmation or daily quote for someone with ${moonSign} Moon Sign. Focus on spiritual growth, inner peace, and the current celestial shift. Keep it under 25 words.`
    : `Generate a single, powerful spiritual affirmation or daily quote based on Vedic wisdom and general celestial transits. Focus on purpose and clarity. Keep it under 25 words.`;
  
  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: prompt,
  });
  return response.text;
}

export async function calculateAstroProfile(details: any) {
  const ai = getAI();
  const prompt = `You are a specialized Vedic Astrologer expert in the Nepali Bikram Sambat (BS) calendar. 
  Input Birth Details (Bikram Sambat): Year ${details.bsDate.year}, Month ${details.bsDate.month}, Day ${details.bsDate.day}, Time: ${details.time}, Place: ${details.place}.
  Calculate Moon Sign, Nakshatra, and 5-year forecast. Output JSON.`;
  
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: prompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          gregorianDate: { type: Type.STRING },
          moonSign: { type: Type.STRING },
          nakshatra: { type: Type.STRING },
          prediction: { type: Type.STRING },
          remedies: { type: Type.ARRAY, items: { type: Type.STRING } },
          yearlyForecast: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { period: { type: Type.STRING }, prediction: { type: Type.STRING }, intensity: { type: Type.NUMBER }, theme: { type: Type.STRING } }, required: ["period", "prediction", "intensity", "theme"] } },
          monthlyForecast: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { period: { type: Type.STRING }, prediction: { type: Type.STRING }, intensity: { type: Type.NUMBER }, theme: { type: Type.STRING } }, required: ["period", "prediction", "intensity", "theme"] } },
          dailyForecast: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { period: { type: Type.STRING }, prediction: { type: Type.STRING }, intensity: { type: Type.NUMBER }, theme: { type: Type.STRING } }, required: ["period", "prediction", "intensity", "theme"] } }
        },
        required: ["gregorianDate", "moonSign", "nakshatra", "prediction", "remedies", "yearlyForecast", "monthlyForecast", "dailyForecast"]
      }
    }
  });
  return JSON.parse(response.text);
}

export async function checkCompatibility(person1: any, person2: any) {
  const ai = getAI();
  const prompt = `Gun Milan analysis for Person 1 (${person1.year}-${person1.month}-${person1.day}) and Person 2 (${person2.year}-${person2.month}-${person2.day}). Output JSON score/36, analysis, pros, cons.`;
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: prompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          score: { type: Type.NUMBER },
          analysis: { type: Type.STRING },
          pros: { type: Type.ARRAY, items: { type: Type.STRING } },
          cons: { type: Type.ARRAY, items: { type: Type.STRING } }
        },
        required: ["score", "analysis", "pros", "cons"]
      }
    }
  });
  return JSON.parse(response.text);
}

export async function findMuhurta(purpose: string, dateRange: string) {
  const ai = getAI();
  const prompt = `Find 3 auspicious Muhurtas for ${purpose} in BS range ${dateRange}. Output JSON.`;
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: prompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          options: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                time: { type: Type.STRING },
                tithi: { type: Type.STRING },
                nakshatra: { type: Type.STRING },
                reason: { type: Type.STRING }
              },
              required: ["time", "tithi", "nakshatra", "reason"]
            }
          }
        }
      }
    }
  });
  return JSON.parse(response.text);
}

export async function interpretDream(description: string, rashi: string) {
  const ai = getAI();
  const prompt = `Interpret this dream: "${description}" for a person with ${rashi} Moon Sign. Relate it to spiritual growth. Output JSON { interpretation: string, color: string }.`;
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: prompt,
    config: { responseMimeType: "application/json" }
  });
  return JSON.parse(response.text);
}

export async function generateMantraAudio(rashi: string) {
  const ai = getAI();
  const prompt = `Generate the specific Vedic Beej Mantra for ${rashi} Moon Sign. Format: "Om [Seed Sound] Namah". Then speak it 3 times slowly and rhythmically.`;
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-preview-tts",
    contents: [{ parts: [{ text: prompt }] }],
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Charon' } } }
    }
  });
  return response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
}

export async function chatWithGuru(message: string, history: any[]) {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: message,
    config: { systemInstruction: "You are an expert Vedic Astrologer." }
  });
  return response.text;
}

export async function generateAstroVideo(prompt: string, aspectRatio: '16:9' | '9:16') {
  const ai = getAI();
  let operation = await ai.models.generateVideos({
    model: 'veo-3.1-fast-generate-preview',
    prompt,
    config: { resolution: '720p', aspectRatio }
  });
  while (!operation.done) {
    await new Promise(resolve => setTimeout(resolve, 10000));
    operation = await ai.operations.getVideosOperation({ operation });
  }
  const downloadLink = operation.response?.generatedVideos?.[0]?.video?.uri;
  const response = await fetch(`${downloadLink}&key=${API_KEY}`);
  return URL.createObjectURL(await response.blob());
}

export async function analyzeAura(base64Image: string, prompt: string) {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: { parts: [{ inlineData: { data: base64Image, mimeType: 'image/jpeg' } }, { text: prompt }] }
  });
  return response.text;
}

export async function editAura(base64Image: string, editPrompt: string) {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: { parts: [{ inlineData: { data: base64Image, mimeType: 'image/jpeg' } }, { text: editPrompt }] }
  });
  for (const part of response.candidates[0].content.parts) {
    if (part.inlineData) return `data:image/png;base64,${part.inlineData.data}`;
  }
  return null;
}

export async function findSpiritualPlaces(query: string) {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: query,
    config: { tools: [{ googleMaps: {} }] }
  });
  return { text: response.text, chunks: response.candidates?.[0]?.groundingMetadata?.groundingChunks || [] };
}

export async function speakText(text: string) {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-preview-tts",
    contents: [{ parts: [{ text }] }],
    config: { responseModalities: [Modality.AUDIO], speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } } } }
  });
  return response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
}

export function decodeBase64(base64: string) {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
  return bytes;
}

export async function decodeAudioData(data: Uint8Array, ctx: AudioContext, sampleRate: number, numChannels: number) {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);
  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
  }
  return buffer;
}
