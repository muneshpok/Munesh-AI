
export enum AppView {
  PROFILE = 'profile',
  FORECAST = 'forecast',
  COMPATIBILITY = 'compatibility',
  MUHURTA = 'muhurta',
  DREAMS = 'dreams',
  MANTRAS = 'mantras',
  CHAT = 'chat',
  VIDEO = 'video',
  LIVE = 'live',
  AURA = 'aura',
  MAPS = 'maps'
}

export interface BSDate {
  year: number;
  month: number;
  day: number;
}

export interface BirthDetails {
  bsDate: BSDate;
  time: string;
  place: string;
}

export interface ForecastItem {
  period: string;
  prediction: string;
  intensity: number;
  theme: string;
}

export interface AstroReport {
  moonSign: string;
  nakshatra: string;
  prediction: string;
  remedies: string[];
  gregorianDate?: string;
  yearlyForecast: ForecastItem[];
  monthlyForecast: ForecastItem[];
  dailyForecast: ForecastItem[];
}

export interface CompatibilityResult {
  score: number;
  analysis: string;
  pros: string[];
  cons: string[];
}

export interface MuhurtaOption {
  time: string;
  tithi: string;
  nakshatra: string;
  reason: string;
}
