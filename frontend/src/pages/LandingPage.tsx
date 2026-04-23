import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  FileText,
  GitBranch,
  Globe,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import { SiteFooter } from "../components/layout/SiteFooter";
import {
  BLOG_ARTICLES,
  BLOG_DECISION_ARTICLE_SLUGS,
  BLOG_FEATURED_ARTICLE_SLUG,
  LANDING_CRAWLER_BULLETS,
  LANDING_FAQS,
  LANDING_MENTION_ITEMS,
  LANDING_PLATFORM_ITEMS,
  LANDING_PROOF_ITEMS,
  LANDING_TRUST_ITEMS,
  LANDING_WORKFLOW_STEPS,
  PUBLIC_HOME_NAV,
  getLocalizedBlogArticlePath,
  getSampleAuditPath,
} from "../content/marketing";
import { useSiteStats } from "../hooks/useSiteStats";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { useI18n } from "../i18n";
import type { TranslationKey } from "../i18n";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

const PROOF_ICONS = [Search, Bot, Users];
const CAPABILITY_ICONS = [Search, Globe, Users, GitBranch, FileText];
const OPEN_SOURCE_ICONS = [GitBranch, ShieldCheck, Globe, FileText];
const TRUST_ICONS = [ShieldCheck, Bot, GitBranch, CheckCircle2];
const GITHUB_REPO_URL = "https://github.com/study8677/OpenCMO";
const LICENSE_URL = "https://github.com/study8677/OpenCMO/blob/main/LICENSE";
const QUICK_START_URL = "https://github.com/study8677/OpenCMO#quick-start";

export function LandingPage() {
  const { t, locale } = useI18n();
  const { data: siteStats } = useSiteStats();
  const numberFormatter = new Intl.NumberFormat(locale);
  const mentionDateFormatter = new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const seoLocale = getSeoLocaleFromLocale(locale);
  const comparisonArticlePath = getLocalizedBlogArticlePath("opencmo-vs-mautic-posthog", seoLocale);
  const architectureArticlePath = getLocalizedBlogArticlePath("inside-opencmo-workspace", seoLocale);
  const featuredBlogArticle =
    BLOG_ARTICLES.find((article) => article.slug === BLOG_FEATURED_ARTICLE_SLUG)
    ?? BLOG_ARTICLES.find((article) => article.slug === BLOG_DECISION_ARTICLE_SLUGS[0])
    ?? BLOG_ARTICLES[0]!;
  const heroBadgeKeys = [
    "landing.heroBadgeOpenSource",
    "landing.heroBadgeLicense",
    "landing.heroBadgeSelfHost",
    "landing.heroBadgeByok",
  ] as TranslationKey[];
  const openSourceCards = [
    {
      title: "landing.openSourceCardRepoTitle",
      description: "landing.openSourceCardRepoDesc",
      cta: "landing.openSourceCardRepoCta",
      href: GITHUB_REPO_URL,
      external: true,
    },
    {
      title: "landing.openSourceCardLicenseTitle",
      description: "landing.openSourceCardLicenseDesc",
      cta: "landing.openSourceCardLicenseCta",
      href: LICENSE_URL,
      external: true,
    },
    {
      title: "landing.openSourceCardQuickstartTitle",
      description: "landing.openSourceCardQuickstartDesc",
      cta: "landing.openSourceCardQuickstartCta",
      href: QUICK_START_URL,
      external: true,
    },
    {
      title: "landing.openSourceCardArchitectureTitle",
      description: "landing.openSourceCardArchitectureDesc",
      cta: "landing.openSourceCardArchitectureCta",
      href: architectureArticlePath,
      external: false,
    },
  ] as const;

  usePublicPageMetadata({
    title: t("landing.metaTitle"),
    description: t("landing.metaDescription"),
    basePath: "/",
  });

  return (
    <div className="min-h-screen bg-[#f6efe5] text-slate-950">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="dark" />

      <main className="pb-16">
        <section className="relative overflow-hidden bg-[#08141f] text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_16%,rgba(201,111,69,0.3),transparent_24%),radial-gradient(circle_at_82%_18%,rgba(134,200,188,0.22),transparent_24%),linear-gradient(135deg,#08141f_0%,#0c2538_44%,#08141f_100%)]" />
          <div className="absolute -left-12 top-24 h-64 w-64 rounded-full bg-[#c96f45]/20 blur-3xl animate-float-slow" />
          <div className="absolute bottom-6 right-[10%] h-72 w-72 rounded-full bg-[#86c8bc]/16 blur-3xl animate-float-slower" />

          <div className="relative mx-auto grid min-h-[calc(100svh-80px)] max-w-7xl gap-10 px-4 py-14 lg:grid-cols-[minmax(0,1.02fr)_minmax(380px,0.98fr)] lg:px-8 lg:py-20">
            <motion.div
              initial={{ opacity: 0, y: 32 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col justify-start pt-6 lg:pt-14"
            >
              <p className="inline-flex w-fit rounded-full border border-white/14 bg-white/8 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-[#f3dcc9]">
                {t("landing.heroEyebrow")}
              </p>
              <h1 className="font-display mt-6 max-w-4xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-[3.25rem] lg:leading-[1.04] xl:text-[3.75rem] xl:leading-[1.01]">
                {t("landing.heroTitle")}
              </h1>
              <p className="mt-6 max-w-3xl text-lg leading-8 text-white/72 sm:text-xl">
                {t("landing.heroSubtitle")}
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  to="/workspace"
                  className="inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-5 py-3 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
                >
                  {t("landing.primaryCta")}
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to={getSampleAuditPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-full border border-white/14 bg-white/8 px-5 py-3 text-sm font-semibold text-white transition-colors hover:border-white/28 hover:bg-white/12"
                >
                  {t("landing.sampleCta")}
                </Link>
                <a
                  href={GITHUB_REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-full border border-white/14 bg-white/8 px-5 py-3 text-sm font-semibold text-white transition-colors hover:border-white/28 hover:bg-white/12"
                >
                  {t("landing.githubCta")}
                  <ArrowUpRight size={16} />
                </a>
              </div>

              <div className="mt-6 flex flex-wrap gap-2">
                {heroBadgeKeys.map((key) => (
                  <span
                    key={key}
                    className="inline-flex items-center rounded-full border border-white/12 bg-white/8 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-white/78"
                  >
                    {t(key)}
                  </span>
                ))}
              </div>

              <div className="mt-10">
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#f3dcc9]">
                  {t("landing.proofTitle")}
                </p>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  {LANDING_PROOF_ITEMS.map((item, index) => {
                    const Icon = PROOF_ICONS[index] ?? Sparkles;
                    return (
                      <div
                        key={item.title}
                        className="rounded-2xl border border-white/12 bg-white/8 px-4 py-4"
                      >
                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10 text-[#f3dcc9]">
                          <Icon size={16} />
                        </div>
                        <p className="mt-3 text-sm font-semibold leading-6 text-white">
                          {t(item.title)}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.85, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
              className="relative flex items-start pt-2 lg:pt-6"
            >
              <div className="relative w-full overflow-hidden rounded-[2rem] border border-white/12 bg-[linear-gradient(160deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03))] p-6 shadow-[0_28px_100px_rgba(0,0,0,0.3)]">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(201,111,69,0.18),transparent_32%),linear-gradient(180deg,rgba(255,255,255,0.04),transparent_64%)]" />
                <div className="relative">
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#f3dcc9]">
                    {t("landing.previewLabel")}
                  </p>
                  <h2 className="mt-3 text-2xl font-semibold tracking-tight text-white">
                    {t("landing.previewTitle")}
                  </h2>
                  <p className="mt-3 text-sm leading-7 text-white/68">
                    {t("landing.previewSubtitle")}
                  </p>

                  <div className="mt-5 space-y-3">
                    {LANDING_PROOF_ITEMS.map((item, index) => {
                      const Icon = PROOF_ICONS[index] ?? Sparkles;
                      return (
                        <div
                          key={item.title}
                          className="rounded-2xl border border-white/10 bg-[#08141f]/60 p-4"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10 text-[#f3dcc9]">
                              <Icon size={16} />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-white">{t(item.title)}</p>
                              <p className="mt-1 text-sm leading-6 text-white/68">{t(item.description)}</p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-5 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-200">
                      {t("landing.previewActionLabel")}
                    </p>
                    <p className="mt-2 text-sm font-semibold text-white">{t("landing.previewAction")}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <section id="open-source" className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("landing.openSourceEyebrow")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("landing.openSourceTitle")}
              </h2>
              <p className="mt-4 text-base leading-8 text-slate-700">
                {t("landing.openSourceSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-10 grid gap-5 lg:grid-cols-[minmax(0,1.08fr)_minmax(320px,0.92fr)]">
            <div className="grid gap-5 md:grid-cols-2">
              {openSourceCards.map((item, index) => {
                const Icon = OPEN_SOURCE_ICONS[index] ?? Sparkles;
                const cardBody = (
                  <>
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                      <Icon size={18} />
                    </div>
                    <h3 className="font-display mt-5 text-2xl font-semibold tracking-tight text-slate-950">
                      {t(item.title)}
                    </h3>
                    <p className="mt-3 text-base leading-8 text-slate-700">
                      {t(item.description)}
                    </p>
                    <span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-colors group-hover:text-[#c96f45]">
                      {t(item.cta)}
                      <ArrowUpRight size={15} />
                    </span>
                  </>
                );

                return (
                  <SectionReveal key={item.title} delay={index * 0.05}>
                    {item.external ? (
                      <a
                        href={item.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)] transition-transform duration-300 hover:-translate-y-1"
                      >
                        {cardBody}
                      </a>
                    ) : (
                      <Link
                        to={item.href}
                        className="group rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)] transition-transform duration-300 hover:-translate-y-1"
                      >
                        {cardBody}
                      </Link>
                    )}
                  </SectionReveal>
                );
              })}
            </div>

            <SectionReveal delay={0.14}>
              <div className="rounded-[2rem] border border-black/8 bg-[#082032] p-6 text-white shadow-[0_18px_60px_rgba(8,32,50,0.12)]">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#f3dcc9]">
                  {t("landing.compareEyebrow")}
                </p>
                <h3 className="mt-3 text-2xl font-semibold tracking-tight">
                  {t("landing.compareTitle")}
                </h3>
                <p className="mt-4 text-sm leading-7 text-white/72">
                  {t("landing.compareBody")}
                </p>
                <div className="mt-5 space-y-3">
                  {([
                    "landing.comparePoint1",
                    "landing.comparePoint2",
                    "landing.comparePoint3",
                    "landing.comparePoint4",
                  ] as TranslationKey[]).map((key) => (
                    <div
                      key={key}
                      className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm leading-6 text-white/82"
                    >
                      <CheckCircle2 size={16} className="mt-1 shrink-0 text-emerald-300" />
                      <span>{t(key)}</span>
                    </div>
                  ))}
                </div>
                <Link
                  to={comparisonArticlePath}
                  className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-white transition-colors hover:text-[#f3dcc9]"
                >
                  {t("landing.compareCta")}
                  <ArrowUpRight size={15} />
                </Link>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section id="sample-audit" className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("landing.proofTitle")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("landing.proofSubtitle")}
              </h2>
            </div>
          </SectionReveal>

          <div className="mt-10 grid gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
            <div className="grid gap-5 md:grid-cols-3">
              {LANDING_PROOF_ITEMS.map((item, index) => {
                const Icon = PROOF_ICONS[index] ?? Sparkles;
                return (
                  <SectionReveal key={item.title} delay={index * 0.06}>
                    <article className="rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#082032] text-white">
                        <Icon size={18} />
                      </div>
                      <h3 className="font-display mt-5 text-2xl font-semibold tracking-tight text-slate-950">
                        {t(item.title)}
                      </h3>
                      <p className="mt-3 text-base leading-8 text-slate-700">
                        {t(item.description)}
                      </p>
                    </article>
                  </SectionReveal>
                );
              })}
            </div>

            <SectionReveal delay={0.12}>
              <div className="rounded-[2rem] border border-black/8 bg-[#082032] p-6 text-white shadow-[0_18px_60px_rgba(8,32,50,0.12)]">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#f3dcc9]">
                  {t("landing.workflowEyebrow")}
                </p>
                <h3 className="mt-3 text-2xl font-semibold tracking-tight">
                  {t("landing.previewTitle")}
                </h3>
                <div className="mt-5 space-y-3">
                  {(["landing.stage1", "landing.stage2", "landing.stage3", "landing.stage4", "landing.stage5", "landing.stage6"] as TranslationKey[]).map((key) => (
                    <div
                      key={key}
                      className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm text-white/80"
                    >
                      <CheckCircle2 size={16} className="text-emerald-300" />
                      <span>{t(key)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section id="workflow" className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="overflow-hidden rounded-[2.4rem] border border-black/8 bg-[#efe5d6] shadow-[0_22px_70px_rgba(8,32,50,0.08)]">
              <div className="grid gap-8 px-6 py-8 lg:grid-cols-[minmax(0,0.88fr)_minmax(0,1.12fr)] lg:px-8 lg:py-10">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                    {t("landing.workflowEyebrow")}
                  </p>
                  <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                    {t("landing.workflowTitle")}
                  </h2>
                  <p className="mt-4 max-w-xl text-base leading-8 text-slate-700">
                    {t("landing.workflowSubtitle")}
                  </p>
                </div>

                <div className="space-y-3">
                  {LANDING_WORKFLOW_STEPS.map((step, index) => (
                    <motion.article
                      key={step.title}
                      initial={{ opacity: 0, x: 24 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true, amount: 0.3 }}
                      transition={{ duration: 0.55, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }}
                      className="grid gap-4 rounded-[1.6rem] border border-black/8 bg-white/75 px-5 py-5 sm:grid-cols-[64px_minmax(0,1fr)]"
                    >
                      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#082032] text-sm font-semibold text-white">
                        0{index + 1}
                      </div>
                      <div>
                        <h3 className="font-display text-2xl font-semibold tracking-tight text-slate-950">
                          {t(step.title)}
                        </h3>
                        <p className="mt-2 text-base leading-7 text-slate-700">
                          {t(step.description)}
                        </p>
                      </div>
                    </motion.article>
                  ))}
                </div>
              </div>
            </div>
          </SectionReveal>
        </section>

        <section id="platform" className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("landing.platformEyebrow")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("landing.platformTitle")}
              </h2>
              <p className="mt-4 text-base leading-8 text-slate-700">
                {t("landing.platformSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-5">
            {LANDING_PLATFORM_ITEMS.map((item, index) => {
              const Icon = CAPABILITY_ICONS[index] ?? Sparkles;
              return (
                <SectionReveal key={item.title} delay={index * 0.05}>
                  <article className="h-full rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                      <Icon size={18} />
                    </div>
                    <h3 className="font-display mt-5 text-2xl font-semibold tracking-tight text-slate-950">
                      {t(item.title)}
                    </h3>
                    <p className="mt-3 text-base leading-8 text-slate-700">
                      {t(item.description)}
                    </p>
                  </article>
                </SectionReveal>
              );
            })}
          </div>
        </section>

        <section id="trust" className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("landing.trustEyebrow")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("landing.trustTitle")}
              </h2>
              <p className="mt-4 text-base leading-8 text-slate-700">
                {t("landing.trustSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-10 grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
            <div className="grid gap-5 md:grid-cols-2">
              {LANDING_TRUST_ITEMS.map((item, index) => {
                const Icon = TRUST_ICONS[index] ?? ShieldCheck;
                return (
                  <SectionReveal key={item.title} delay={index * 0.05}>
                    <article className="rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                        <Icon size={18} />
                      </div>
                      <h3 className="mt-5 text-lg font-semibold text-slate-950">{t(item.title)}</h3>
                      <p className="mt-3 text-base leading-8 text-slate-700">{t(item.description)}</p>
                    </article>
                  </SectionReveal>
                );
              })}
            </div>

            <SectionReveal delay={0.16}>
              <div className="rounded-[2rem] border border-black/8 bg-[#082032] p-6 text-white shadow-[0_18px_60px_rgba(8,32,50,0.12)]">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#f3dcc9]">
                  {t("landing.trustPanelTitle")}
                </p>
                <p className="mt-4 text-sm leading-7 text-white/72">
                  {t("landing.trustPanelBody")}
                </p>
                <div className="mt-5 space-y-3">
                  {([
                    "landing.trustPanel1",
                    "landing.trustPanel2",
                    "landing.trustPanel3",
                    "landing.trustPanel4",
                    "landing.trustPanel5",
                  ] as TranslationKey[]).map((key) => (
                    <div
                      key={key}
                      className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm leading-6 text-white/82"
                    >
                      <CheckCircle2 size={16} className="mt-1 shrink-0 text-emerald-300" />
                      <span>{t(key)}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-5 rounded-2xl border border-white/10 bg-white/6 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/50">
                    {t("siteFooter.liveStats")}
                  </p>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
                        {t("siteFooter.totalVisits")}
                      </p>
                      <p className="mt-2 text-2xl font-semibold">
                        {numberFormatter.format(siteStats?.total_visits ?? 0)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
                        {t("siteFooter.uniqueVisitors")}
                      </p>
                      <p className="mt-2 text-2xl font-semibold">
                        {numberFormatter.format(siteStats?.unique_visitors ?? 0)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section id="mentions" className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("landing.mentionsEyebrow")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("landing.mentionsTitle")}
              </h2>
              <p className="mt-4 text-base leading-8 text-slate-700">
                {t("landing.mentionsSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-10 grid gap-5 lg:grid-cols-[minmax(0,1.08fr)_minmax(320px,0.92fr)]">
            <div className="grid gap-5">
              {LANDING_MENTION_ITEMS.map((item, index) => (
                <SectionReveal key={item.href} delay={index * 0.06}>
                  <article className="rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
                    <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      <span>{t(item.source)}</span>
                      <span>{mentionDateFormatter.format(new Date(item.publishedAt))}</span>
                    </div>
                    <h3 className="font-display mt-4 text-2xl font-semibold tracking-tight text-slate-950">
                      {t(item.title)}
                    </h3>
                    <p className="mt-3 text-base leading-8 text-slate-700">
                      {t(item.description)}
                    </p>
                    <a
                      href={item.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-colors hover:text-[#c96f45]"
                    >
                      {t("landing.mentionReadCta")}
                      <ArrowUpRight size={15} />
                    </a>
                  </article>
                </SectionReveal>
              ))}
            </div>

            <SectionReveal delay={0.14}>
              <div className="rounded-[2rem] border border-black/8 bg-[#082032] p-6 text-white shadow-[0_18px_60px_rgba(8,32,50,0.12)]">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#f3dcc9]">
                  {t("landing.mentionsPanelEyebrow")}
                </p>
                <h3 className="mt-3 text-2xl font-semibold tracking-tight">
                  {t("landing.mentionsPanelTitle")}
                </h3>
                <p className="mt-4 text-sm leading-7 text-white/72">
                  {t("landing.mentionsPanelBody")}
                </p>
                <div className="mt-5 space-y-3">
                  {([
                    "landing.mentionsPoint1",
                    "landing.mentionsPoint2",
                    "landing.mentionsPoint3",
                  ] as TranslationKey[]).map((key) => (
                    <div
                      key={key}
                      className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm leading-6 text-white/82"
                    >
                      <CheckCircle2 size={16} className="mt-1 shrink-0 text-emerald-300" />
                      <span>{t(key)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section id="faq" className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("landing.navFaq")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("landing.faqTitle")}
              </h2>
            </div>
          </SectionReveal>

          <div className="mt-8 divide-y divide-black/8 rounded-[2rem] border border-black/8 bg-white/75 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
            {LANDING_FAQS.map((item, index) => (
              <SectionReveal key={item.question} delay={index * 0.05}>
                <article className="grid gap-4 px-6 py-6 md:grid-cols-[minmax(0,300px)_minmax(0,1fr)] md:px-8">
                  <h3 className="font-display text-2xl font-semibold tracking-tight text-slate-950">
                    {t(item.question)}
                  </h3>
                  <p className="max-w-3xl text-base leading-8 text-slate-700">
                    {t(item.answer)}
                  </p>
                </article>
              </SectionReveal>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.9fr)]">
            <SectionReveal>
              <div className="rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">
                  {t("landing.crawlerTitle")}
                </p>
                <p className="mt-4 text-base leading-8 text-slate-700">
                  {t("landing.crawlerBody")}
                </p>
                <div className="mt-5 space-y-3">
                  {LANDING_CRAWLER_BULLETS.map((key) => (
                    <div
                      key={key}
                      className="flex items-start gap-3 rounded-2xl border border-black/8 bg-[#f8fafc] px-4 py-3 text-sm leading-6 text-slate-700"
                    >
                      <CheckCircle2 size={16} className="mt-1 shrink-0 text-emerald-600" />
                      <p>{t(key)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </SectionReveal>

            <SectionReveal delay={0.1}>
              <Link
                to={getLocalizedBlogArticlePath(featuredBlogArticle.slug, seoLocale)}
                className={`group block overflow-hidden rounded-[2rem] border border-black/8 bg-gradient-to-br p-6 shadow-[0_18px_60px_rgba(8,32,50,0.06)] transition-transform duration-300 hover:-translate-y-1 ${featuredBlogArticle.accentClass}`}
              >
                <div className="rounded-[1.4rem] bg-white/78 p-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.26em] text-slate-500">
                    {t("landing.blogPreviewEyebrow")}
                  </p>
                  <h3 className="font-display mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {t(featuredBlogArticle.title)}
                  </h3>
                  <p className="mt-3 text-sm leading-7 text-slate-700">
                    {t(featuredBlogArticle.summary)}
                  </p>
                  <div className="mt-5 flex items-center justify-between text-sm font-semibold text-slate-700">
                    <span>{t("landing.blogPreviewCta")}</span>
                    <span className="inline-flex items-center gap-2 text-slate-900">
                      {t("blog.readArticleCta")}
                      <ArrowUpRight size={15} className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                    </span>
                  </div>
                </div>
              </Link>
            </SectionReveal>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SectionReveal>
            <div className="overflow-hidden rounded-[2.4rem] border border-black/8 bg-[#082032] px-6 py-8 text-white shadow-[0_24px_90px_rgba(8,32,50,0.18)] sm:px-8 sm:py-10">
              <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
                <div className="max-w-3xl">
                  <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#f3dcc9]">
                    {t("landing.finalEyebrow")}
                  </p>
                  <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                    {t("landing.finalTitle")}
                  </h2>
                  <p className="mt-4 text-base leading-8 text-white/72">
                    {t("landing.finalSubtitle")}
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Link
                    to="/workspace"
                    className="inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-5 py-3 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
                  >
                    {t("landing.primaryCta")}
                    <ArrowRight size={16} />
                  </Link>
                  <Link
                    to={getSampleAuditPath(seoLocale)}
                    className="inline-flex items-center gap-2 rounded-full border border-white/14 bg-white/8 px-5 py-3 text-sm font-semibold text-white transition-colors hover:border-white/28 hover:bg-white/12"
                  >
                    {t("landing.sampleCta")}
                  </Link>
                </div>
              </div>
            </div>
          </SectionReveal>
        </section>

        <div className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SiteFooter />
        </div>
      </main>
    </div>
  );
}
