'use client';

import { NextIntlClientProvider } from 'next-intl';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Locale, defaultLocale, locales } from './config';

// Import messages
import enMessages from '@/messages/en.json';
import koMessages from '@/messages/ko.json';

const messages: Record<Locale, typeof enMessages> = {
  en: enMessages,
  ko: koMessages,
};

interface LocaleContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined);

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within I18nProvider');
  }
  return context;
}

interface I18nProviderProps {
  children: ReactNode;
}

export function I18nProvider({ children }: I18nProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Get locale from localStorage on client
    const savedLocale = localStorage.getItem('locale') as Locale | null;
    if (savedLocale && locales.includes(savedLocale)) {
      setLocaleState(savedLocale);
    } else {
      // Try to detect browser language
      const browserLang = navigator.language.split('-')[0];
      if (browserLang === 'ko') {
        setLocaleState('ko');
        localStorage.setItem('locale', 'ko');
      }
    }
    setIsHydrated(true);
  }, []);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem('locale', newLocale);
  };

  // Prevent hydration mismatch by showing default locale on server
  const currentLocale = isHydrated ? locale : defaultLocale;

  return (
    <LocaleContext.Provider value={{ locale: currentLocale, setLocale }}>
      <NextIntlClientProvider
        locale={currentLocale}
        messages={messages[currentLocale]}
        timeZone="Asia/Seoul"
      >
        {children}
      </NextIntlClientProvider>
    </LocaleContext.Provider>
  );
}
