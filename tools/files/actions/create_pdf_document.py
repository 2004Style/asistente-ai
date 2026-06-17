"""
Creates a PDF document from text/markdown content.
"""
import os
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.web.actions.download_media import resolve_directory

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

logger = logging.getLogger("CreatePDFDocumentTool")

class CreatePDFDocumentInput(BaseModel):
    title: str = Field(..., description="The title of the PDF document.")
    content: str = Field(..., description="The content of the document (supports markdown-style headings #, ##, ###).")
    output_dir: Optional[str] = Field(None, description="The folder to save the PDF in (e.g., 'documentos', 'descargas', or a full path).")
    filename: str = Field(..., description="The filename for the PDF document (e.g., 'reporte_tecnologia.pdf').")

class CreatePDFDocumentTool(BaseTool):
    manifest = ToolManifest(
        name="create_pdf_document",
        description="Creates a PDF document with formatted headings and paragraphs from text/markdown content.",
        arguments_schema=CreatePDFDocumentInput,
        permission_level="low",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        title = kwargs.get("title")
        content = kwargs.get("content")
        output_dir_str = kwargs.get("output_dir")
        filename = kwargs.get("filename")
        
        if not title or not content or not filename:
            return {"error": "Missing parameters: title, content, and filename are required."}
            
        # Ensure filename ends with .pdf
        if not filename.endswith(".pdf"):
            filename += ".pdf"
            
        output_dir = resolve_directory(output_dir_str, default_type="downloads")
        file_path = output_dir / filename
        
        try:
            logger.info(f"Generating PDF document: {file_path}")
            
            # Setup document template
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=letter,
                rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=24,
                leading=28,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor='#1A365D' # Navy blue
            )
            
            h1_style = ParagraphStyle(
                'H1Style',
                parent=styles['Heading2'],
                fontSize=16,
                leading=20,
                spaceBefore=14,
                spaceAfter=6,
                textColor='#2B6CB0' # Soft blue
            )
            
            h2_style = ParagraphStyle(
                'H2Style',
                parent=styles['Heading3'],
                fontSize=13,
                leading=16,
                spaceBefore=10,
                spaceAfter=4,
                textColor='#2D3748'
            )
            
            body_style = ParagraphStyle(
                'BodyStyle',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT,
                spaceAfter=8,
                textColor='#2D3748'
            )
            
            story = []
            
            # Document Title
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 10))
            
            # Parse markdown-like content line by line
            lines = content.split("\n")
            current_paragraph_lines = []
            
            def flush_paragraph():
                nonlocal current_paragraph_lines
                if current_paragraph_lines:
                    p_text = " ".join(current_paragraph_lines).strip()
                    if p_text:
                        story.append(Paragraph(p_text, body_style))
                    current_paragraph_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    flush_paragraph()
                    continue
                    
                # Headings
                if line_stripped.startswith("# "):
                    flush_paragraph()
                    story.append(Paragraph(line_stripped[2:], h1_style))
                elif line_stripped.startswith("## "):
                    flush_paragraph()
                    story.append(Paragraph(line_stripped[3:], h2_style))
                elif line_stripped.startswith("### "):
                    flush_paragraph()
                    story.append(Paragraph(line_stripped[4:], h2_style))
                else:
                    current_paragraph_lines.append(line_stripped)
                    
            # Flush any remaining paragraph
            flush_paragraph()
            
            # Build the document
            doc.build(story)
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "filename": filename,
                "output_dir": str(output_dir),
                "message": f"Documento PDF creado correctamente en: {file_path}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create PDF document: {e}")
            return {"error": f"Failed to create PDF document: {str(e)}"}
