"""
Builds publication-quality PDF documents for StegoVault:
1. PROJECT_REPORT.pdf  (Formal academic project report)
2. VIVA_PREPARATION.pdf (Viva exam cheat sheet & presentation guide)
"""

import os
import re
import markdown
from xhtml2pdf import pisa


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def clean_markdown_for_pdf(text: str) -> str:
    """Removes emoji glyphs and normalizes LaTeX math blocks for clean PDF rendering."""
    # Remove emoji characters that standard PDF fonts cannot render
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)

    # Clean display math blocks to clean readable expressions
    text = text.replace("$$\\text{MSE} = \\frac{1}{K} \\sum_{i=1}^{K} \\left( C_i^{\\text{original}} - C_i^{\\text{stego}} \\right)^2$$",
                        "<div class='math-box'><b>MSE</b> = (1 / K) * sum( (C<sub>original</sub>(i) - C<sub>stego</sub>(i))<sup>2</sup> )</div>")
    text = text.replace("$$\\text{PSNR} = 10 \\cdot \\log_{10}\\left( \\frac{255^2}{\\text{MSE}} \\right) \\quad (\\text{dB})$$",
                        "<div class='math-box'><b>PSNR</b> = 10 * log<sub>10</sub>( 255<sup>2</sup> / MSE ) &nbsp; (in dB)</div>")
    text = text.replace("$$DK = \\text{PBKDF2}(P, S, c, dkLen)$$",
                        "<div class='math-box'><b>DK</b> = PBKDF2(Passphrase, Salt, c = 480,000, dkLen = 32 bytes)</div>")
    text = text.replace("$$\\text{Payload} = \\text{Salt (16 bytes)} \\ || \\ \\text{Ciphertext (N bytes)}$$",
                        "<div class='math-box'><b>Payload</b> = Salt (16 bytes) || Ciphertext (N bytes)</div>")
    text = text.replace("$$\\text{Cap}_{\\text{max}} = \\left\\lfloor \\frac{(W \\times H \\times 3) - 32}{8} \\right\\rfloor$$",
                        "<div class='math-box'><b>Capacity<sub>max</sub></b> = floor( ((Width * Height * 3) - 32) / 8 ) &nbsp; bytes</div>")

    # Clean inline Greek or special characters
    text = text.replace("Σ", "sum")
    text = text.replace("⌊", "floor(")
    text = text.replace("⌋", ")")
    text = text.replace("χ²", "Chi-Square (chi^2)")
    text = text.replace("≈", "approx. ")
    text = text.replace("•", "&bull;")
    text = text.replace("±", "&plusmn;")
    text = text.replace("≤", "&le;")
    text = text.replace("≥", "&ge;")

    # Clean inline LaTeX
    text = re.sub(r"\$([^\$]+)\$", r"<i>\1</i>", text)

    return text


def build_pdf(md_filename: str, pdf_filename: str, document_title: str, is_formal_report: bool = False):
    md_path = os.path.join(BASE_DIR, md_filename)
    pdf_path = os.path.join(BASE_DIR, pdf_filename)

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    cleaned_md = clean_markdown_for_pdf(md_text)

    # Convert to HTML
    body_html = markdown.markdown(
        cleaned_md,
        extensions=["extra", "tables", "fenced_code", "nl2br"],
    )

    cover_page_html = ""
    if is_formal_report:
        # Separate title from content for a dedicated cover page
        cover_page_html = """
        <div class="cover-page">
            <div style="font-size: 11pt; letter-spacing: 2px; text-transform: uppercase; color: #475569; margin-bottom: 25px;">
                Bachelor of Technology in Computer Science &amp; Engineering
            </div>
            <div style="font-size: 12pt; color: #64748b; margin-bottom: 35px;">
                A MINOR PROJECT REPORT ON
            </div>
            <h1 style="font-size: 22pt; color: #1e3a8a; line-height: 1.3; margin-bottom: 20px; border: none;">
                DUAL-LAYER IMAGE STEGANOGRAPHY WITH AUTHENTICATED AES ENCRYPTION
            </h1>
            <div style="font-size: 11pt; color: #334155; margin-bottom: 60px;">
                Secure Spatial Domain LSB Embedding with PBKDF2 Key Derivation
            </div>

            <div style="margin-top: 80px; margin-bottom: 40px;">
                <div style="font-size: 10pt; color: #64748b; margin-bottom: 6px;">SUBMITTED BY:</div>
                <div style="font-size: 15pt; font-weight: bold; color: #0f172a;">AMARTYA BHUSHAN</div>
                <div style="font-size: 10.5pt; color: #475569; margin-top: 4px;">Department of Computer Science &amp; Engineering</div>
            </div>

            <div style="margin-top: 70px; border-top: 1px solid #cbd5e1; padding-top: 15px; font-size: 9.5pt; color: #64748b;">
                Academic Session 2025 &ndash; 2026
            </div>
        </div>
        <div style="page-break-before: always;"></div>
        """

    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{document_title}</title>
    <style>
        @page {{
            size: a4 portrait;
            margin: 22mm 18mm 22mm 18mm;
            @bottom-right {{
                content: "Page " counter(page);
                font-size: 8.5pt;
                font-family: Helvetica, Arial, sans-serif;
                color: #64748b;
            }}
            @bottom-left {{
                content: "StegoVault • Academic Security Project";
                font-size: 8pt;
                font-family: Helvetica, Arial, sans-serif;
                color: #94a3b8;
            }}
        }}

        body {{
            font-family: Helvetica, Arial, sans-serif;
            font-size: 9.5pt;
            line-height: 1.55;
            color: #1e293b;
        }}

        .cover-page {{
            text-align: center;
            padding-top: 40px;
        }}

        h1 {{
            font-size: 17pt;
            color: #1e3a8a;
            border-bottom: 1.5px solid #1e3a8a;
            padding-bottom: 4px;
            margin-top: 22px;
            margin-bottom: 12px;
            page-break-after: avoid;
        }}

        h2 {{
            font-size: 13pt;
            color: #1e40af;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 3px;
            margin-top: 18px;
            margin-bottom: 8px;
            page-break-after: avoid;
        }}

        h3 {{
            font-size: 11pt;
            color: #0f172a;
            margin-top: 14px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }}

        h4 {{
            font-size: 10pt;
            color: #334155;
            margin-top: 10px;
            margin-bottom: 4px;
            page-break-after: avoid;
        }}

        p {{
            margin-bottom: 8px;
            text-align: justify;
        }}

        ul, ol {{
            margin-top: 4px;
            margin-bottom: 10px;
            padding-left: 22px;
        }}

        li {{
            margin-bottom: 4px;
        }}

        table {{
            width: 100%;
            margin-top: 12px;
            margin-bottom: 14px;
            font-size: 8.5pt;
        }}

        th {{
            background-color: #1e3a8a;
            color: #ffffff;
            font-weight: bold;
            padding: 6px 8px;
            border: 1px solid #94a3b8;
            text-align: left;
        }}

        td {{
            padding: 5px 8px;
            border: 1px solid #cbd5e1;
            vertical-align: top;
        }}

        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}

        pre {{
            background-color: #f1f5f9;
            border: 1px solid #cbd5e1;
            padding: 8px 10px;
            font-family: Courier, monospace;
            font-size: 8pt;
            line-height: 1.35;
            margin-top: 8px;
            margin-bottom: 10px;
        }}

        code {{
            font-family: Courier, monospace;
            background-color: #f1f5f9;
            padding: 1px 3px;
            font-size: 8.5pt;
            color: #0f172a;
        }}

        blockquote {{
            background-color: #f8fafc;
            border-left: 3.5px solid #2563eb;
            margin: 8px 0;
            padding: 6px 12px;
            color: #334155;
        }}

        .math-box {{
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 3px solid #0284c7;
            padding: 6px 12px;
            margin: 8px 0;
            font-size: 9.5pt;
            color: #0f172a;
        }}

        hr {{
            border: 0;
            border-top: 1px solid #cbd5e1;
            margin: 16px 0;
        }}
    </style>
</head>
<body>
    {cover_page_html}
    {body_html}
</body>
</html>"""

    with open(pdf_path, "wb") as f_out:
        status = pisa.CreatePDF(full_html, dest=f_out)

    if status.err:
        print(f"Error compiling {pdf_filename}")
        return False
    else:
        file_size = os.path.getsize(pdf_path)
        print(f"Generated {pdf_filename} successfully ({file_size:,} bytes)")
        return True


if __name__ == "__main__":
    print("Generating StegoVault documentation PDFs...")
    build_pdf("PROJECT_REPORT.md", "PROJECT_REPORT.pdf", "StegoVault - Minor Project Report", is_formal_report=True)
    build_pdf("VIVA_PREPARATION.md", "VIVA_PREPARATION.pdf", "StegoVault - Viva Defense & Presentation Guide", is_formal_report=False)
    print("Done!")
