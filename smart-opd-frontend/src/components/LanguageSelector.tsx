'use client'
import { useState, useEffect } from 'react'
import { SUPPORTED_LANGUAGES, getStoredLanguage, setStoredLanguage } from '@/lib/i18n'
import { Language } from '@/types'
import { Globe, Check } from 'lucide-react'

interface LanguageSelectorProps {
  onLanguageChange?: (lang: Language) => void
  className?: string
}

export default function LanguageSelector({ onLanguageChange, className = '' }: LanguageSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selected, setSelected] = useState<Language>(getStoredLanguage())

  useEffect(() => {
    const stored = getStoredLanguage()
    setSelected(stored)
    onLanguageChange?.(stored)
  }, [onLanguageChange])

  const handleSelect = (lang: Language) => {
    setSelected(lang)
    setStoredLanguage(lang)
    setIsOpen(false)
    onLanguageChange?.(lang)
  }

  const currentLang = SUPPORTED_LANGUAGES.find(l => l.code === selected)

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition-colors text-sm font-medium text-slate-700"
      >
        <Globe className="w-4 h-4 text-slate-500" />
        <span>{currentLang?.native}</span>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl border border-slate-200 shadow-lg z-20 overflow-hidden">
            {SUPPORTED_LANGUAGES.map(lang => (
              <button
                key={lang.code}
                onClick={() => handleSelect(lang.code)}
                className={`w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors ${
                  selected === lang.code ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
                }`}
              >
                <span>{lang.native}</span>
                {selected === lang.code && <Check className="w-4 h-4" />}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}