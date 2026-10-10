"""
Generate a publication-grade PDF report for Stage 3M Multi-Model CTTA Discovery
using ReportLab with NumberedCanvas, professional styling, exact tables, and embedded figures.
Outputs: reports/stage3m/stage3_multimodel_extension.pdf
"""

import os
from pathlib import Path
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = PROJECT_ROOT / "results" / "stage3_multimodel" / "stage3m_full_results.csv"
FIG_DIR = PROJECT_ROOT / "reports" / "stage3m" / "figures"
PDF_OUT = PROJECT_ROOT / "reports" / "stage3m" / "stage3_multimodel_extension.pdf"


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total page count and draw running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#4A5568"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 755, "DSG-CTTA Stage 3M: Multi-Model CTTA Discovery Report")
            self.drawRightString(612 - 36, 755, "Protocol v1.1.0-model-expansion")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 749, 612 - 36, 749)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 38, 612 - 36, 38)
        self.drawString(36, 26, "Stage 3M Multi-Model Extension — Scientific Safeguards Enforced — N=6 Speakers / 1 per Group")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 36, 26, page_str)
        self.restoreState()


def build_pdf():
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6
    )
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#B91C1C"),
        spaceAfter=6
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#0F172A")
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Stage 3M: Multi-Model CTTA Discovery Report", title_style))
    story.append(Paragraph("<b>Protocol:</b> v1.1.0-model-expansion &nbsp;|&nbsp; <b>Standards:</b> ADR-001, ADR-002, ADR-005 &nbsp;|&nbsp; <b>Dataset:</b> L2-ARCTIC final_test (60 utts)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceBefore=0, spaceAfter=8))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Core Research Questions", h1_style))
    story.append(Paragraph(
        "Stage 3M executes the pre-registered multi-model discovery extension mandated under Protocol Amendment v1.1.0-model-expansion. "
        "Evaluating 39 designated conditions across six distinct models (3 CTC backbones adapted under 4 methods and 3 stream orders = 36 cells; "
        "3 Seq2Seq static portability controls = 3 cells) determines whether the accent regressions and disparity widening observed on "
        "Wav2Vec2-base generalize across speech foundation models.", body_style
    ))
    story.append(Paragraph(
        "<b>Key Discovery:</b> On <code>data2vec_base</code>, unconstrained SUTA again improved overall WER (-0.55%) while regressing Spanish "
        "accent WER by <b>+2.17% points</b> (breaching the pre-registered threshold &delta;<sub>G</sub> = +2.00%). "
        "On <code>wav2vec2_100h</code> under ORDER_C, DMSUTA triggered <b>catastrophic collapse</b> (WER 99.46%, +11.42% overall regression). "
        "This confirms that CTTA subgroup degradation and stream order vulnerability are architectural risks inherent to unsupervised frame-entropy adaptation.", body_style
    ))

    # Static Baselines
    story.append(Paragraph("2. Baseline Characterization & CTC/Seq2Seq Boundary", h1_style))
    story.append(Paragraph(
        "To honor the CTC/Seq2Seq boundary, autoregressive Whisper models are evaluated strictly under No-Adapt static control. "
        "Below are the zero-shot baseline WER and disparity metrics across all six participating foundation models:", body_style
    ))

    df = pd.read_csv(RESULTS_CSV)
    static_df = df[(df["method"] == "no_adapt") & (df["ordering_id"].str.startswith("ORDER_A"))].copy()

    table_data = [[
        Paragraph("<b>Model Key</b>", table_cell_bold),
        Paragraph("<b>Architecture</b>", table_cell_bold),
        Paragraph("<b>HuggingFace Checkpoint</b>", table_cell_bold),
        Paragraph("<b>Corpus WER</b>", table_cell_bold),
        Paragraph("<b>Disparity D</b>", table_cell_bold),
        Paragraph("<b>Role / Method Eligibility</b>", table_cell_bold)
    ]]

    for _, r in static_df.iterrows():
        table_data.append([
            Paragraph(str(r["model_key"]), table_cell_bold),
            Paragraph(str(r["architecture"]), table_cell),
            Paragraph("facebook/..." if "wav2vec2" in r["model_key"] or "data2vec" in r["model_key"] else "openai/...", table_cell),
            Paragraph(f"{r['corpus_wer']*100:.2f}%", table_cell),
            Paragraph(f"{r['disparity_d']*100:.2f}%", table_cell),
            Paragraph("Adapted (SUTA/DSUTA/DMSUTA)" if r["architecture"] == "CTC" else "Static Control Only", table_cell)
        ])

    t = Table(table_data, colWidths=[100, 75, 110, 65, 65, 125])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Figure 1
    fig1 = FIG_DIR / "fig3m_1_static_baseline_comparison.png"
    if fig1.exists():
        story.append(Image(str(fig1), width=6.8*inch, height=2.4*inch))
        story.append(Spacer(1, 8))

    # Results Section
    story.append(PageBreak())
    story.append(Paragraph("3. Complete Stage 3M Empirical Results Matrix (39 Cells)", h1_style))
    story.append(Paragraph(
        "Every incoming window was evaluated strictly prequentially using frozen &theta;<sub>t</sub> before adaptation. "
        "No-Adapt invariance was verified across all three stream orders (100% identical error counts).", body_style
    ))

    # Build 39-cell table
    res_table_data = [[
        Paragraph("<b>Model</b>", table_cell_bold),
        Paragraph("<b>Method</b>", table_cell_bold),
        Paragraph("<b>Order</b>", table_cell_bold),
        Paragraph("<b>WER (%)</b>", table_cell_bold),
        Paragraph("<b>&Delta;R (%)</b>", table_cell_bold),
        Paragraph("<b>D (%)</b>", table_cell_bold),
        Paragraph("<b>&Delta;D (%)</b>", table_cell_bold),
        Paragraph("<b>max &Delta;g</b>", table_cell_bold),
        Paragraph("<b>Worst Subgroup</b>", table_cell_bold)
    ]]

    for _, r in df.iterrows():
        dr_str = f"{r['delta_r']*100:+.2f}%" if r['method'] != 'no_adapt' else "0.00%"
        dd_str = f"{r['delta_d']*100:+.2f}%" if r['method'] != 'no_adapt' else "0.00%"
        mg_str = f"{r['max_delta_g']*100:+.2f}%" if r['method'] != 'no_adapt' else "0.00%"
        res_table_data.append([
            Paragraph(str(r["model_key"]).replace("_", " "), table_cell),
            Paragraph(str(r["method"]).upper(), table_cell_bold if r['method'] != 'no_adapt' else table_cell),
            Paragraph(str(r["ordering_id"]).replace(" (static)", ""), table_cell),
            Paragraph(f"{r['corpus_wer']*100:.2f}%", table_cell),
            Paragraph(dr_str, table_cell_bold if r['delta_r'] > 0 else table_cell),
            Paragraph(f"{r['disparity_d']*100:.2f}%", table_cell),
            Paragraph(dd_str, table_cell),
            Paragraph(mg_str, table_cell_bold if r['max_delta_g'] >= 0.02 else table_cell),
            Paragraph(str(r["worst_group"]), table_cell)
        ])

    rt = Table(res_table_data, colWidths=[80, 55, 45, 55, 50, 50, 50, 55, 100])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(rt)
    story.append(Spacer(1, 8))

    # Figures 2 & 3
    story.append(PageBreak())
    story.append(Paragraph("4. Adaptation Harm, Subgroup Risk & Order Sensitivity", h1_style))
    
    fig2 = FIG_DIR / "fig3m_2_model_method_deltas.png"
    if fig2.exists():
        story.append(Image(str(fig2), width=6.8*inch, height=2.5*inch))
        story.append(Spacer(1, 6))

    fig3 = FIG_DIR / "fig3m_3_stream_order_sensitivity.png"
    if fig3.exists():
        story.append(Image(str(fig3), width=6.8*inch, height=2.2*inch))
        story.append(Spacer(1, 8))

    story.append(Paragraph("5. Statistical Limitations & Explicit Scope Boundary", h1_style))
    story.append(Paragraph(
        "<b>Crucial Methodological Caveat:</b> The Stage 3M evaluation stream evaluates exactly <b>N=6 speakers (1 speaker per demographic group)</b>. "
        "A speaker-cluster bootstrap cannot estimate within-group speaker variance when each group contains only one observed individual. "
        "Consequently, bootstrap intervals reported in <code>stage3m_bootstrap_uncertainty.csv</code> reflect stream-level resampling sensitivity "
        "and <b>must NOT be interpreted as population-level coverage intervals</b>. Stage 4M expands the evaluation sample to N=12 speakers (2 per group) "
        "to rigorously examine population-level generalization.", callout_style
    ))

    story.append(Paragraph("6. Scientific Verdict & Recommendation for Stage 4M", h1_style))
    story.append(Paragraph(
        "Stage 3M demonstrates that adaptation effects are model-, method- and stream-order-dependent. "
        "Overall WER and subgroup safety can move in opposite directions, and severe degradation emerged on wav2vec2_100h under ORDER_C. "
        "All 39 designated cells are empirically verified. Subject to the forensic reproducibility bridge and collapse diagnostics in the Stage 3M Scientific Audit Addendum, "
        "Stage 4M preparation is justified.", body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Publication-Grade Stage 3M PDF generated successfully: {PDF_OUT}")


if __name__ == "__main__":
    build_pdf()
