import { useEffect, type ReactNode } from "react";
import { useI18n } from "../../i18n";
import type { SeoLocale } from "../../utils/publicRoutes";

export function PublicLocaleSync({
  locale,
  children,
}: {
  locale: SeoLocale;
  children: ReactNode;
}) {
  const { setLocale } = useI18n();

  useEffect(() => {
    setLocale(locale);
  }, [locale, setLocale]);

  return <>{children}</>;
}

