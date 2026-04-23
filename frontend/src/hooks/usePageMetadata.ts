import { useEffect } from "react";

type PageMetadataOptions = {
  title: string;
  description: string;
  canonicalPath: string;
  alternates?: Array<{
    hrefLang: string;
    path: string;
  }>;
  robots?: string;
};

function ensureMeta(selector: string, attribute: "name" | "property", value: string) {
  const existing = document.querySelector<HTMLMetaElement>(selector);
  if (existing) {
    return existing;
  }
  const node = document.createElement("meta");
  node.setAttribute(attribute, value);
  document.head.appendChild(node);
  return node;
}

function ensureCanonical() {
  const existing = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (existing) {
    return existing;
  }
  const node = document.createElement("link");
  node.setAttribute("rel", "canonical");
  document.head.appendChild(node);
  return node;
}

function syncAlternateLinks(alternates: Array<{ hrefLang: string; path: string }>) {
  const managedSelector = 'link[rel="alternate"][data-opencmo-managed="true"]';
  document.querySelectorAll<HTMLLinkElement>(managedSelector).forEach((node) => node.remove());

  const canonicalLink = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  let currentAnchor: Element | null = canonicalLink ?? document.head.querySelector("meta:last-of-type");

  alternates.forEach((alternate) => {
    const node = document.createElement("link");
    node.setAttribute("rel", "alternate");
    node.setAttribute("hreflang", alternate.hrefLang);
    node.setAttribute("href", new URL(alternate.path, window.location.origin).toString());
    node.setAttribute("data-opencmo-managed", "true");
    currentAnchor?.insertAdjacentElement("afterend", node);
    currentAnchor = node;
  });
}

export function usePageMetadata({
  title,
  description,
  canonicalPath,
  alternates = [],
  robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1",
}: PageMetadataOptions) {
  useEffect(() => {
    const previousTitle = document.title;
    const descriptionMeta = ensureMeta('meta[name="description"]', "name", "description");
    const robotsMeta = ensureMeta('meta[name="robots"]', "name", "robots");
    const ogTitleMeta = ensureMeta('meta[property="og:title"]', "property", "og:title");
    const ogDescriptionMeta = ensureMeta('meta[property="og:description"]', "property", "og:description");
    const ogUrlMeta = ensureMeta('meta[property="og:url"]', "property", "og:url");
    const twitterTitleMeta = ensureMeta('meta[name="twitter:title"]', "name", "twitter:title");
    const twitterDescriptionMeta = ensureMeta('meta[name="twitter:description"]', "name", "twitter:description");
    const canonicalLink = ensureCanonical();

    const previousDescription = descriptionMeta.getAttribute("content");
    const previousRobots = robotsMeta.getAttribute("content");
    const previousOgTitle = ogTitleMeta.getAttribute("content");
    const previousOgDescription = ogDescriptionMeta.getAttribute("content");
    const previousOgUrl = ogUrlMeta.getAttribute("content");
    const previousTwitterTitle = twitterTitleMeta.getAttribute("content");
    const previousTwitterDescription = twitterDescriptionMeta.getAttribute("content");
    const previousCanonical = canonicalLink.getAttribute("href");

    const canonicalUrl = new URL(canonicalPath, window.location.origin).toString();

    document.title = title;
    descriptionMeta.setAttribute("content", description);
    robotsMeta.setAttribute("content", robots);
    ogTitleMeta.setAttribute("content", title);
    ogDescriptionMeta.setAttribute("content", description);
    ogUrlMeta.setAttribute("content", canonicalUrl);
    twitterTitleMeta.setAttribute("content", title);
    twitterDescriptionMeta.setAttribute("content", description);
    canonicalLink.setAttribute("href", canonicalUrl);
    syncAlternateLinks(alternates);

    return () => {
      document.title = previousTitle;
      if (previousDescription) {
        descriptionMeta.setAttribute("content", previousDescription);
      }
      if (previousRobots) {
        robotsMeta.setAttribute("content", previousRobots);
      }
      if (previousOgTitle) {
        ogTitleMeta.setAttribute("content", previousOgTitle);
      }
      if (previousOgDescription) {
        ogDescriptionMeta.setAttribute("content", previousOgDescription);
      }
      if (previousOgUrl) {
        ogUrlMeta.setAttribute("content", previousOgUrl);
      }
      if (previousTwitterTitle) {
        twitterTitleMeta.setAttribute("content", previousTwitterTitle);
      }
      if (previousTwitterDescription) {
        twitterDescriptionMeta.setAttribute("content", previousTwitterDescription);
      }
      if (previousCanonical) {
        canonicalLink.setAttribute("href", previousCanonical);
      }
      document.querySelectorAll<HTMLLinkElement>('link[rel="alternate"][data-opencmo-managed="true"]').forEach((node) => node.remove());
    };
  }, [alternates, canonicalPath, description, robots, title]);
}
