import json
import os
from typing import List, Dict, Any
from pypdf import PdfReader
import io

class KBManager:
    def __init__(self, storage_path: str = "kb.json"):
        self.storage_path = storage_path
        self.kb = self._load_kb()

    def _load_kb(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                return json.load(f)
        return []

    def save_kb(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.kb, f, indent=4)

    def add_section(self, content: str, source_name: str):
        self.kb.append({
            "source": source_name,
            "content": content
        })
        self.save_kb()

    def process_files(self, uploaded_files):
        """
        Processes a list of uploaded files. 
        If 5+ files, combines them into one section.
        """
        if not uploaded_files:
            return None

        if len(uploaded_files) >= 5:
            combined_content = ""
            source_names = []
            for uploaded_file in uploaded_files:
                text = self._extract_text(uploaded_file)
                combined_content += f"\n--- Section from {uploaded_file.name} ---\n{text}\n"
                source_names.append(uploaded_file.name)
            
            combined_source = f"Combined Collection: {', '.join(source_names[:3])}..."
            self.add_section(combined_content, combined_source)
            return combined_source
        else:
            sources = []
            for uploaded_file in uploaded_files:
                text = self._extract_text(uploaded_file)
                self.add_section(text, uploaded_file.name)
                sources.append(uploaded_file.name)
            return ", ".join(sources)

    def _extract_text(self, uploaded_file) -> str:
        if uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif uploaded_file.name.endswith(('.txt', '.md')):
            return uploaded_file.read().decode('utf-8')
        else:
            # For images, we would ideally use OCR/Vision, 
            # for now we'll mark it as non-text or placeholder
            return f"[Non-text file: {uploaded_file.name}]"

    def query_kb(self, query: str) -> str:
        # Simple keyword-based retrieval for MVP
        # In a full version, this would use embeddings
        relevant_content = ""
        query_words = set(query.lower().split())
        
        for section in self.kb:
            content_lower = section['content'].lower()
            if any(word in content_lower for word in query_words):
                relevant_content += f"\n--- Source: {section['source']} ---\n{section['content']}\n"
        
        return relevant_content[:5000] # Cap to avoid context overflow
