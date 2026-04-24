export type Locale = "en";

export const SUPPORTED_LOCALES: Locale[] = ["en"];

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN",
};

const BROWSER_LOCALE_MAP: Array<[prefix: string, locale: Locale]> = [
  ["en", "en"],
];

export function isLocale(value: string | null | undefined): value is Locale {
  return value != null && SUPPORTED_LOCALES.includes(value as Locale);
}

export function normalizeLocale(value: string | null | undefined): Locale {
  return "en";
}

export function getDocumentLanguage(locale: Locale): string {
  return "en";
}

export function resolveLocaleText<T extends string>(
  locale: Locale,
  values: Partial<Record<Locale, T>> & { en: T },
): T {
  return values.en;
}
