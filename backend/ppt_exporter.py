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


class MTMPPTExporter:
    def __init__(self, template_path: str = "Template PPT.pptx"):
        self.template_path = template_path

    def generate_presentation(self, export_data: Dict[str, Any], output_path: str = "output_report.pptx") -> str:
        """
        Generate PowerPoint presentation based on Template PPT.pptx with Layout Safeguard.
        
        export_data structure:
        {
            "kpi": {"sl_kirim": 88.5, "sl_realisasi": 84.2, "gap": -4.3, "target": 85.0},
            "trend": [...],
            "pareto": {
                "alasan": [...],
                "mtm_alias": [...],
                "cabang": [...],
                "grup_brand": [...],
                "item": [...]
            },
            "grid": [...],
            "selected_modules": {
                "kpi_summary": True,
                "pareto_sheets": True,
                "detail_grid": True
            }
        }
        """
        if HAS_PYTHON_PPTX and os.path.exists(self.template_path):
            return self._generate_with_python_pptx(export_data, output_path)
        else:
            return self._generate_fallback(export_data, output_path)

    def _generate_with_python_pptx(self, export_data: Dict[str, Any], output_path: str) -> str:
        prs = Presentation(self.template_path)
        blank_slide_layout = prs.slide_layouts[0] if prs.slide_layouts else prs.slide_layouts[0]

        kpi = export_data.get("kpi", {})
        pareto = export_data.get("pareto", {})
        grid = export_data.get("grid", [])
        modules = export_data.get("selected_modules", {})

        # Slide 1: Executive KPI & Trend Summary
        if modules.get("kpi_summary", True) and len(prs.slides) > 0:
            slide1 = prs.slides[0]
            
            # Title below header
            title_box = slide1.shapes.add_textbox(Inches(0.6), Inches(1.3), Inches(8.8), Inches(0.5))
            tf = title_box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = "EXECUTIVE KPI SERVICE LEVEL SUMMARY"
            p.font.size = Pt(20)
            p.font.bold = True
            p.font.color.rgb = RGBColor(192, 0, 0) # Merah Konimex

            # KPI Metric Cards (Safeguard bounding box: Y=1.9", W=8.8")
            card_w = Inches(2.7)
            card_h = Inches(1.3)
            gap_w = Inches(0.35)

            metrics = [
                ("SERVICE LEVEL KIRIM", f"{kpi.get('sl_kirim', 0):.1f}%", "Target: 85.0%"),
                ("SERVICE LEVEL REALISASI", f"{kpi.get('sl_realisasi', 0):.1f}%", "Target: 85.0%"),
                ("GAP (REALISASI - KIRIM)", f"{kpi.get('gap', 0):+.1f}%", "Perbedaan Performa")
            ]

            for i, (title, val, sub) in enumerate(metrics):
                left = Inches(0.6) + i * (card_w + gap_w)
                top = Inches(2.0)
                
                # Shape Card Background
                shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, card_w, card_h)
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor(245, 245, 245)
                shape.line.color.rgb = RGBColor(200, 0, 0)

                tf_card = shape.text_frame
                tf_card.word_wrap = True
                
                p0 = tf_card.paragraphs[0]
                p0.text = title
                p0.font.size = Pt(11)
                p0.font.bold = True
                p0.font.color.rgb = RGBColor(100, 100, 100)
                p0.alignment = PP_ALIGN.CENTER
                
                p1 = tf_card.add_paragraph()
                p1.text = val
                p1.font.size = Pt(24)
                p1.font.bold = True
                p1.font.color.rgb = RGBColor(192, 0, 0)
                p1.alignment = PP_ALIGN.CENTER

                p2 = tf_card.add_paragraph()
                p2.text = sub
                p2.font.size = Pt(9)
                p2.font.color.rgb = RGBColor(120, 120, 120)
                p2.alignment = PP_ALIGN.CENTER

            # Monthly Trend Table
            trend_data = export_data.get("trend", [])
            if trend_data:
                table_shape = slide1.shapes.add_table(min(6, len(trend_data) + 1), 4, Inches(0.6), Inches(3.6), Inches(8.8), Inches(1.5))
                table = table_shape.table
                
                # Headers
                headers = ["Bulan", "SL Kirim (%)", "SL Realisasi (%)", "Target (%)"]
                for c, h in enumerate(headers):
                    cell = table.cell(0, c)
                    cell.text = h
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                    for p in cell.text_frame.paragraphs:
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.font.size = Pt(10)

                for r, row_data in enumerate(trend_data[:5]):
                    r_idx = r + 1
                    vals = [str(row_data.get("month", "")), f"{row_data.get('sl_kirim', 0):.1f}%", f"{row_data.get('sl_realisasi', 0):.1f}%", "85.0%"]
                    for c, v in enumerate(vals):
                        cell = table.cell(r_idx, c)
                        cell.text = v
                        for p in cell.text_frame.paragraphs:
                            p.font.size = Pt(9)

        # Slide 2: Pareto Multi-Dimension Summary
        if modules.get("pareto_sheets", True) and len(prs.slides) > 1:
            slide2 = prs.slides[1]
            title_box2 = slide2.shapes.add_textbox(Inches(0.6), Inches(1.3), Inches(8.8), Inches(0.5))
            tf2 = title_box2.text_frame
            p = tf2.paragraphs[0]
            p.text = "ANALISIS PARETO MULTI-DIMENSI (DESCENDING CONTRIBUTION)"
            p.font.size = Pt(18)
            p.font.bold = True
            p.font.color.rgb = RGBColor(192, 0, 0)

            # Pareto Summary Table for 5 dimensions
            dims = [("Alasan", pareto.get("alasan", [])), 
                    ("MTM Alias", pareto.get("mtm_alias", [])), 
                    ("Cabang", pareto.get("cabang", [])), 
                    ("Grup Brand", pareto.get("grup_brand", [])), 
                    ("Item", pareto.get("item", []))]

            p_table = slide2.shapes.add_table(6, 4, Inches(0.6), Inches(2.0), Inches(8.8), Inches(2.8)).table
            p_table.cell(0, 0).text = "Dimensi Sheet"
            p_table.cell(0, 1).text = "Elemen Kontribusi Terbesar"
            p_table.cell(0, 2).text = "Nilai Contrib (IDR/Qty)"
            p_table.cell(0, 3).text = "Kumulatif Pareto (%)"

            for c in range(4):
                cell = p_table.cell(0, c)
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                for p in cell.text_frame.paragraphs:
                    p.font.bold = True
                    p.font.color.rgb = RGBColor(255, 255, 255)
                    p.font.size = Pt(10)

            for idx, (dim_name, items) in enumerate(dims):
                row_i = idx + 1
                top_item = items[0] if items else {"name": "-", "value": 0, "cumulative_percentage": 0}
                p_table.cell(row_i, 0).text = dim_name
                p_table.cell(row_i, 1).text = str(top_item.get("name", "-"))
                p_table.cell(row_i, 2).text = f"{top_item.get('value', 0):,.0f}"
                p_table.cell(row_i, 3).text = f"{top_item.get('cumulative_percentage', 0):.1f}%"

        # Slide 3: Detail Data Grid
        if modules.get("detail_grid", True) and len(prs.slides) > 2:
            slide3 = prs.slides[2]
            title_box3 = slide3.shapes.add_textbox(Inches(0.6), Inches(1.3), Inches(8.8), Inches(0.5))
            p3 = title_box3.text_frame.paragraphs[0]
            p3.text = "TABEL DETAIL DATA ANALISIS TRANSACTION"
            p3.font.size = Pt(18)
            p3.font.bold = True
            p3.font.color.rgb = RGBColor(192, 0, 0)

            if grid:
                g_table = slide3.shapes.add_table(min(8, len(grid) + 1), 6, Inches(0.6), Inches(2.0), Inches(8.8), Inches(3.0)).table
                g_headers = ["Bulan", "Cabang", "Group Brand", "Item", "IDR Kirim", "Alasan"]
                for c, h in enumerate(g_headers):
                    cell = g_table.cell(0, c)
                    cell.text = h
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(192, 0, 0)
                    for p in cell.text_frame.paragraphs:
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.font.size = Pt(9)

                for r, row in enumerate(grid[:7]):
                    r_idx = r + 1
                    vals = [
                        str(row.get("month", "")),
                        str(row.get("branch", "")),
                        str(row.get("brand_group", "")),
                        str(row.get("item_name", "")),
                        f"{row.get('idr_kirim', 0):,.0f}",
                        str(row.get("reason_final", ""))
                    ]
                    for c, v in enumerate(vals):
                        cell = g_table.cell(r_idx, c)
                        cell.text = v
                        for p in cell.text_frame.paragraphs:
                            p.font.size = Pt(8)

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
