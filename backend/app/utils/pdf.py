"""
PDF processing utilities using PyMuPDF (fitz) and pdfplumber.
"""
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import io
from loguru import logger
from ..config import config


class PDFProcessor:
    """PDF processing with text extraction and preview generation."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF processor.
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.doc = None
        self.page_count = 0
        
        try:
            self.doc = fitz.open(pdf_path)
            self.page_count = len(self.doc)
            logger.info(f"Opened PDF: {pdf_path} ({self.page_count} pages)")
        except Exception as e:
            logger.error(f"Failed to open PDF {pdf_path}: {e}")
            raise
    
    def extract_page_text(self, page_no: int) -> str:
        """
        Extract text from a specific page.
        
        Args:
            page_no: Page number (0-indexed)
        
        Returns:
            Extracted text
        """
        try:
            page = self.doc[page_no]
            text = page.get_text()
            
            # Fallback to pdfplumber if PyMuPDF fails or returns empty
            if not text.strip():
                logger.warning(f"PyMuPDF returned empty text for page {page_no}, trying pdfplumber")
                text = self._extract_with_pdfplumber(page_no)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from page {page_no}: {e}")
            # Try pdfplumber as fallback
            try:
                return self._extract_with_pdfplumber(page_no)
            except:
                return ""
    
    def _extract_with_pdfplumber(self, page_no: int) -> str:
        """Fallback text extraction using pdfplumber."""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[page_no]
                text = page.extract_text()
                return text.strip() if text else ""
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for page {page_no}: {e}")
            return ""
    
    def extract_page_tables(self, page_no: int) -> List[Dict[str, Any]]:
        """
        Extract tables from a specific page using pdfplumber.
        
        Args:
            page_no: Page number (0-indexed)
        
        Returns:
            List of tables, each as a dict with 'data' (list of rows) and 'bbox'
        """
        tables = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[page_no]
                extracted_tables = page.extract_tables()
                
                for idx, table in enumerate(extracted_tables):
                    if table:
                        # Convert table to readable format
                        table_text = self._table_to_text(table)
                        tables.append({
                            "index": idx,
                            "data": table,
                            "text": table_text
                        })
                        logger.debug(f"Extracted table {idx} from page {page_no} with {len(table)} rows")
        except Exception as e:
            logger.error(f"Error extracting tables from page {page_no}: {e}")
        
        return tables
    
    def _table_to_text(self, table: List[List]) -> str:
        """Convert a table (list of rows) to readable text format."""
        if not table:
            return ""
        
        lines = []
        for row in table:
            # Filter out None values and convert to strings
            row_text = [str(cell) if cell is not None else "" for cell in row]
            lines.append(" | ".join(row_text))
        
        return "\n".join(lines)
    
    def extract_page_images(self, page_no: int, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract images from a specific page.
        
        Args:
            page_no: Page number (0-indexed)
            output_dir: Optional directory to save extracted images
        
        Returns:
            List of image info dicts with 'image' (PIL Image), 'bbox', and optionally 'path'
        """
        images = []
        try:
            page = self.doc[page_no]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    base_image = self.doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Convert to PIL Image
                    img_pil = Image.open(io.BytesIO(image_bytes))
                    
                    image_info = {
                        "index": img_index,
                        "image": img_pil,
                        "width": img_pil.width,
                        "height": img_pil.height,
                        "format": image_ext,
                        "bbox": img[1:5] if len(img) > 1 else None
                    }
                    
                    # Save image if output directory provided
                    if output_dir:
                        output_path = Path(output_dir) / f"page_{page_no}_img_{img_index}.{image_ext}"
                        Path(output_dir).mkdir(parents=True, exist_ok=True)
                        img_pil.save(output_path)
                        image_info["path"] = str(output_path)
                    
                    images.append(image_info)
                    logger.debug(f"Extracted image {img_index} from page {page_no}: {img_pil.width}x{img_pil.height}")
                    
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_no}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting images from page {page_no}: {e}")
        
        return images
    
    def extract_all_page_content(self, page_no: int, images_output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract all content from a page: text, tables, and images.
        
        Args:
            page_no: Page number (0-indexed)
            images_output_dir: Optional directory to save extracted images
        
        Returns:
            Dict with 'text', 'tables', and 'images'
        """
        content = {
            "text": "",
            "tables": [],
            "images": []
        }
        
        # Extract text
        content["text"] = self.extract_page_text(page_no)
        
        # Extract tables
        content["tables"] = self.extract_page_tables(page_no)
        
        # Extract images
        content["images"] = self.extract_page_images(page_no, images_output_dir)
        
        logger.info(f"Extracted content from page {page_no}: {len(content['text'])} chars, "
                   f"{len(content['tables'])} tables, {len(content['images'])} images")
        
        return content
    
    def generate_page_preview(
        self,
        page_no: int,
        output_path: str,
        width: int = 1200,
        format: str = "PNG"
    ) -> str:
        """
        Generate a preview image for a page.
        
        Args:
            page_no: Page number (0-indexed)
            output_path: Path to save the preview image
            width: Target width in pixels
            format: Image format (PNG, JPEG)
        
        Returns:
            Path to the saved preview image
        """
        try:
            page = self.doc[page_no]
            
            # Calculate zoom to achieve target width
            page_width = page.rect.width
            zoom = width / page_width
            
            # Create transformation matrix
            mat = fitz.Matrix(zoom, zoom)
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            img.save(output_path, format=format)
            
            logger.debug(f"Generated preview for page {page_no}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating preview for page {page_no}: {e}")
            raise
    
    def extract_all_pages(self) -> List[Dict[str, Any]]:
        """
        Extract text from all pages.
        
        Returns:
            List of dicts with page_no and text
        """
        pages = []
        for page_no in range(self.page_count):
            text = self.extract_page_text(page_no)
            pages.append({
                "page_no": page_no,
                "text": text
            })
        
        logger.info(f"Extracted text from {len(pages)} pages")
        return pages
    
    def generate_all_previews(
        self,
        output_dir: str,
        width: int = 1200
    ) -> List[str]:
        """
        Generate preview images for all pages.
        
        Args:
            output_dir: Directory to save previews
            width: Target width in pixels
        
        Returns:
            List of preview file paths
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        previews = []
        for page_no in range(self.page_count):
            output_path = str(Path(output_dir) / f"page_{page_no}.png")
            try:
                self.generate_page_preview(page_no, output_path, width)
                previews.append(output_path)
            except Exception as e:
                logger.error(f"Failed to generate preview for page {page_no}: {e}")
                previews.append(None)
        
        logger.info(f"Generated {len([p for p in previews if p])} previews")
        return previews
    
    def get_page_dimensions(self, page_no: int) -> Tuple[float, float]:
        """
        Get dimensions of a page.
        
        Args:
            page_no: Page number (0-indexed)
        
        Returns:
            Tuple of (width, height) in points
        """
        try:
            page = self.doc[page_no]
            rect = page.rect
            return (rect.width, rect.height)
        except Exception as e:
            logger.error(f"Error getting dimensions for page {page_no}: {e}")
            return (0, 0)
    
    def close(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()
            logger.debug(f"Closed PDF: {self.pdf_path}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

