import { useLocation } from "react-router";
import { usePageMetadata } from "./usePageMetadata";
import { getLocalizedPublicPath, getPublicAlternatePaths, stripPublicLocalePrefix } from "../utils/publicRoutes";

type PublicPageMetadataOptions = {
  title: string;
  description: string;
  basePath: string;
  robots?: string;
};

export function usePublicPageMetadata({
  title,
  description,
  basePath,
  robots,
}: PublicPageMetadataOptions) {
  const location = useLocation();
  const { routeLocale } = stripPublicLocalePrefix(location.pathname);
  const canonicalPath = routeLocale ? getLocalizedPublicPath(basePath, routeLocale) : basePath;

  usePageMetadata({
    title,
    description,
    canonicalPath,
    alternates: getPublicAlternatePaths(basePath),
    robots,
  });
}

