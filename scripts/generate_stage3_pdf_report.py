"""
Generate a comprehensive, publication-grade PDF report for Stage 3 CTTA Discovery
using ReportLab with NumberedCanvas, professional styling, exact tables, and embedded figures.
Revised to incorporate multi-order matrix across all 4 methods, paired speaker-cluster
bootstrap uncertainty analysis, refined scientific determinations, and perfectly balanced 4-page layout.
"""

import os
import json
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas


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
            self.drawString(45, 755, "DSG-CTTA: Stage 3 CTTA Discovery & Adaptation Disparity Report (Revised)")
            self.drawRightString(612 - 45, 755, "Protocol v1.0.0-canonical")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(45, 749, 612 - 45, 749)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(45, 38, 612 - 45, 38)
        self.drawString(45, 26, "Confidential — Academic Research Initiative — Stage 3 Discovery & Phenomenon Boundary Audit")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 45, 26, page_str)
        self.restoreState()


def build_stage3_pdf_report(
    output_pdf: str = "reports/stage3_discovery_report.pdf",
    ctta_dir: str = "reports/ctta"
):
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    # Color Palette
    c_primary = colors.HexColor("#1E3A8A")    # Deep Navy
    c_secondary = colors.HexColor("#0D9488")  # Teal
    c_dark = colors.HexColor("#0F172A")       # Dark Charcoal
    c_light_bg = colors.HexColor("#F8FAFC")   # Light Gray/Slate
    c_border = colors.HexColor("#CBD5E1")     # Light Border Gray
    c_accent_amber = colors.HexColor("#D97706") # Amber

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15.5,
        leading=19,
        textColor=c_primary,
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#475569"),
        spaceAfter=5
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=c_primary,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=c_secondary,
        spaceBefore=4,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=c_dark,
        spaceAfter=4
    )

    callout_text = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=8.5,
        textColor=colors.white,
        alignment=1  # Centered
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8.5,
        textColor=c_dark
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold'
    )

    table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=table_cell,
        alignment=1
    )

    table_cell_center_bold = ParagraphStyle(
        'TableCellCenterBold',
        parent=table_cell_bold,
        alignment=1
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE, EXECUTIVE SUMMARY, LOGIC, CANONICAL RESULTS (TABLE 1 & 2)
    # =========================================================================
    story.append(Paragraph("DSG-CTTA: Continual Test-Time Adaptation Discovery Report", title_style))
    story.append(Paragraph(
        "<b>Rigorous Empirical Characterization:</b> Performance Disparities, Subgroup Dynamics, "
        "and Prequential Robustness Across Continual Adaptation Baselines",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_primary, spaceBefore=1, spaceAfter=4))

    # Metadata Banner Table
    meta_data = [
        [
            Paragraph("<b>Protocol:</b> <code>v1.0.0-canonical</code>", table_cell),
            Paragraph("<b>Partition:</b> <code>final_test.csv</code> (60 utts, 6 spks)", table_cell),
            Paragraph("<b>Model:</b> <code>wav2vec2-base-960h</code>", table_cell)
        ],
        [
            Paragraph("<b>Paradigm:</b> Prequential (B<sub>t</sub> &rarr; &theta;<sub>t</sub>)", table_cell),
            Paragraph("<b>Isolation:</b> Air-Gapped Audio (0 text / 0 meta)", table_cell),
            Paragraph("<b>Scope:</b> 4 Methods &times; 3 Orders (12 runs)", table_cell)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[174, 184, 164])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. Executive Summary & Research Logic", h1_style))
    story.append(Paragraph(
        "<b>Stage 3 is technically successful as a CTTA discovery pilot, but it is not strong enough to conclude that adaptation-induced disparity does not occur.</b> "
        "The evaluation pipeline establishes a mathematically verified prequential streaming runtime across adaptation methods (SUTA, DSUTA, DMSUTA). "
        "We approve moving forward to <b>Stage 4: Larger-Scale Mechanism / Phenomenon Characterization</b>, but we explicitly <b>do NOT approve moving directly to Stage 5 (DSG)</b>. "
        "The static Stage 2 disparity baseline (<i>D</i><sub>0</sub>) serves strictly as the pre-adaptation reference (&theta;<sub>0</sub>), not as evidence that DSG is necessary.",
        body_style
    ))

    # Scale & Sensitivity Callout Box
    box_scale = [
        [
            Paragraph(
                "<b>BENCHMARK SCALE &amp; WORD-LEVEL SENSITIVITY:</b> "
                "The <code>final_test</code> stream contains 60 utterances, 6 speakers, and 552 reference words (~92 words per group). "
                "On a 92-word subgroup, <b>a single word classification alteration represents &Delta;WER<sub>g</sub> = 1/92 &approx; 1.09%</b>. "
                "The observed reverse-order regression of +1.09% corresponds literally to <b>one word</b>. "
                "A +1.09% change is a real observed numerical shift, but cannot be claimed as practically meaningful or statistically negligible without confidence intervals and larger-scale multi-speaker evaluation.",
                callout_text
            )
        ]
    ]
    t_scale = Table(box_scale, colWidths=[522])
    t_scale.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ('BOX', (0, 0), (-1, -1), 0.8, c_accent_amber),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_scale)
    story.append(Spacer(1, 4))

    # Invariants Box
    story.append(Paragraph(
        "<b>Prequential Protocol:</b> <code>B<sub>t</sub> &rarr; &theta;<sub>t</sub> Prediction &rarr; Offline Scoring &rarr; Unlabeled Adaptation &rarr; &theta;<sub>t+1</sub></code>. "
        "Window B<sub>t</sub> is never evaluated using &theta;<sub>t+1</sub>. Online runtime receives zero reference text, labels, speaker IDs, or accent metadata. "
        "Passing 25/25 automated tests proves implementation obeys invariants, <b>not</b> that the sample size is powered for a null claim.<br/>"
        "<b>Speech Variety vs Accent:</b> Groups represent <i>L1-associated English speech varieties</i> where phonology, proficiency, and acoustics are intertwined.<br/>"
        "<b>Window Size Protocol (K=4):</b> Chosen as the pre-registered default in <code>configs/default_config.yaml</code> (60/4 = 15 windows). "
        "In Stage 4, <i>K</i> &isin; {1, 4, 5, 10} will be calibrated on development/calibration splits before untouched final evaluation.",
        body_style
    ))
    story.append(Spacer(1, 3))

    # Table 1: Primary ORDER_A Results
    story.append(Paragraph("<b>Table 1: Canonical Stream Results (ORDER_A, K=4) Without Safety Intervention</b>", h2_style))
    headers_t1 = [
        Paragraph("<b>Method</b>", table_header),
        Paragraph("<b>Live Corpus WER</b>", table_header),
        Paragraph("<b>&Delta;<sub>R</sub> (Overall)</b>", table_header),
        Paragraph("<b>Disparity D</b>", table_header),
        Paragraph("<b>&Delta;<sub>D</sub> (Disparity)</b>", table_header),
        Paragraph("<b>Max Regr max<sub>g</sub>&Delta;<sub>g</sub></b>", table_header),
        Paragraph("<b>Worst Subgroup</b>", table_header),
        Paragraph("<b>Updates / Resets</b>", table_header)
    ]
    rows_t1 = [
        headers_t1,
        [Paragraph("<b>No-Adapt (Control)</b>", table_cell_bold), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("None", table_cell_center), Paragraph("0 / 0", table_cell_center)],
        [Paragraph("<b>SUTA</b>", table_cell_bold), Paragraph("85.14%", table_cell_center), Paragraph("<b>-0.37%</b>", table_cell_center), Paragraph("19.57%", table_cell_center), Paragraph("<b>-1.08%</b>", table_cell_center), Paragraph("<b>0.00%</b>", table_cell_center), Paragraph("None", table_cell_center), Paragraph("15 / 0", table_cell_center)],
        [Paragraph("<b>DSUTA</b>", table_cell_bold), Paragraph("85.33%", table_cell_center), Paragraph("<b>-0.18%</b>", table_cell_center), Paragraph("19.57%", table_cell_center), Paragraph("<b>-1.08%</b>", table_cell_center), Paragraph("<b>0.00%</b>", table_cell_center), Paragraph("None", table_cell_center), Paragraph("15 / 1", table_cell_center)],
        [Paragraph("<b>DMSUTA</b>", table_cell_bold), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("None", table_cell_center), Paragraph("15 / 0", table_cell_center)],
    ]
    t1 = Table(rows_t1, colWidths=[92, 62, 60, 60, 60, 72, 62, 54])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
    ]))
    story.append(t1)
    story.append(Spacer(1, 3))

    # Table 2: Group Breakdown on ORDER_A
    story.append(Paragraph("<b>Table 2: L1 Speech Variety Performance Breakdown on Canonical ORDER_A</b>", h2_style))
    headers_t2 = [
        Paragraph("<b>L1 Variety</b>", table_header),
        Paragraph("<b>No-Adapt WER</b>", table_header),
        Paragraph("<b>SUTA WER</b>", table_header),
        Paragraph("<b>SUTA &Delta;<sub>g</sub></b>", table_header),
        Paragraph("<b>DSUTA WER</b>", table_header),
        Paragraph("<b>DSUTA &Delta;<sub>g</sub></b>", table_header),
        Paragraph("<b>DMSUTA WER</b>", table_header),
        Paragraph("<b>DMSUTA &Delta;<sub>g</sub></b>", table_header)
    ]
    rows_t2 = [
        headers_t2,
        [Paragraph("Arabic", table_cell_bold), Paragraph("89.13%", table_cell_center), Paragraph("89.13%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("89.13%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("89.13%", table_cell_center), Paragraph("0.00%", table_cell_center)],
        [Paragraph("Hindi", table_cell_bold), Paragraph("97.83%", table_cell_center), Paragraph("96.74%", table_cell_center), Paragraph("<b>-1.09%</b>", table_cell_center), Paragraph("96.74%", table_cell_center), Paragraph("<b>-1.09%</b>", table_cell_center), Paragraph("97.83%", table_cell_center), Paragraph("0.00%", table_cell_center)],
        [Paragraph("Korean", table_cell_bold), Paragraph("82.61%", table_cell_center), Paragraph("82.61%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("82.61%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("82.61%", table_cell_center), Paragraph("0.00%", table_cell_center)],
        [Paragraph("Mandarin", table_cell_bold), Paragraph("77.17%", table_cell_center), Paragraph("77.17%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("77.17%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("77.17%", table_cell_center), Paragraph("0.00%", table_cell_center)],
        [Paragraph("Spanish", table_cell_bold), Paragraph("85.87%", table_cell_center), Paragraph("85.87%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("85.87%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("85.87%", table_cell_center), Paragraph("0.00%", table_cell_center)],
        [Paragraph("Vietnamese", table_cell_bold), Paragraph("80.43%", table_cell_center), Paragraph("79.35%", table_cell_center), Paragraph("<b>-1.08%</b>", table_cell_center), Paragraph("80.43%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("80.43%", table_cell_center), Paragraph("0.00%", table_cell_center)],
    ]
    t2 = Table(rows_t2, colWidths=[88, 62, 62, 62, 62, 62, 62, 62])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
    ]))
    story.append(t2)

    # =========================================================================
    # PAGE 2: PREQUENTIAL FIGURES & FULL MULTI-ORDER MATRIX (TABLE 3)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("2. Prequential Trajectories & Full Multi-Order Matrix", h1_style))
    story.append(Paragraph(
        "Four high-resolution prequential trajectory figures capture adaptation progression, disparity dynamics, and group trajectories:",
        body_style
    ))

    fig_overall = os.path.join(ctta_dir, "figures", "overall_wer_trajectory.png")
    fig_disp = os.path.join(ctta_dir, "figures", "disparity_trajectory.png")
    fig_grp = os.path.join(ctta_dir, "figures", "group_wer_trajectory_suta.png")
    fig_bar = os.path.join(ctta_dir, "figures", "cross_method_comparison.png")

    fig_grid = []
    if os.path.exists(fig_overall) and os.path.exists(fig_disp):
        fig_grid.append([
            Image(fig_overall, width=3.45*inch, height=1.7*inch),
            Image(fig_disp, width=3.45*inch, height=1.7*inch)
        ])
        fig_grid.append([
            Paragraph("<b>Figure 1:</b> Cumulative Prequential Overall WER Progression", table_cell_center),
            Paragraph("<b>Figure 2:</b> Prequential Cross-Group Disparity D<sub>t</sub> Dynamics", table_cell_center)
        ])

    if os.path.exists(fig_grp) and os.path.exists(fig_bar):
        fig_grid.append([
            Image(fig_grp, width=3.45*inch, height=1.7*inch),
            Image(fig_bar, width=3.45*inch, height=1.7*inch)
        ])
        fig_grid.append([
            Paragraph("<b>Figure 3:</b> Group-Level WER Trajectories under Continual SUTA", table_cell_center),
            Paragraph("<b>Figure 4:</b> Cross-Method Performance and Disparity Comparison", table_cell_center)
        ])

    if fig_grid:
        t_figs = Table(fig_grid, colWidths=[261, 261])
        t_figs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t_figs)

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Table 3: Full Multi-Order Robustness Matrix (4 Methods &times; 3 Stream Orders)</b>", h2_style))
    story.append(Paragraph(
        "To test stream-order sensitivity, No-Adapt, SUTA, DSUTA, and DMSUTA were evaluated across three stream permutations: "
        "<code>ORDER_A</code> (Canonical), <code>ORDER_B</code> (Reverse), and <code>ORDER_C</code> (Permuted):",
        body_style
    ))

    headers_t3 = [
        Paragraph("<b>Stream Order</b>", table_header),
        Paragraph("<b>Method</b>", table_header),
        Paragraph("<b>Corpus WER</b>", table_header),
        Paragraph("<b>&Delta;<sub>R</sub></b>", table_header),
        Paragraph("<b>Disparity D</b>", table_header),
        Paragraph("<b>&Delta;<sub>D</sub></b>", table_header),
        Paragraph("<b>Max Regr max<sub>g</sub>&Delta;<sub>g</sub></b>", table_header),
        Paragraph("<b>Worst Regressed Subgroup</b>", table_header)
    ]
    rows_t3 = [
        headers_t3,
        [Paragraph("<b>ORDER_A</b>", table_cell_bold), Paragraph("No-Adapt", table_cell), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("None", table_cell_center)],
        [Paragraph("<b>ORDER_A</b>", table_cell_bold), Paragraph("SUTA", table_cell_bold), Paragraph("85.14%", table_cell_center), Paragraph("<b>-0.37%</b>", table_cell_center), Paragraph("19.57%", table_cell_center), Paragraph("<b>-1.08%</b>", table_cell_center), Paragraph("<b>0.00%</b>", table_cell_center), Paragraph("None", table_cell_center)],
        [Paragraph("<b>ORDER_A</b>", table_cell_bold), Paragraph("DSUTA", table_cell_bold), Paragraph("85.33%", table_cell_center), Paragraph("<b>-0.18%</b>", table_cell_center), Paragraph("19.57%", table_cell_center), Paragraph("<b>-1.08%</b>", table_cell_center), Paragraph("<b>0.00%</b>", table_cell_center), Paragraph("None", table_cell_center)],
        [Paragraph("<b>ORDER_A</b>", table_cell_bold), Paragraph("DMSUTA", table_cell_bold), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("None", table_cell_center)],
        [Paragraph("<b>ORDER_B</b>", table_cell_bold), Paragraph("No-Adapt", table_cell), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("None", table_cell_center)],
        [Paragraph("<b>ORDER_B</b>", table_cell_bold), Paragraph("SUTA", table_cell_bold), Paragraph("85.69%", table_cell_center), Paragraph("<b>+0.18%</b>", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("<b>+1.09%</b>", table_cell_center), Paragraph("Arabic", table_cell_center)],
        [Paragraph("<b>ORDER_B</b>", table_cell_bold), Paragraph("DSUTA", table_cell_bold), Paragraph("85.14%", table_cell_center), Paragraph("<b>-0.37%</b>", table_cell_center), Paragraph("19.57%", table_cell_center), Paragraph("<b>-1.08%</b>", table_cell_center), Paragraph("<b>+1.09%</b>", table_cell_center), Paragraph("Vietnamese", table_cell_center)],
        [Paragraph("<b>ORDER_B</b>", table_cell_bold), Paragraph("DMSUTA", table_cell_bold), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("19.57%", table_cell_center), Paragraph("<b>-1.08%</b>", table_cell_center), Paragraph("<b>+1.09%</b>", table_cell_center), Paragraph("Arabic", table_cell_center)],
        [Paragraph("<b>ORDER_C</b>", table_cell_bold), Paragraph("No-Adapt", table_cell), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("None", table_cell_center)],
        [Paragraph("<b>ORDER_C</b>", table_cell_bold), Paragraph("SUTA", table_cell_bold), Paragraph("85.51%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("<b>+1.09%</b>", table_cell_center), Paragraph("Spanish", table_cell_center)],
        [Paragraph("<b>ORDER_C</b>", table_cell_bold), Paragraph("DSUTA", table_cell_bold), Paragraph("85.14%", table_cell_center), Paragraph("<b>-0.37%</b>", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("<b>0.00%</b>", table_cell_center), Paragraph("None", table_cell_center)],
        [Paragraph("<b>ORDER_C</b>", table_cell_bold), Paragraph("DMSUTA", table_cell_bold), Paragraph("85.33%", table_cell_center), Paragraph("<b>-0.18%</b>", table_cell_center), Paragraph("20.65%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("<b>+1.09%</b>", table_cell_center), Paragraph("Vietnamese", table_cell_center)],
    ]
    t3 = Table(rows_t3, colWidths=[66, 68, 60, 52, 60, 52, 80, 84])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_dark),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
    ]))
    story.append(t3)

    # =========================================================================
    # PAGE 3: BOOTSTRAP UNCERTAINTY (TABLE 4) & EVIDENCE BOUNDARIES
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Statistical Uncertainty & Evidence Boundary", h1_style))
    story.append(Paragraph(
        "<b>Table 4: Paired Speaker-Cluster Bootstrap Analysis (B=1,000 resamples, &alpha;=0.05).</b> "
        "Confidence intervals explicitly distinguish observed numerical changes from statistically verified effects:",
        body_style
    ))

    headers_t4 = [
        Paragraph("<b>Order</b>", table_header),
        Paragraph("<b>Method</b>", table_header),
        Paragraph("<b>Metric</b>", table_header),
        Paragraph("<b>Point Est</b>", table_header),
        Paragraph("<b>Boot Mean</b>", table_header),
        Paragraph("<b>Std Error</b>", table_header),
        Paragraph("<b>95% Confidence Interval</b>", table_header),
        Paragraph("<b>95% UCB</b>", table_header)
    ]
    rows_t4 = [
        headers_t4,
        # ORDER_A
        [Paragraph("ORDER_A", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("-0.37%", table_cell_center), Paragraph("-0.35%", table_cell_center), Paragraph("0.20%", table_cell_center), Paragraph("[-0.72%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("-1.08%", table_cell_center), Paragraph("-0.72%", table_cell_center), Paragraph("0.52%", table_cell_center), Paragraph("[-1.09%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("[0.00%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("-0.18%", table_cell_center), Paragraph("-0.17%", table_cell_center), Paragraph("0.16%", table_cell_center), Paragraph("[-0.54%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("-1.08%", table_cell_center), Paragraph("-0.71%", table_cell_center), Paragraph("0.52%", table_cell_center), Paragraph("[-1.09%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("[0.00%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("[0.00%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("[0.00%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_A", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("[0.00%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        # ORDER_B
        [Paragraph("ORDER_B", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("+0.18%", table_cell_center), Paragraph("+0.18%", table_cell_center), Paragraph("0.16%", table_cell_center), Paragraph("[0.00%, +0.54%]", table_cell_center_bold), Paragraph("+0.54%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("+0.29%", table_cell_center), Paragraph("0.48%", table_cell_center), Paragraph("[0.00%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("+1.09%", table_cell_center), Paragraph("+0.74%", table_cell_center), Paragraph("0.51%", table_cell_center), Paragraph("[0.00%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("-0.37%", table_cell_center), Paragraph("-0.37%", table_cell_center), Paragraph("0.32%", table_cell_center), Paragraph("[-0.91%, +0.36%]", table_cell_center_bold), Paragraph("+0.18%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("-1.08%", table_cell_center), Paragraph("-1.07%", table_cell_center), Paragraph("0.16%", table_cell_center), Paragraph("[-1.09%, -1.09%]", table_cell_center_bold), Paragraph("-1.09%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("+1.09%", table_cell_center), Paragraph("+0.73%", table_cell_center), Paragraph("0.51%", table_cell_center), Paragraph("[0.00%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("+0.01%", table_cell_center), Paragraph("0.25%", table_cell_center), Paragraph("[-0.54%, +0.54%]", table_cell_center_bold), Paragraph("+0.36%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("-1.08%", table_cell_center), Paragraph("-0.42%", table_cell_center), Paragraph("0.96%", table_cell_center), Paragraph("[-1.09%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
        [Paragraph("ORDER_B", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("+1.09%", table_cell_center), Paragraph("+0.74%", table_cell_center), Paragraph("0.51%", table_cell_center), Paragraph("[0.00%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
        # ORDER_C
        [Paragraph("ORDER_C", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.25%", table_cell_center), Paragraph("[-0.54%, +0.54%]", table_cell_center_bold), Paragraph("+0.36%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("-0.22%", table_cell_center), Paragraph("0.58%", table_cell_center), Paragraph("[-1.09%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("SUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("+1.09%", table_cell_center), Paragraph("+0.74%", table_cell_center), Paragraph("0.51%", table_cell_center), Paragraph("[0.00%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("-0.37%", table_cell_center), Paragraph("-0.37%", table_cell_center), Paragraph("0.21%", table_cell_center), Paragraph("[-0.72%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("-0.36%", table_cell_center), Paragraph("0.51%", table_cell_center), Paragraph("[-1.09%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("DSUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("0.00%", table_cell_center), Paragraph("[0.00%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("&Delta;<sub>R</sub>", table_cell), Paragraph("-0.18%", table_cell_center), Paragraph("-0.19%", table_cell_center), Paragraph("0.39%", table_cell_center), Paragraph("[-1.09%, +0.54%]", table_cell_center_bold), Paragraph("+0.36%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("&Delta;<sub>D</sub>", table_cell), Paragraph("0.00%", table_cell_center), Paragraph("-0.58%", table_cell_center), Paragraph("0.96%", table_cell_center), Paragraph("[-2.17%, 0.00%]", table_cell_center_bold), Paragraph("0.00%", table_cell_center)],
        [Paragraph("ORDER_C", table_cell), Paragraph("DMSUTA", table_cell_bold), Paragraph("max<sub>g</sub>&Delta;<sub>g</sub>", table_cell), Paragraph("+1.09%", table_cell_center), Paragraph("+0.73%", table_cell_center), Paragraph("0.51%", table_cell_center), Paragraph("[0.00%, +1.09%]", table_cell_center_bold), Paragraph("+1.09%", table_cell_center)],
    ]
    t4 = Table(rows_t4, colWidths=[54, 50, 48, 50, 50, 50, 130, 50])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
    ]))
    story.append(t4)
    story.append(Spacer(1, 4))

    # Evidence Boundaries Table
    story.append(Paragraph("<b>Scientific Boundaries: What Stage 3 Has vs Has NOT Demonstrated</b>", h2_style))
    box_evidence = [
        [
            Paragraph("<b>NOT DEMONSTRATED BY CURRENT EVIDENCE:</b>", table_cell_bold),
            Paragraph("<b>DEMONSTRATED &amp; EMPIRICALLY OBSERVED:</b>", table_cell_bold)
        ],
        [
            Paragraph(
                "&times; CTTA causes disparity amplification (&Delta;<sub>D</sub> &gt; &delta;<sub>D</sub>)<br/>"
                "&times; CTTA causes systematic subgroup regression (&max;<sub>g</sub> &Delta;<sub>g</sub> &gt; &delta;<sub>G</sub>)<br/>"
                "&times; SUTA is harmful / DSUTA is harmful<br/>"
                "&times; DMSUTA is safe<br/>"
                "&times; DSG is necessary<br/>"
                "&times; DSG will improve fairness",
                table_cell
            ),
            Paragraph(
                "&check; CTTA can slightly change overall WER (&Delta;<sub>R</sub> &in; [-0.37%, +0.18%])<br/>"
                "&check; SUTA / DSUTA produced small gains on ORDER_A (-0.37%, -0.18%)<br/>"
                "&check; DMSUTA produced flat aggregate WER on ORDER_A (0.00%)<br/>"
                "&check; Small order-dependent subgroup regression (+1.09%, 1 word) observed<br/>"
                "&check; No disparity amplification observed on any tested stream (&Delta;<sub>D</sub> &le; 0.00%)<br/>"
                "&check; Prequential/label-isolation passed all 25 automated tests",
                table_cell
            )
        ]
    ]
    t_ev = Table(box_evidence, colWidths=[256, 266])
    t_ev.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_light_bg),
        ('BOX', (0, 0), (-1, -1), 0.8, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_ev)

    # =========================================================================
    # PAGE 4: COUPLING DETERMINATION, STAGE 4 MANDATE & PROVENANCE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. Coupling Determination, Stage 4 Mandate & Provenance", h1_style))

    box_coupling = [
        [
            Paragraph(
                "<b>CANONICAL SCIENTIFIC DETERMINATION (MANDATORY STANDARD):</b><br/>"
                "<b>\"Meaningful coupling is not demonstrated on the current benchmark stream. "
                "The observed changes are small, and the current sample size and unfrozen practical-effect "
                "threshold prevent a stronger conclusion regarding the absence of adaptation-induced subgroup harm.\"</b><br/><br/>"
                "&bull; <i>Practical Significance Threshold (&delta;):</i> Status remains <code>UNKNOWN: delta not frozen sufficiently for final discovery</code>. "
                "No post-hoc threshold was manufactured from test data.<br/>"
                "&bull; <i>Permissible Scientific Claim:</i> No practically meaningful coupling was demonstrated under current pilot conditions.<br/>"
                "&bull; <i>Impermissible Claim:</i> We do NOT claim proof that CTTA does not cause disparity amplification.",
                callout_text
            )
        ]
    ]
    t_coup = Table(box_coupling, colWidths=[522])
    t_coup.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ('BOX', (0, 0), (-1, -1), 1, c_accent_amber),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_coup)
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Stage 4 Mandate &amp; Execution Architecture</b>", h2_style))
    story.append(Paragraph(
        "<b>1. NO-GO for Stage 5 DSG on Current Final Test Stream:</b> "
        "Proceeding directly to build DSG safety controllers without empirical evidence of disparity amplification would violate scientific integrity.<br/>"
        "<b>2. PROCEED to Stage 4 (Phenomenon Characterization) to test boundary conditions:</b><br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4A (Data-Scale Expansion):</b> Maximize disjoint independent speakers across Dev, Cal, Sentinel, and Final Test splits.<br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4B (Freeze &delta;<sub>G</sub> / &delta;<sub>D</sub>):</b> Statistically derive &delta; via calibration power analysis and smallest practically important effect.<br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4C (Window-Size Experiments):</b> Sweep <i>K</i> &isin; {1, 4, 5, 10} on Dev/Cal splits before untouched final evaluation.<br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4D (Multi-Order Matrix):</b> Test all primary CTTA methods across multiple stream permutations.<br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4E (Acoustic Stress Testing):</b> Introduce controlled distribution shifts (additive babble noise, SNR steps, non-stationary shift).<br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4F (Speaker-Cluster Uncertainty):</b> Full paired bootstrap 95% CIs for &Delta;<sub>R</sub>, &Delta;<sub>g</sub>, and &Delta;<sub>D</sub> across all conditions.<br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4G (Condition-Wise Boundaries):</b> Map multidimensional instability boundaries (Method &times; Order &times; K &times; Shift Severity).<br/>"
        "&nbsp;&nbsp;&bull; <b>Stage 4H (GO / NO-GO for DSG):</b> Implement DSG in Stage 5 <i>only</i> if coupling is demonstrated under characterized conditions.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Provenance Table
    story.append(Paragraph("<b>Technical Provenance &amp; Verification Audit</b>", h2_style))
    prov_data = [
        [Paragraph("<b>Artifact / Verification Check</b>", table_header), Paragraph("<b>Observed Fingerprint / Value</b>", table_header), Paragraph("<b>Verification Status</b>", table_header)],
        [Paragraph("Stream ORDER_A Hash", table_cell), Paragraph("e02b45a1fd007011f1816e88907de3507d4b29bb883c58b4...", table_cell), Paragraph("VERIFIED (Deterministic)", table_cell_center)],
        [Paragraph("Stream ORDER_B Hash", table_cell), Paragraph("e45bd9d0921c06db18d80f68e09f5fa414a383b0fce04bda...", table_cell), Paragraph("VERIFIED (Distinct)", table_cell_center)],
        [Paragraph("Stream ORDER_C Hash", table_cell), Paragraph("5dc02804e713625afae2cfbbd8e03e7d446b0b2e3e6015ca...", table_cell), Paragraph("VERIFIED (Permuted)", table_cell_center)],
        [Paragraph("Prequential Live Invariant", table_cell), Paragraph("Window B_t scored with theta_t strictly prior to update", table_cell), Paragraph("VERIFIED (Air-Gapped)", table_cell_center)],
        [Paragraph("Multi-Order Matrix Scope", table_cell), Paragraph("All 4 Methods x 3 Stream Orders (12 experimental runs)", table_cell), Paragraph("VERIFIED (Complete)", table_cell_center)],
        [Paragraph("Speaker-Cluster Bootstrap", table_cell), Paragraph("B=1,000 paired resamples for Delta_R, Delta_D, max Delta_g", table_cell), Paragraph("VERIFIED (Alpha=0.05)", table_cell_center)],
        [Paragraph("Automated Test Suite", table_cell), Paragraph("25 / 25 Passing (19 baseline + 6 prequential)", table_cell), Paragraph("PASS (100%)", table_cell_center)]
    ]
    t_prov = Table(prov_data, colWidths=[134, 248, 140])
    t_prov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
    ]))
    story.append(t_prov)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_pdf


if __name__ == "__main__":
    pdf_path = build_stage3_pdf_report()
    print(f"Stage 3 PDF successfully generated: {pdf_path}")
