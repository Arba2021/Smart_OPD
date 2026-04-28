import { Language, Translation } from '@/types'

export const SUPPORTED_LANGUAGES: { code: Language; label: string; native: string }[] = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
]

export const DEFAULT_LANGUAGE: Language = 'en'

export const STORAGE_KEY = 'smart-opd-language'

export function getStoredLanguage(): Language {
  if (typeof window === 'undefined') return DEFAULT_LANGUAGE
  const stored = localStorage.getItem(STORAGE_KEY) as Language
  return SUPPORTED_LANGUAGES.some(l => l.code === stored) ? stored : DEFAULT_LANGUAGE
}

export function setStoredLanguage(lang: Language): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEY, lang)
}

export async function getTranslations(lang: Language): Promise<Translation> {
  try {
    const module = await import(`@/translations/${lang}.ts`)
    return module.default
  } catch {
    const module = await import(`@/translations/${DEFAULT_LANGUAGE}.ts`)
    return module.default
  }
}