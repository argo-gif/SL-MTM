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

        filters = export_data.get("filters", {})
        kpi = export_data.get("kpi", {})
        pareto = export_data.get("pareto", {})
        grid = export_data.get("grid", [])
        modules = export_data.get("selected_modules", {})

        sel_month = filters.get("month", "2026-08")
        sel_mtm = filters.get("mtm_type", "KA")
        sel_branch = filters.get("branch", "Semua Cabang")
        sel_brand = filters.get("brand_group", "Semua Grup Brand")
        month_label = format_month_label(sel_month)

        filter_info = f"📌 Filter Aktif: Bulan = {month_label} | MTM = {sel_mtm} | Cabang = {sel_branch} | Brand = {sel_brand}"

        content_layout = prs.slide_layouts[2] if len(prs.slide_layouts) > 2 else prs.slide_layouts[0]

        # Slide 0: Cover Slide Title & Subtitle Enhancement with Filter Month Identity
        if len(prs.slides) > 0:
            cover_slide = prs.slides[0]
            cov_box = cover_slide.shapes.add_textbox(Inches(0.8), Inches(3.8), Inches(8.5), Inches(1.5))
            tf_cov = cov_box.text_frame
            tf_cov.word_wrap = True
            
            p0 = tf_cov.paragraphs[0]
            p0.text = "LAPORAN EXECUTIVE SERVICE LEVEL MTM"
            p0.font.size = Pt(20)
            p0.font.bold = True
            p0.font.color.rgb = RGBColor(255, 255, 255)
            
            p1 = tf_cov.add_paragraph()
            p1.text = f"Analisis Performa Pengiriman, Realisasi, dan Pareto Unfulfill"
            p1.font.size = Pt(13)
            p1.font.color.rgb = RGBColor(255, 215, 0)

            p2 = tf_cov.add_paragraph()
            p2.text = f"PERIODE FILTER: {month_label} | JENIS MTM: {sel_mtm} | CABANG: {sel_branch}"
            p2.font.size = Pt(11)
            p2.font.bold = True
            p2.font.color.rgb = RGBColor(248, 250, 252)

        # Slide 1 (prs.slides[1]): Executive KPI Summary & Monthly Performance Trend Table
        if modules.get("kpi_summary", True) and len(prs.slides) > 1:
            slide_kpi = prs.slides[1]

            # Clear default title text
            for shape in list(slide_kpi.shapes):
                if shape.has_text_frame and shape.text_frame.text in ["Title 4", "Click to add title"]:
                    shape.text_frame.text = ""

            title_box = slide_kpi.shapes.add_textbox(Inches(0.6), Inches(1.0), Inches(8.8), Inches(0.6))
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
            card_w = Inches(2.7)
            card_h = Inches(1.15)
            gap_w = Inches(0.35)

            metrics = [
                ("SERVICE LEVEL KIRIM", f"{kpi.get('sl_kirim', 0):.1f}%", "Target Acuan: 85.0%"),
                ("SERVICE LEVEL REALISASI", f"{kpi.get('sl_realisasi', 0):.1f}%", "Target Acuan: 85.0%"),
                ("GAP REALISASI VS KIRIM", f"{kpi.get('gap', 0):+.1f}%", "Selisih Performa")
            ]

            for i, (title, val, sub) in enumerate(metrics):
                left = Inches(0.6) + i * (card_w + gap_w)
                top = Inches(1.7)

                shape = slide_kpi.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, card_w, card_h)
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor(248, 249, 250)
                shape.line.color.rgb = RGBColor(192, 0, 0)

                tf_card = shape.text_frame
                tf_card.word_wrap = True

                p0 = tf_card.paragraphs[0]
                p0.text = title
                p0.font.size = Pt(9.5)
                p0.font.bold = True
                p0.font.color.rgb = RGBColor(100, 100, 100)
                p0.alignment = PP_ALIGN.CENTER

                p1 = tf_card.add_paragraph()
                p1.text = val
                p1.font.size = Pt(21)
                p1.font.bold = True
                p1.font.color.rgb = RGBColor(192, 0, 0) if "GAP" not in title else (RGBColor(34, 197, 94) if kpi.get('gap', 0) >= 0 else RGBColor(239, 68, 68))
                p1.alignment = PP_ALIGN.CENTER

                p2 = tf_card.add_paragraph()
                p2.text = sub
                p2.font.size = Pt(8)
                p2.font.color.rgb = RGBColor(120, 120, 120)
                p2.alignment = PP_ALIGN.CENTER

            # Monthly Trend Table
            trend_data = export_data.get("trend", [])
            if trend_data:
                table_shape = slide_kpi.shapes.add_table(min(7, len(trend_data) + 1), 6, Inches(0.6), Inches(3.05), Inches(8.8), Inches(1.9))
                table = table_shape.table

                headers = ["Bulan", "Total Pesan", "Total Kirim", "Total Realisasi", "SL Kirim (%)", "SL Realisasi (%)"]
                for c, h in enumerate(headers):
                    cell = table.cell(0, c)
                    cell.text = h
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                    for p in cell.text_frame.paragraphs:
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.font.size = Pt(9)
                        p.alignment = PP_ALIGN.CENTER

                for r, row_data in enumerate(trend_data[:6]):
                    r_idx = r + 1
                    raw_m = str(row_data.get("month", ""))
                    m_formatted = format_month_label(raw_m)

                    vals = [
                        m_formatted,
                        f"{row_data.get('total_p', 0):,.0f}",
                        f"{row_data.get('total_k', 0):,.0f}",
                        f"{row_data.get('total_r', 0):,.0f}",
                        f"{row_data.get('sl_kirim', 0):.1f}%",
                        f"{row_data.get('sl_realisasi', 0):.1f}%"
                    ]
                    for c, v in enumerate(vals):
                        cell = table.cell(r_idx, c)
                        cell.text = v
                        # Highlight active filter month
                        is_active_month = (raw_m == sel_month or m_formatted == month_label)
                        if is_active_month:
                            cell.fill.solid()
                            cell.fill.fore_color.rgb = RGBColor(254, 242, 242) # Soft Red tint

                        for p in cell.text_frame.paragraphs:
                            p.font.size = Pt(8.5)
                            if is_active_month:
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(192, 0, 0)
                            if c >= 1:
                                p.alignment = PP_ALIGN.RIGHT
                            if c == 0:
                                p.alignment = PP_ALIGN.CENTER

        # Slide 2: Pareto Multi-Dimension Analysis Slide
        if modules.get("pareto_sheets", True):
            slide_pareto = prs.slides.add_slide(content_layout)

            title_box2 = slide_pareto.shapes.add_textbox(Inches(0.6), Inches(1.0), Inches(8.8), Inches(0.6))
            tf2 = title_box2.text_frame
            p = tf2.paragraphs[0]
            p.text = f"2. ANALISIS PARETO UNFULLFILL MULTI-DIMENSI ({month_label})"
            p.font.size = Pt(17)
            p.font.bold = True
            p.font.color.rgb = RGBColor(192, 0, 0)

            p_sub2 = tf2.add_paragraph()
            p_sub2.text = filter_info
            p_sub2.font.size = Pt(8.5)
            p_sub2.font.bold = True
            p_sub2.font.color.rgb = RGBColor(100, 100, 100)

            dims = [
                ("Alasan Keterlambatan", pareto.get("alasan", [])), 
                ("Akun MTM Alias", pareto.get("mtm_alias", [])), 
                ("Nama Cabang", pareto.get("cabang", [])), 
                ("Grup Brand", pareto.get("grup_brand", [])), 
                ("Item / Produk SKU", pareto.get("item", []))
            ]

            p_table = slide_pareto.shapes.add_table(6, 5, Inches(0.6), Inches(1.7), Inches(8.8), Inches(3.2)).table
            p_headers = ["Dimensi Sheet", "Akar Masalah / Elemen Terbesar", "Nilai Unfulfilled", "Kontribusi (%)", "Status Pareto"]
            for c, h in enumerate(p_headers):
                cell = p_table.cell(0, c)
                cell.text = h
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                for p in cell.text_frame.paragraphs:
                    p.font.bold = True
                    p.font.color.rgb = RGBColor(255, 255, 255)
                    p.font.size = Pt(9.5)
                    p.alignment = PP_ALIGN.CENTER

            for idx, (dim_name, items) in enumerate(dims):
                row_i = idx + 1
                top_item = items[0] if items else {"name": "-", "value": 0, "percentage": 0, "cumulative_percentage": 0}
                val_num = top_item.get('value', 0)
                val_str = f"Rp {val_num:,.0f}" if val_num >= 1000 else f"{val_num:,.0f} unit"

                p_table.cell(row_i, 0).text = dim_name
                p_table.cell(row_i, 1).text = str(top_item.get("name", "-"))
                p_table.cell(row_i, 2).text = val_str
                p_table.cell(row_i, 3).text = f"{top_item.get('percentage', 0):.1f}%"
                p_table.cell(row_i, 4).text = "⭐ Vital 80%" if top_item.get('cumulative_percentage', 0) <= 80 else "Minor"

                for c in range(5):
                    cell = p_table.cell(row_i, c)
                    for p in cell.text_frame.paragraphs:
                        p.font.size = Pt(8.5)
                        if c in [2, 3]:
                            p.alignment = PP_ALIGN.RIGHT
                        elif c in [0, 4]:
                            p.alignment = PP_ALIGN.CENTER

        # Slide 3: Detail Data Grid Table Slide
        if modules.get("detail_grid", True):
            slide_grid = prs.slides.add_slide(content_layout)

            title_box3 = slide_grid.shapes.add_textbox(Inches(0.6), Inches(1.0), Inches(8.8), Inches(0.6))
            tf3 = title_box3.text_frame
            p3 = tf3.paragraphs[0]
            p3.text = f"3. TABEL DETAIL DATA ANALISIS TRANSACTION ({month_label})"
            p3.font.size = Pt(17)
            p3.font.bold = True
            p3.font.color.rgb = RGBColor(192, 0, 0)

            p_sub3 = tf3.add_paragraph()
            p_sub3.text = filter_info
            p_sub3.font.size = Pt(8.5)
            p_sub3.font.bold = True
            p_sub3.font.color.rgb = RGBColor(100, 100, 100)

            if grid:
                g_table = slide_grid.shapes.add_table(min(11, len(grid) + 1), 8, Inches(0.6), Inches(1.7), Inches(8.8), Inches(3.3)).table
                g_headers = ["#", "Nama Dimensi", "Total Order", "Total Kirim", "Total Realisasi", "Gap Selisih", "SL Kirim", "SL Realisasi"]
                for c, h in enumerate(g_headers):
                    cell = g_table.cell(0, c)
                    cell.text = h
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                    for p in cell.text_frame.paragraphs:
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.font.size = Pt(8.5)
                        p.alignment = PP_ALIGN.CENTER

                for r, row in enumerate(grid[:10]):
                    r_idx = r + 1
                    vals = [
                        str(r_idx),
                        str(row.get("name", "")),
                        f"{row.get('total_pesan', 0):,.0f}",
                        f"{row.get('total_kirim', 0):,.0f}",
                        f"{row.get('total_realisasi', 0):,.0f}",
                        f"{row.get('gap_unfulfill', 0):,.0f}",
                        f"{row.get('sl_kirim', 0):.1f}%",
                        f"{row.get('sl_realisasi', 0):.1f}%"
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
