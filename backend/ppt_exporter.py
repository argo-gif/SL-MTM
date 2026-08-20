import os
import sys
import copy
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

try:
    import pptx
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    HAS_PYTHON_PPTX = True
except ImportError:
    HAS_PYTHON_PPTX = False


def format_month_label(m_str: Any) -> str:
    if not m_str or str(m_str).lower() in ['all', 'semua', 'semua bulan', 'none']:
        return "Semua Bulan"
    months_id = {
        '01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR', '05': 'MEI', '06': 'JUN',
        '07': 'JUL', '08': 'AGU', '09': 'SEP', '10': 'OKT', '11': 'NOV', '12': 'DES'
    }
    parts = str(m_str).split('-')
    if len(parts) == 2:
        yr, mo = parts[0], parts[1]
        return f"{months_id.get(mo, mo)}-{yr}"
    return str(m_str)


class MTMPPTExporter:
    def __init__(self, template_path: str = "Template PPT.pptx"):
        self.template_path = template_path

    def generate_presentation(self, export_data: Dict[str, Any], output_path: str = "output_report.pptx") -> str:
        """
        Generate PowerPoint presentation based on Template PPT.pptx with complete slide data population matching dashboard filters.
        """
        if HAS_PYTHON_PPTX and os.path.exists(self.template_path):
            return self._generate_with_python_pptx(export_data, output_path)
        else:
            return self._generate_fallback(export_data, output_path)

    def _generate_with_python_pptx(self, export_data: Dict[str, Any], output_path: str) -> str:
        prs = Presentation(self.template_path)

def build_active_filters_summary(filters: Dict[str, Any]) -> str:
    if not filters:
        return "📌 Filter Aktif: Semua Data"

    parts = []

    # 1. Month
    m_val = filters.get("months") or filters.get("month")
    if m_val:
        if isinstance(m_val, list):
            valid_m = [format_month_label(m) for m in m_val if m and str(m).upper() not in ["ALL", "SEMUA", "SEMUA BULAN"]]
            if valid_m:
                if len(valid_m) == 1:
                    parts.append(f"Bulan = {valid_m[0]}")
                else:
                    parts.append(f"Bulan = {len(valid_m)} Terpilih ({', '.join(valid_m[:2])})")
        else:
            lbl = format_month_label(m_val)
            if lbl != "Semua Bulan":
                parts.append(f"Bulan = {lbl}")
    if not any(p.startswith("Bulan =") for p in parts):
        parts.append("Bulan = AGU-2026")

    # 2. MTM Type
    t_val = filters.get("mtm_types") or filters.get("mtm_type")
    if t_val:
        if isinstance(t_val, list):
            valid_t = [str(t).strip() for t in t_val if t and str(t).upper() not in ["ALL", "SEMUA", "SEMUA JENIS MTM"]]
            if valid_t:
                parts.append(f"MTM = {', '.join(valid_t)}")
        else:
            t_str = str(t_val).strip()
            if t_str and t_str.upper() not in ["ALL", "SEMUA", "SEMUA JENIS MTM"]:
                parts.append(f"MTM = {t_str}")

    # 3. Branch
    b_val = filters.get("branches") or filters.get("branch")
    if b_val:
        if isinstance(b_val, list):
            valid_b = [str(b).strip() for b in b_val if b and str(b).upper() not in ["ALL", "SEMUA", "SEMUA CABANG"]]
            if valid_b:
                if len(valid_b) == 1:
                    parts.append(f"Cabang = {valid_b[0]}")
                else:
                    parts.append(f"Cabang = {len(valid_b)} Terpilih")
        else:
            b_str = str(b_val).strip()
            if b_str and b_str.upper() not in ["ALL", "SEMUA", "SEMUA CABANG"]:
                parts.append(f"Cabang = {b_str}")

    # 4. MTM Alias
    a_val = filters.get("mtm_aliases") or filters.get("mtm_alias")
    if a_val:
        if isinstance(a_val, list):
            valid_a = [str(a).strip() for a in a_val if a and str(a).upper() not in ["ALL", "SEMUA", "SEMUA ALIAS"]]
            if valid_a:
                if len(valid_a) == 1:
                    parts.append(f"MTM Alias = {valid_a[0]}")
                else:
                    parts.append(f"MTM Alias = {len(valid_a)} Terpilih")
        else:
            a_str = str(a_val).strip()
            if a_str and a_str.upper() not in ["ALL", "SEMUA", "SEMUA ALIAS"]:
                parts.append(f"MTM Alias = {a_str}")

    # 5. Brand Group
    bg_val = filters.get("brand_groups") or filters.get("brand_group")
    if bg_val:
        if isinstance(bg_val, list):
            valid_bg = [str(bg).strip() for bg in bg_val if bg and str(bg).upper() not in ["ALL", "SEMUA", "SEMUA GRUP BRAND"]]
            if valid_bg:
                if len(valid_bg) == 1:
                    parts.append(f"Brand = {valid_bg[0]}")
                else:
                    parts.append(f"Brand = {len(valid_bg)} Terpilih")
        else:
            bg_str = str(bg_val).strip()
            if bg_str and bg_str.upper() not in ["ALL", "SEMUA", "SEMUA GRUP BRAND"]:
                parts.append(f"Brand = {bg_str}")

    # 6. Item
    i_val = filters.get("items") or filters.get("item")
    if i_val:
        if isinstance(i_val, list):
            valid_i = [str(i).strip() for i in i_val if i and str(i).upper() not in ["ALL", "SEMUA", "SEMUA PRODUK / ITEM"]]
            if valid_i:
                if len(valid_i) == 1:
                    parts.append(f"Item = {valid_i[0]}")
                else:
                    parts.append(f"Item = {len(valid_i)} Terpilih")
        else:
            i_str = str(i_val).strip()
            if i_str and i_str.upper() not in ["ALL", "SEMUA", "SEMUA PRODUK / ITEM"]:
                parts.append(f"Item = {i_str}")

    # 7. Reason
    r_val = filters.get("reasons") or filters.get("reason")
    if r_val:
        if isinstance(r_val, list):
            valid_r = [str(r).strip() for r in r_val if r and str(r).upper() not in ["ALL", "SEMUA", "SEMUA ALASAN"]]
            if valid_r:
                if len(valid_r) == 1:
                    parts.append(f"Alasan = {valid_r[0]}")
                else:
                    parts.append(f"Alasan = {len(valid_r)} Terpilih")
        else:
            r_str = str(r_val).strip()
            if r_str and r_str.upper() not in ["ALL", "SEMUA", "SEMUA ALASAN"]:
                parts.append(f"Alasan = {r_str}")

    return "📌 Filter Aktif: " + " | ".join(parts)


class MTMPPTExporter:
    def __init__(self, template_path: str = "Template PPT.pptx"):
        self.template_path = template_path

    def generate_presentation(self, export_data: Dict[str, Any], output_path: str = "output_report.pptx") -> str:
        """
        Generate PowerPoint presentation based on Template PPT.pptx with complete slide data population matching dashboard filters.
        """
        if HAS_PYTHON_PPTX and os.path.exists(self.template_path):
            return self._generate_with_python_pptx(export_data, output_path)
        else:
            return self._generate_fallback(export_data, output_path)

    def _generate_with_python_pptx(self, export_data: Dict[str, Any], output_path: str) -> str:
        prs = Presentation(self.template_path)

        # Clean up pre-existing extra template slides beyond Slide 0 and Slide 1
        while len(prs.slides) > 2:
            rId = prs.slides._sldIdLst[2].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[2]

        filters = export_data.get("filters", {})
        kpi = export_data.get("kpi", {})
        pareto = export_data.get("pareto", {})
        grid = export_data.get("grid", [])
        modules = export_data.get("selected_modules", {})

        sel_month = filters.get("month", "2026-08")
        sel_mtm = filters.get("mtm_type", "KA")
        month_label = format_month_label(sel_month)

        filter_info = build_active_filters_summary(filters)

        content_layout = prs.slide_layouts[9] if len(prs.slide_layouts) > 9 else prs.slide_layouts[0]

        # Slide 0: Cover Slide Title & Subtitle Population Inside Template Dashed Boxes
        if len(prs.slides) > 0:
            cover_slide = prs.slides[0]

            # Populate Top Dashed Box (Placeholder 0)
            if len(cover_slide.placeholders) > 0:
                ph0 = cover_slide.placeholders[0]
                tf0 = ph0.text_frame
                tf0.word_wrap = True
                p0 = tf0.paragraphs[0]
                p0.text = "LAPORAN EXECUTIVE SERVICE LEVEL MTM"
                p0.font.size = Pt(20)
                p0.font.bold = True
                p0.font.color.rgb = RGBColor(255, 255, 255)
                
                p1 = tf0.add_paragraph()
                p1.text = "Analisis Performa Pengiriman, Realisasi, dan Pareto Unfulfill"
                p1.font.size = Pt(12)
                p1.font.color.rgb = RGBColor(255, 215, 0)

            # Populate Bottom Dashed Box (Placeholder 1)
            if len(cover_slide.placeholders) > 1:
                ph1 = cover_slide.placeholders[1]
                tf1 = ph1.text_frame
                tf1.word_wrap = True
                p2 = tf1.paragraphs[0]
                p2.text = filter_info.replace("📌 Filter Aktif: ", "PERIODE FILTER: ")
                p2.font.size = Pt(9.5)
                p2.font.bold = True
                p2.font.color.rgb = RGBColor(255, 255, 255)
            else:
                # Fallback if placeholder 1 is missing
                cov_box = cover_slide.shapes.add_textbox(Inches(4.87), Inches(1.58), Inches(4.79), Inches(1.48))
                tf_cov = cov_box.text_frame
                tf_cov.word_wrap = True
                p0 = tf_cov.paragraphs[0]
                p0.text = "LAPORAN EXECUTIVE SERVICE LEVEL MTM"
                p0.font.size = Pt(20)
                p0.font.bold = True
                p0.font.color.rgb = RGBColor(255, 255, 255)
                p1 = tf_cov.add_paragraph()
                p1.text = "Analisis Performa Pengiriman, Realisasi, dan Pareto Unfulfill"
                p1.font.size = Pt(12)
                p1.font.color.rgb = RGBColor(255, 215, 0)

        # Slide 1 (prs.slides[1]): Executive KPI Summary & Monthly Performance Trend Table
        if modules.get("kpi_summary", True) and len(prs.slides) > 1:
            slide_kpi = prs.slides[1]

            # Clear default title text
            for shape in list(slide_kpi.shapes):
                if shape.has_text_frame and shape.text_frame.text in ["Title 4", "Click to add title"]:
                    shape.text_frame.text = ""

            title_box = slide_kpi.shapes.add_textbox(Inches(0.55), Inches(0.45), Inches(8.8), Inches(0.60))
            tf = title_box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = f"1. EXECUTIVE KPI SUMMARY & TREND ({month_label})"
            p.font.size = Pt(17)
            p.font.bold = True
            p.font.color.rgb = RGBColor(192, 0, 0)

            p_sub = tf.add_paragraph()
            p_sub.text = filter_info
            p_sub.font.size = Pt(8.5)
            p_sub.font.bold = True
            p_sub.font.color.rgb = RGBColor(100, 100, 100)

            # KPI Metric Cards (3 Cards)
            card_w = Inches(2.75)
            card_h = Inches(0.95)
            gap_w = Inches(0.28)

            metrics = [
                ("SERVICE LEVEL KIRIM", f"{kpi.get('sl_kirim', 0):.1f}%", "Target Acuan: 85.0%"),
                ("SERVICE LEVEL REALISASI", f"{kpi.get('sl_realisasi', 0):.1f}%", "Target Acuan: 85.0%"),
                ("GAP REALISASI VS KIRIM", f"{kpi.get('gap', 0):+.1f}%", "Selisih Performa")
            ]

            for i, (title, val, sub) in enumerate(metrics):
                left = Inches(0.55) + i * (card_w + gap_w)
                top = Inches(1.15)

                shape = slide_kpi.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, card_w, card_h)
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor(248, 249, 250)
                shape.line.color.rgb = RGBColor(192, 0, 0)

                tf_card = shape.text_frame
                tf_card.word_wrap = True

                p0 = tf_card.paragraphs[0]
                p0.text = title
                p0.font.size = Pt(9)
                p0.font.bold = True
                p0.font.color.rgb = RGBColor(100, 100, 100)
                p0.alignment = PP_ALIGN.CENTER

                p1 = tf_card.add_paragraph()
                p1.text = val
                p1.font.size = Pt(19)
                p1.font.bold = True
                p1.font.color.rgb = RGBColor(192, 0, 0) if "GAP" not in title else (RGBColor(34, 197, 94) if kpi.get('gap', 0) >= 0 else RGBColor(239, 68, 68))
                p1.alignment = PP_ALIGN.CENTER

                p2 = tf_card.add_paragraph()
                p2.text = sub
                p2.font.size = Pt(7.5)
                p2.font.color.rgb = RGBColor(120, 120, 120)
                p2.alignment = PP_ALIGN.CENTER

            # Monthly Performance Trend Bar Chart (Grafik Batang / Column Clustered MTM Dashboard Style)
            trend_data = export_data.get("trend", [])
            if trend_data:
                chart_data = CategoryChartData()
                chart_data.categories = [format_month_label(r.get("month", "")) for r in trend_data]
                chart_data.add_series('SL Kirim (%)', [round(float(r.get('sl_kirim', 0)), 1) for r in trend_data])
                chart_data.add_series('SL Realisasi (%)', [round(float(r.get('sl_realisasi', 0)), 1) for r in trend_data])

                x, y, cx, cy = Inches(0.55), Inches(2.18), Inches(8.8), Inches(2.55)
                chart_shape = slide_kpi.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data)
                chart = chart_shape.chart

                chart.has_legend = True
                chart.legend.position = XL_LEGEND_POSITION.TOP
                chart.legend.include_in_layout = False
                chart.legend.font.size = Pt(8.5)

                plot = chart.plots[0]
                plot.has_data_labels = True
                data_labels = plot.data_labels
                data_labels.font.size = Pt(7.5)
                data_labels.font.bold = True

                # Format Value & Category Axes cleanly
                val_axis = chart.value_axis
                val_axis.maximum_scale = 100
                val_axis.minimum_scale = 0
                val_axis.major_unit = 20
                val_axis.tick_labels.font.size = Pt(8)

                cat_axis = chart.category_axis
                cat_axis.tick_labels.font.size = Pt(8)

                # Style Series Fills (High Contrast Color Distinction)
                # Series 0: SL Kirim (Konimex Primary Red)
                if len(chart.series) > 0:
                    series0 = chart.series[0]
                    series0.format.fill.solid()
                    series0.format.fill.fore_color.rgb = RGBColor(192, 0, 0)

                # Series 1: SL Realisasi (Royal Blue - High Contrast Distinction)
                if len(chart.series) > 1:
                    series1 = chart.series[1]
                    series1.format.fill.solid()
                    series1.format.fill.fore_color.rgb = RGBColor(37, 99, 235)

        # Slide 2+: Dedicated Pareto & Vital Detail Grid Slides Per Dimension
        if modules.get("pareto_sheets", True) or modules.get("detail_grid", True):
            pareto_data = export_data.get("pareto", {})
            grid_by_dim = export_data.get("grid_by_dim", {})

            dimensions_cfg = [
                ("alasan", "ALASAN KETERLAMBATAN"),
                ("mtm_alias", "AKUN MTM ALIAS"),
                ("cabang", "NAMA CABANG"),
                ("grup_brand", "GRUP BRAND"),
                ("item", "ITEM / PRODUK SKU")
            ]

            section_idx = 2
            for dim_key, dim_label in dimensions_cfg:
                pareto_items = pareto_data.get(dim_key, [])
                if not pareto_items:
                    continue

                # Identify Vital Pareto 80% items
                vital_items = []
                for item in pareto_items:
                    prev_cum = float(item.get("cumulative_percentage", 0)) - float(item.get("percentage", 0))
                    if prev_cum < 80.0:
                        vital_items.append(item)
                vital_names = set([v.get("name") for v in vital_items if v.get("name")])

                # SLIDE A: PARETO ANALYSIS SLIDE FOR THIS DIMENSION
                slide_p = prs.slides.add_slide(content_layout)

                # Title in top dashed box (Top: 0.45", Left: 0.55", W: 8.8", H: 0.60")
                title_box_p = slide_p.shapes.add_textbox(Inches(0.55), Inches(0.45), Inches(8.8), Inches(0.60))
                tf_p = title_box_p.text_frame
                tf_p.word_wrap = True
                p_p = tf_p.paragraphs[0]
                p_p.text = f"{section_idx}.1 ANALISIS PARETO UNFULLFILL - {dim_label} ({month_label})"
                p_p.font.size = Pt(16)
                p_p.font.bold = True
                p_p.font.color.rgb = RGBColor(192, 0, 0)

                p_sub_p = tf_p.add_paragraph()
                p_sub_p.text = filter_info
                p_sub_p.font.size = Pt(8.5)
                p_sub_p.font.bold = True
                p_sub_p.font.color.rgb = RGBColor(100, 100, 100)

                # Pareto Table for this dimension (display up to 9 rows)
                rows_p_cnt = min(10, len(pareto_items) + 1)
                p_table = slide_p.shapes.add_table(rows_p_cnt, 6, Inches(0.55), Inches(1.15), Inches(8.8), Inches(3.8)).table

                p_col_widths = [Inches(0.6), Inches(3.2), Inches(1.5), Inches(1.1), Inches(1.1), Inches(1.3)]
                for c_i, w in enumerate(p_col_widths):
                    p_table.columns[c_i].width = w

                headers_p = ["No", "Nama Elemen / Kategori", "Nilai Unfulfilled", "Kontribusi (%)", "Kumulatif (%)", "Status Pareto"]
                for c, h in enumerate(headers_p):
                    cell = p_table.cell(0, c)
                    cell.text = h
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                    for p in cell.text_frame.paragraphs:
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.font.size = Pt(8.5)
                        p.alignment = PP_ALIGN.CENTER

                for r, item in enumerate(pareto_items[:9]):
                    r_idx = r + 1
                    val_num = float(item.get("value", 0))
                    val_str = f"Rp {val_num:,.0f}" if val_num >= 1000 else f"{val_num:,.0f} unit"
                    pct = float(item.get("percentage", 0))
                    cum_pct = float(item.get("cumulative_percentage", 0))
                    
                    prev_cum = cum_pct - pct
                    is_vital = (prev_cum < 80.0)
                    status_str = "⭐ Vital 80%" if is_vital else "Trivial 20%"

                    vals = [
                        str(r_idx),
                        str(item.get("name", "-")),
                        val_str,
                        f"{pct:.1f}%",
                        f"{cum_pct:.1f}%",
                        status_str
                    ]

                    for c, v in enumerate(vals):
                        cell = p_table.cell(r_idx, c)
                        cell.text = v
                        if is_vital:
                            cell.fill.solid()
                            cell.fill.fore_color.rgb = RGBColor(254, 242, 242)

                        for p in cell.text_frame.paragraphs:
                            p.font.size = Pt(8)
                            if is_vital:
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(192, 0, 0)
                            if c in [2, 3, 4]:
                                p.alignment = PP_ALIGN.RIGHT
                            elif c in [0, 5]:
                                p.alignment = PP_ALIGN.CENTER

                # SLIDE B: DETAIL DATA GRID TABLE SLIDE FOR THIS DIMENSION (VITAL PARETO ONLY)
                grid_dim = grid_by_dim.get(dim_key, [])
                if not grid_dim and export_data.get("grid"):
                    grid_dim = export_data.get("grid", [])

                if vital_names:
                    vital_grid = [g for g in grid_dim if g.get("name") in vital_names]
                    if not vital_grid:
                        vital_grid = grid_dim[:5]
                else:
                    vital_grid = grid_dim[:5]

                if vital_grid:
                    slide_g = prs.slides.add_slide(content_layout)

                    # Title in top dashed box (Top: 0.45", Left: 0.55", W: 8.8", H: 0.60")
                    title_box_g = slide_g.shapes.add_textbox(Inches(0.55), Inches(0.45), Inches(8.8), Inches(0.60))
                    tf_g = title_box_g.text_frame
                    tf_g.word_wrap = True
                    p_g = tf_g.paragraphs[0]
                    p_g.text = f"{section_idx}.2 TABEL DETAIL TRANSAKSI - VITAL PARETO {dim_label} ({month_label})"
                    p_g.font.size = Pt(15)
                    p_g.font.bold = True
                    p_g.font.color.rgb = RGBColor(192, 0, 0)

                    p_sub_g = tf_g.add_paragraph()
                    p_sub_g.text = f"{filter_info} | Filter Vital Pareto 80%"
                    p_sub_g.font.size = Pt(8.5)
                    p_sub_g.font.bold = True
                    p_sub_g.font.color.rgb = RGBColor(100, 100, 100)

                    rows_g_cnt = min(11, len(vital_grid) + 1)
                    g_table = slide_g.shapes.add_table(rows_g_cnt, 8, Inches(0.55), Inches(1.15), Inches(8.8), Inches(3.8)).table

                    g_col_widths = [Inches(0.5), Inches(2.3), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.1), Inches(0.8), Inches(0.8)]
                    for c_i, w in enumerate(g_col_widths):
                        g_table.columns[c_i].width = w

                    headers_g = ["#", "Nama Elemen (Vital 80%)", "Total Order", "Total Kirim", "Total Realisasi", "Nilai Unfulfill", "SL Kirim", "SL Realisasi"]
                    for c, h in enumerate(headers_g):
                        cell = g_table.cell(0, c)
                        cell.text = h
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                        for p in cell.text_frame.paragraphs:
                            p.font.bold = True
                            p.font.color.rgb = RGBColor(255, 255, 255)
                            p.font.size = Pt(8)
                            p.alignment = PP_ALIGN.CENTER

                    for r, row_data in enumerate(vital_grid[:10]):
                        r_idx = r + 1
                        sl_k_val = float(row_data.get("sl_kirim", 0))
                        sl_r_val = float(row_data.get("sl_realisasi", 0))
                        
                        tp_val = row_data.get('total_p', row_data.get('total_pesan', 0))
                        tk_val = row_data.get('total_k', row_data.get('total_kirim', 0))
                        tr_val = row_data.get('total_r', row_data.get('total_realisasi', 0))
                        gap_val = row_data.get('gap_unfulfill', 0)

                        vals = [
                            str(r_idx),
                            str(row_data.get("name", "")),
                            f"{tp_val:,.0f}",
                            f"{tk_val:,.0f}",
                            f"{tr_val:,.0f}",
                            f"{gap_val:,.0f}",
                            f"{sl_k_val:.1f}%",
                            f"{sl_r_val:.1f}%"
                        ]
                        for c, v in enumerate(vals):
                            cell = g_table.cell(r_idx, c)
                            cell.text = v
                            for p in cell.text_frame.paragraphs:
                                p.font.size = Pt(8)
                                if c in [2, 3, 4, 5]:
                                    p.alignment = PP_ALIGN.RIGHT
                                elif c in [0, 6, 7]:
                                    p.alignment = PP_ALIGN.CENTER

                section_idx += 1

        prs.save(output_path)
        print(f"Presentation saved successfully to {output_path}")
        return output_path

    def _generate_fallback(self, export_data: Dict[str, Any], output_path: str) -> str:
        """Fallback copy of Template PPT.pptx if pptx library is not loaded."""
        if os.path.exists(self.template_path):
            with open(self.template_path, 'rb') as f_in:
                content = f_in.read()
            with open(output_path, 'wb') as f_out:
                f_out.write(content)
            print(f"Fallback PPT exported to {output_path}")
            return output_path
        else:
            raise FileNotFoundError("Template PPT.pptx not found!")
