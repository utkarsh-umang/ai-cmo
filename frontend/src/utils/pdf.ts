const LOGO_URL = "/logo.png";

/**
 * Convert a logo image URL to a base64 data-URI so it can be
 * embedded reliably in the print window.
 */
async function loadLogoAsDataURI(): Promise<string> {
  try {
    const resp = await fetch(LOGO_URL);
    const blob = await resp.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch {
    return "";
  }
}

/**
 * Build a self-contained print stylesheet that produces premium,
 * highly-readable A4 pages via the browser's native print engine.
 */
function buildPrintCSS(): string {
  return `
    @page {
      size: A4;
      margin: 24mm 22mm;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
      font-size: 14.5px;
      line-height: 1.8;
      color: #334155;
      background: #fff;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    /* ---- Header ---- */
    .report-header {
      display: flex;
      align-items: center;
      gap: 16px;
      border-bottom: 3px solid #6366f1;
      padding-bottom: 20px;
      margin-bottom: 35px;
    }
    .report-header img {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      object-fit: contain;
    }
    .report-header-title {
      font-size: 24px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.4px;
      line-height: 1.3;
    }
    .report-header-sub {
      font-size: 12.5px;
      color: #94a3b8;
      margin-top: 4px;
    }

    /* ---- Content (matches .premium-report) ---- */
    .premium-report h1 {
      font-size: 24px;
      font-weight: 800;
      color: #0f172a;
      margin: 36px 0 16px;
      padding-bottom: 12px;
      border-bottom: 3px solid #6366f1;
      letter-spacing: -0.3px;
      line-height: 1.35;
      page-break-after: avoid;
      break-after: avoid;
    }
    .premium-report h1:first-child { margin-top: 0; }

    .premium-report h2 {
      font-size: 19px;
      font-weight: 700;
      color: #1e293b;
      margin: 30px 0 12px;
      padding-bottom: 6px;
      border-bottom: 2px solid #f1f5f9;
      line-height: 1.35;
      page-break-after: avoid;
      break-after: avoid;
      display: flex;
      align-items: center;
    }
    .premium-report h2::before {
      content: "";
      display: inline-block;
      width: 6px;
      height: 22px;
      background: #6366f1;
      border-radius: 4px;
      margin-right: 10px;
    }

    .premium-report h3 {
      font-size: 16px;
      font-weight: 700;
      color: #1e293b;
      margin: 24px 0 10px;
      padding-left: 12px;
      border-left: 4px solid #a5b4fc;
      line-height: 1.4;
      background: #f8fafc;
      padding-top: 6px;
      padding-bottom: 6px;
      padding-right: 10px;
      border-radius: 0 4px 4px 0;
      width: max-content;
      page-break-after: avoid;
      break-after: avoid;
    }

    .premium-report h4 {
      font-size: 14.5px;
      font-weight: 700;
      color: #334155;
      margin: 20px 0 8px;
      page-break-after: avoid;
      break-after: avoid;
    }

    .premium-report p {
      margin: 0 0 18px;
      text-align: justify;
      orphans: 3;
      widows: 3;
    }

    .premium-report ul { list-style: none; margin: 12px 0 20px; padding-left: 20px; }
    .premium-report ol { list-style: decimal; margin: 12px 0 20px; padding-left: 28px; }
    
    .premium-report ul > li { position: relative; margin-bottom: 8px; line-height: 1.7; }
    .premium-report ul > li::before {
      content: "•";
      position: absolute;
      left: -16px;
      color: #6366f1;
      font-weight: 900;
      font-size: 1.2em;
      top: -2px;
    }
    .premium-report ol > li::marker { color: #6366f1; font-weight: 700; }

    .premium-report blockquote {
      margin: 20px 0;
      padding: 12px 20px;
      background: #eff6ff;
      border-left: 5px solid #3b82f6;
      border-top: 1px solid #e0e7ff;
      border-right: 1px solid #e0e7ff;
      border-bottom: 1px solid #e0e7ff;
      border-radius: 0 8px 8px 0;
      color: #334155;
      font-style: italic;
    }
    .premium-report blockquote p { margin-bottom: 8px; }
    .premium-report blockquote p:last-child { margin-bottom: 0; }

    .premium-report strong {
      font-weight: 700;
      color: #0f172a;
      background: #f1f5f9;
      padding: 0 4px;
      border-radius: 2px;
    }

    .premium-report code {
      font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
      font-size: 13px;
      background: #eef2ff;
      padding: 2px 6px;
      border-radius: 4px;
      color: #4f46e5;
      border: 1px solid #e0e7ff;
      white-space: pre-wrap;
      word-break: break-all;
    }

    .premium-report pre {
      background: #0f172a;
      color: #f8fafc;
      padding: 18px;
      border-radius: 10px;
      overflow: auto;
      margin: 16px 0 24px;
      font-size: 13px;
      line-height: 1.6;
      page-break-inside: avoid;
    }
    .premium-report pre code {
      background: none;
      padding: 0;
      border: none;
      color: inherit;
    }

    .premium-report table {
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 13.5px;
      page-break-inside: avoid;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
    }
    .premium-report thead {
      background: #f8fafc;
      border-bottom: 2px solid #cbd5e1;
    }
    .premium-report th {
      font-weight: 700;
      text-align: left;
      padding: 10px 16px;
      color: #334155;
    }
    .premium-report td {
      padding: 9px 16px;
      border-bottom: 1px solid #f1f5f9;
      color: #475569;
    }
    .premium-report tr:last-child td { border-bottom: none; }

    .premium-report hr {
      border: none;
      border-top: 2px solid #f1f5f9;
      margin: 30px auto;
      width: 70%;
      border-radius: 2px;
    }

    .premium-report a {
      color: #4f46e5;
      text-decoration: underline;
      text-decoration-color: #c7d2fe;
      text-decoration-thickness: 2px;
      text-underline-offset: 2px;
    }

    /* ---- Footer ---- */
    .report-footer {
      border-top: 1.5px solid #e2e8f0;
      margin-top: 40px;
      padding-top: 16px;
      display: flex;
      justify-content: space-between;
      font-size: 11.5px;
      color: #64748b;
    }
  `;
}

/**
 * Open a new print-optimised window with the report content and
 * trigger the browser's native Print dialog (Save as PDF).
 *
 * This approach uses the browser's built-in rendering and pagination
 * engine instead of html2canvas, so it handles long documents without
 * freezing or running out of memory.
 */
export async function downloadAsPDF({
  elementId,
  filename: _filename = "report.pdf",
  title = "AI CMO Report",
  subtitle,
}: {
  elementId: string;
  filename?: string;
  title?: string;
  subtitle?: string;
}) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`[pdf] Element #${elementId} not found.`);
    return;
  }

  const logoDataURI = await loadLogoAsDataURI();
  const dateStr = new Date().toLocaleDateString("zh-CN");

  const logoHTML = logoDataURI
    ? `<img src="${logoDataURI}" alt="logo" />`
    : "";

  const subtitleHTML = subtitle
    ? `<div class="report-header-sub">${subtitle}</div>`
    : "";

  const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>${title}</title>
  <style>${buildPrintCSS()}</style>
</head>
<body>
  <div class="report-header">
    ${logoHTML}
    <div>
      <div class="report-header-title">${title}</div>
      ${subtitleHTML}
      <div class="report-header-sub">Generated by OpenCMO · ${dateStr}</div>
    </div>
  </div>

  <div class="premium-report">
    ${element.innerHTML}
  </div>

  <div class="report-footer">
    <span>OpenCMO — AI-Powered Marketing Intelligence</span>
    <span>${new Date().toISOString().slice(0, 10)}</span>
  </div>
</body>
</html>`;

  // Open a new window, write the styled HTML, and trigger print
  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    alert("Please allow popups to download the PDF.");
    return;
  }

  printWindow.document.write(htmlContent);
  printWindow.document.close();

  // Wait for fonts and images to load, then print
  printWindow.onload = () => {
    setTimeout(() => {
      printWindow.print();
    }, 300);
  };

  // Fallback: if onload doesn't fire (some browsers), trigger after a delay
  setTimeout(() => {
    if (!printWindow.closed) {
      printWindow.print();
    }
  }, 1500);
}
