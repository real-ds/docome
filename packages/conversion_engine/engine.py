import io
from pathlib import Path
from typing import List, Optional, Union

import pymupdf
from docx import Document
from docx.shared import Inches, Pt
from PIL import Image


class ConversionEngine:
    def __init__(self):
        pass

    def docx_to_pdf(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        if isinstance(input_path, bytes):
            doc = Document(io.BytesIO(input_path))
        else:
            doc = Document(input_path)

        pdf_doc = pymupdf.open()

        for para in doc.paragraphs:
            if para.text.strip():
                page = pdf_doc.new_page(width=595, height=842)
                
                text = para.text
                for run in para.runs:
                    pass

                page.insert_text((72, 72), text, fontsize=11)

        pdf_doc.save(output_path)
        pdf_doc.close()

    def pdf_to_docx(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        doc = Document()

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            text = page.get_text()
            if text.strip():
                for line in text.split("\n"):
                    if line.strip():
                        p = doc.add_paragraph(line)

            doc.add_page_break()

        doc.save(output_path)
        pdf_doc.close()

    def xlsx_to_pdf(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        if isinstance(input_path, bytes):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(input_path))
        else:
            import openpyxl
            wb = openpyxl.load_workbook(input_path)

        pdf_doc = pymupdf.open()

        for sheet in wb.sheetnames:
            ws = wb[sheet]
            
            page = pdf_doc.new_page(width=595, height=842)
            y_position = 50
            
            for row in ws.iter_rows(values_only=True):
                row_text = "  |  ".join([str(cell) if cell is not None else "" for cell in row])
                if row_text.strip():
                    page.insert_text((50, y_position), row_text, fontsize=9)
                    y_position += 15
                    
                    if y_position > 750:
                        page = pdf_doc.new_page(width=595, height=842)
                        y_position = 50

            if ws.sheetnames.index(sheet) < len(ws.sheetnames) - 1:
                pass

        pdf_doc.save(output_path)
        pdf_doc.close()

    def pdf_to_xlsx(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        import openpyxl
        from openpyxl import Workbook

        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        wb = Workbook()
        ws = wb.active
        ws.title = "Extracted"

        row_idx = 1
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            text = page.get_text()
            
            for line in text.split("\n"):
                if line.strip():
                    cells = line.split("\t")
                    for col_idx, cell in enumerate(cells, start=1):
                        ws.cell(row=row_idx, column=col_idx, value=cell.strip())
                    row_idx += 1

        wb.save(output_path)
        pdf_doc.close()

    def pptx_to_pdf(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        if isinstance(input_path, bytes):
            import pptx
            prs = pptx.Presentation(io.BytesIO(input_path))
        else:
            import pptx
            prs = pptx.Presentation(input_path)

        pdf_doc = pymupdf.open()

        for slide in prs.slides:
            page = pdf_doc.new_page(width=595, height=842)
            y_position = 50
            
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    page.insert_text((50, y_position), shape.text, fontsize=11)
                    y_position += 15

        pdf_doc.save(output_path)
        pdf_doc.close()

    def pdf_to_pptx(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        from pptx import Presentation
        from pptx.util import Inches, Pt

        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        prs = Presentation()

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            text = page.get_text()
            
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            
            if text.strip():
                text_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(5))
                tf = text_box.text_frame
                tf.text = text

        prs.save(output_path)
        pdf_doc.close()

    def html_to_pdf(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError("weasyprint is required for HTML to PDF conversion. Install with: pip install weasyprint")

        if isinstance(input_path, bytes):
            html_content = input_path.decode("utf-8")
        elif Path(input_path).suffix.lower() in [".html", ".htm"]:
            html_content = Path(input_path).read_text(encoding="utf-8")
        else:
            html_content = str(input_path)

        HTML(string=html_content).write_pdf(output_path)

    def pdf_to_text(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        text_parts = []
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            text = page.get_text()
            text_parts.append(text)

        full_text = "\n\n--- Page Break ---\n\n".join(text_parts)

        pdf_doc.close()

        if output_path:
            Path(output_path).write_text(full_text, encoding="utf-8")

        return full_text

    def pdf_to_markdown(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        md_parts = []
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            md_parts.append(f"## Page {page_num + 1}\n")
            
            text = page.get_text()
            blocks = page.get_text("dict")
            
            for block in blocks.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            text_content = span.get("text", "")
                            if span.get("flags", 0) & 2:
                                line_text += f"**{text_content}**"
                            elif span.get("flags", 0) & 1:
                                line_text += f"*{text_content}*"
                            else:
                                line_text += text_content
                        
                        if line_text.strip():
                            md_parts.append(line_text)
                
                elif block.get("type") == 1:
                    md_parts.append("---")
            
            md_parts.append("")

        full_md = "\n".join(md_parts)
        pdf_doc.close()

        if output_path:
            Path(output_path).write_text(full_md, encoding="utf-8")

        return full_md
