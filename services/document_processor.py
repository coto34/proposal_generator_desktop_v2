import os
from pathlib import Path
from typing import Optional
import pypdf
from docx import Document
from pdfminer.high_level import extract_text
from docxtpl import DocxTemplate
import openpyxl
from openpyxl.styles import Font, Alignment
import json

class DocumentProcessor:
    """Handles document processing for ToR extraction and template generation"""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> Optional[str]:
        """Extract text from PDF or DOCX file"""
        if not file_path or not os.path.exists(file_path):
            return None
            
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.pdf':
                return DocumentProcessor._extract_from_pdf(file_path)
            elif extension == '.docx':
                return DocumentProcessor._extract_from_docx(file_path)
            else:
                return f"Formato de archivo no soportado: {extension}"
        except Exception as e:
            return f"Error al procesar archivo: {str(e)}"
    
    @staticmethod
    def _extract_from_pdf(file_path: Path) -> str:
        """Extract text from PDF using pdfminer"""
        try:
            # First try with pdfminer
            text = extract_text(str(file_path))
            if text.strip():
                return text.strip()
        except:
            pass
        
        try:
            # Fallback to pypdf
            reader = pypdf.PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error al extraer texto del PDF: {str(e)}"
    
    @staticmethod
    def _extract_from_docx(file_path: Path) -> str:
        """Extract text from DOCX"""
        try:
            doc = Document(str(file_path))
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text.strip())
            return "\n".join(text)
        except Exception as e:
            return f"Error al extraer texto del DOCX: {str(e)}"
    
    @staticmethod
    def generate_docx_from_template(template_path: str, output_path: str, context: dict) -> bool:
        """Generate DOCX from template using docxtpl"""
        try:
            if not template_path or not os.path.exists(template_path):
                # Create a basic template if none provided
                return DocumentProcessor._create_basic_docx(output_path, context)
            
            doc = DocxTemplate(template_path)
            doc.render(context)
            doc.save(output_path)
            return True
        except Exception as e:
            print(f"Error generating DOCX: {e}")
            # Fallback to basic template
            return DocumentProcessor._create_basic_docx(output_path, context)
    
    @staticmethod
    def _create_basic_docx(output_path: str, context: dict) -> bool:
        """Create a basic DOCX document without template"""
        try:
            doc = Document()
            
            # Title
            title = doc.add_heading(context.get('project_title', 'Propuesta de Proyecto'), 0)
            
            # Project info
            doc.add_heading('Información del Proyecto', level=1)
            
            project_info = [
                f"País: {context.get('country', 'N/A')}",
                f"Donante: {context.get('donor', 'N/A')}",
                f"Duración: {context.get('duration_months', 'N/A')} meses",
                f"Presupuesto: {context.get('budget_cap', 'N/A')}"
            ]
            
            for info in project_info:
                doc.add_paragraph(info)
            
            # Organization profile
            if context.get('org_profile'):
                doc.add_heading('Perfil de la Organización', level=1)
                doc.add_paragraph(context.get('org_profile', ''))
            
            # Narrative content
            if context.get('narrative'):
                doc.add_heading('Narrativa del Proyecto', level=1)
                doc.add_paragraph(context.get('narrative', ''))
            
            doc.save(output_path)
            return True
        except Exception as e:
            print(f"Error creating basic DOCX: {e}")
            return False
    
    @staticmethod
    def generate_excel_budget(output_path: str, budget_data: dict) -> bool:
        """Generate Excel budget from budget data"""
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Presupuesto"
            
            # Headers
            headers = [
                'Código', 'Categoría', 'Descripción', 'Unidad', 
                'Cantidad', 'Costo Unitario', 'Meses', 'Fase', 
                'Total', 'Justificación'
            ]
            
            # Style headers
            header_font = Font(bold=True)
            center_alignment = Alignment(horizontal='center')
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.alignment = center_alignment
            
            # Add budget items
            row = 2
            for item in budget_data.get('items', []):
                total = item.get('qty', 0) * item.get('unit_cost', 0) * item.get('months', 1)
                
                values = [
                    item.get('code', ''),
                    item.get('category', ''),
                    item.get('description', ''),
                    item.get('unit', ''),
                    item.get('qty', 0),
                    item.get('unit_cost', 0),
                    item.get('months', 1),
                    item.get('phase', ''),
                    total,
                    item.get('justification', '')
                ]
                
                for col, value in enumerate(values, 1):
                    ws.cell(row=row, column=col, value=value)
                row += 1
            
            # Add summary
            if budget_data.get('summary_by_category'):
                row += 2
                ws.cell(row=row, column=1, value="RESUMEN POR CATEGORÍA").font = header_font
                row += 1
                
                for category, amount in budget_data.get('summary_by_category', {}).items():
                    ws.cell(row=row, column=1, value=category)
                    ws.cell(row=row, column=2, value=amount)
                    row += 1
            
            # Add total
            row += 1
            ws.cell(row=row, column=1, value="TOTAL").font = header_font
            ws.cell(row=row, column=2, value=budget_data.get('total', 0)).font = header_font
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            wb.save(output_path)
            return True
            
        except Exception as e:
            print(f"Error generating Excel budget: {e}")
            return False