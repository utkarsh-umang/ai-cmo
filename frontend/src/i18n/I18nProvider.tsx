import { createContext, useState, useCallback, useEffect, type ReactNode } from "react";
import { en, type TranslationKey } from "./locales/en";
import {
  getDocumentLanguage,
  normalizeLocale,
  type Locale,
} from "./locale";

const dictionaries: Record<Locale, Partial<Record<TranslationKey, string>>> = { en };

function getInitialLocale(): Locale {
  return "en";
}

export interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState("en");
  }, []);

  useEffect(() => {
    document.documentElement.lang = "en";
    document.documentElement.dataset.locale = "en";
  }, []);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) => {
      let text = en[key] || key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          text = text.replaceAll(`{{${k}}}`, String(v));
        }
      }
      return text;
    },
    [],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export type { Locale };
