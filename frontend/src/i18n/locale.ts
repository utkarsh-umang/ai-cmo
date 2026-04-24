export type Locale = "en";

export const SUPPORTED_LOCALES: Locale[] = ["en"];

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN",
};

export function isLocale(value: string | null | undefined): value is Locale {
  return value === "en";
}

export function normalizeLocale(_value: string | null | undefined): Locale {
  return "en";
}

export function getDocumentLanguage(_locale: Locale): string {
  return "en";
}

export function resolveLocaleText<T extends string>(
  _locale: Locale,
  values: Partial<Record<Locale, T>> & { en: T },
): T {
  return values.en;
}
