import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import fr from '../locales/fr.json'
import en from '../locales/en.json'
import it from '../locales/it.json'
import es from '../locales/es.json'

const saved = localStorage.getItem('lang') || 'fr'

i18n.use(initReactI18next).init({
  resources: { 
    fr: { translation: fr }, 
    en: { translation: en }, 
    it: { translation: it },
    es: { translation: es }
  },
  lng: saved,
  fallbackLng: 'fr',
  interpolation: { escapeValue: false },
})

i18n.on('languageChanged', (lng) => localStorage.setItem('lang', lng))

export default i18n
