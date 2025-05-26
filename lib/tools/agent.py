from typing import Dict, Any, List
import google.generativeai as genai
import re
from pathlib import Path

from lib.tools.util import Tool

class Agent:
    """Base agent class"""
    def __init__(self, name: str, description: str, tools: List[Tool] = None):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.classifier_model = genai.GenerativeModel('gemini-2.0-flash')
    
    def can_handle(self, question: str) -> bool:
        """Determine if this agent can handle the question using AI classification"""
        raise NotImplementedError
    
    def process(self, question: str, mode: str = "off-syllabus") -> Dict[str, Any]:
        """Process the question and return response"""
        raise NotImplementedError
    
    def _search_documents(self, question: str, subject_filter: str = None) -> List[Dict[str, str]]:
        """Search through documents in books directory for relevant content"""
        books_dir = Path("books")
        if not books_dir.exists():
            print(f"Books directory not found: {books_dir}")
            return []
        
        relevant_content = []
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.doc'}
        
        print(f"Searching in {books_dir} for question: {question}")
        
        for file_path in books_dir.rglob("*"):
            if not file_path.is_file():
                continue
                
            if file_path.suffix.lower() not in supported_extensions:
                continue
            
            # Filter by subject if specified (make it less strict)
            if subject_filter:
                file_name_lower = file_path.name.lower()
                if not (subject_filter.lower() in file_name_lower or 
                       any(keyword in file_name_lower for keyword in [subject_filter[:4], subject_filter[:5]])):
                    # Don't skip, just continue checking - subject filter is now optional
                    pass
            
            print(f"Processing file: {file_path}")
            
            try:
                content = ""
                file_ext = file_path.suffix.lower()
                
                if file_ext in ['.txt', '.md']:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                elif file_ext == '.pdf':
                    try:
                        # Try multiple PDF reading methods
                        print(f"Attempting to read PDF: {file_path}")
                        
                        # Method 1: PyPDF2
                        try:
                            import PyPDF2
                            with open(file_path, 'rb') as file:
                                reader = PyPDF2.PdfReader(file)
                                content = ""
                                print(f"PDF has {len(reader.pages)} pages")
                                for i, page in enumerate(reader.pages[:20]):  # Limit to first 20 pages
                                    page_text = page.extract_text()
                                    content += page_text + "\n"
                                    print(f"Page {i+1} extracted {len(page_text)} characters")
                                print(f"Total content extracted: {len(content)} characters")
                        except Exception as pdf_error:
                            print(f"PyPDF2 failed: {pdf_error}")
                            
                            # Method 2: Try pdfplumber as backup
                            try:
                                import pdfplumber
                                print("Trying pdfplumber...")
                                with pdfplumber.open(file_path) as pdf:
                                    content = ""
                                    for i, page in enumerate(pdf.pages[:20]):
                                        page_text = page.extract_text() or ""
                                        content += page_text + "\n"
                                        print(f"Page {i+1} extracted {len(page_text)} characters with pdfplumber")
                            except ImportError:
                                print("pdfplumber not available")
                                # Method 3: Basic text extraction attempt
                                with open(file_path, 'rb') as f:
                                    raw_content = f.read()
                                    # Try to extract any readable text
                                    content = raw_content.decode('utf-8', errors='ignore')
                                    # Remove binary junk, keep only readable text
                                    import re
                                    content = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', content)
                                    content = re.sub(r'\s+', ' ', content).strip()
                                    print(f"Raw extraction yielded {len(content)} characters")
                            except Exception as backup_error:
                                print(f"Backup PDF reading failed: {backup_error}")
                                continue
                                
                    except Exception as e:
                        print(f"All PDF reading methods failed for {file_path}: {e}")
                        continue
                elif file_ext in ['.docx']:
                    try:
                        from docx import Document
                        doc = Document(file_path)
                        content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    except Exception as e:
                        print(f"Error reading DOCX {file_path}: {e}")
                        continue
                else:
                    # Skip unsupported formats for now
                    continue
                
                if not content.strip():
                    print(f"No content extracted from {file_path}")
                    continue
                
                print(f"Extracted {len(content)} characters from {file_path}")
                
                # Use multiple methods to determine relevance - make it less strict
                is_relevant = False
                
                # Method 1: Simple keyword matching as fallback (more lenient)
                question_words = [word.lower() for word in question.split() if len(word) > 2]  # Changed from 3 to 2
                content_lower = content.lower()
                keyword_matches = sum(1 for word in question_words if word in content_lower)
                
                # Be more lenient - even partial matches count
                if keyword_matches >= 1 or len(question_words) == 0:  # At least one keyword match OR simple question
                    is_relevant = True
                    print(f"File {file_path.name} relevant by keyword matching ({keyword_matches} matches from words: {question_words})")
                
                # Method 2: Check for common database/storage terms if question is about those topics
                db_terms = ['storage', 'disk', 'memory', 'database', 'raid', 'ssd', 'flash', 'magnetic', 'performance']
                if any(term in question.lower() for term in ['storage', 'disk', 'raid', 'ssd', 'database', 'memory']):
                    if any(term in content_lower for term in db_terms):
                        is_relevant = True
                        print(f"File {file_path.name} relevant by database/storage topic matching")
                
                # Method 3: AI relevance check (but don't rely solely on it)
                if not is_relevant:
                    try:
                        # Make AI prompt less strict
                        relevance_prompt = f"""
                        Could this document help answer the question: "{question}"?
                        
                        Document: {file_path.name}
                        Content preview: {content[:800]}...
                        
                        Be generous - if there's ANY connection, even loose, respond YES.
                        Respond with only "YES" if it could be helpful, "NO" if completely unrelated.
                        """
                        
                        relevance_response = self.classifier_model.generate_content(relevance_prompt)
                        if relevance_response.text.strip().upper() == "YES":
                            is_relevant = True
                            print(f"File {file_path.name} relevant by AI classification")
                    except Exception as e:
                        print(f"AI relevance check failed for {file_path}: {e}")
                        # If AI fails, be very lenient - include most content
                        if len(content) > 100:  # If we extracted substantial content, include it
                            is_relevant = True
                            print(f"Including {file_path.name} due to substantial content ({len(content)} chars)")
                
                print(f"Final relevance decision for {file_path.name}: {is_relevant}")
                
                if is_relevant:
                    # Include more content but chunk it appropriately
                    content_chunk = content[:15000]  # Increased from 2000
                    relevant_content.append({
                        "file": str(file_path.name),
                        "content": content_chunk,
                        "full_path": str(file_path),
                        "size": len(content)
                    })
                    print(f"Added {file_path.name} to relevant content")
                else:
                    print(f"File {file_path.name} not considered relevant")
                        
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue
        
        print(f"Found {len(relevant_content)} relevant documents")
        return relevant_content
    
    def _extract_and_calculate(self, question: str) -> tuple[Dict[str, float], List[str]]:
        """Common method to extract mathematical expressions and calculate results"""
        tools_used = []
        calculations = {}
        
        # Enhanced pattern to catch more mathematical expressions
        calc_patterns = [
            r'[\d\+\-\*/\^\(\)\.]+(?:\s*[\+\-\*/\^]\s*[\d\+\-\*/\^\(\)\.]+)+',
            r'\d+\.?\d*\s*[\+\-\*/\^]\s*\d+\.?\d*',
            r'\(\s*[\d\+\-\*/\^\(\)\.]+\s*\)'
        ]
        
        for pattern in calc_patterns:
            math_expressions = re.findall(pattern, question)
            for expr in math_expressions:
                expr = expr.strip()
                if any(op in expr for op in ['+', '-', '*', '/', '^']) and len(expr) > 1:
                    try:
                        if hasattr(self, 'tools') and self.tools:
                            result = self.tools[0].execute(expr)
                            calculations[expr] = result
                            tools_used.append("calculator")
                    except Exception:
                        continue
        
        return calculations, list(set(tools_used))