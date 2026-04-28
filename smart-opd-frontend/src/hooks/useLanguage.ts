'use client'
import { useState, useEffect, useCallback } from 'react'
import { Language, Translation } from '@/types'
import { getStoredLanguage, setStoredLanguage, getTranslations, DEFAULT_LANGUAGE } from '@/lib/i18n'

export function useLanguage() {
  const [language, setLanguage] = useState<Language>(DEFAULT_LANGUAGE)
  const [translations, setTranslations] = useState<Translation | null>(null)
  const [loading, setLoading] = useState(true)

  const loadTranslations = useCallback(async (lang: Language) => {
    setLoading(true)
    try {
      const t = await getTranslations(lang)
      setTranslations(t)
      setLanguage(lang)
      setStoredLanguage(lang)
    } catch (error) {
      console.error('Failed to load translations:', error)
      const fallback = await getTranslations(DEFAULT_LANGUAGE)
      setTranslations(fallback)
      setLanguage(DEFAULT_LANGUAGE)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const stored = getStoredLanguage()
    loadTranslations(stored)
  }, [loadTranslations])

  const t = useCallback((key: string, fallback?: string): string => {
    if (!translations) return fallback || key
    const keys = key.split('.')
    let value: any = translations
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k]
      } else {
        return fallback || key
      }
    }
    return typeof value === 'string' ? value : fallback || key
  }, [translations])

  return {
    language,
    translations,
    loading,
    t,
    setLanguage: loadTranslations,
  }
}