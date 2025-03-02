from google.cloud import storage
from PyPDF2 import PdfReader
import docx
import io
import re
import os

class GCPDocumentProcessor:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = os.getenv("GCP_BUCKET_NAME")

    def process_gcp_document(self, gcs_path):
        """Process documents from GCP Cloud Storage"""
        bucket_name = gcs_path.split("/")[2]
        blob_path = "/".join(gcs_path.split("/")[3:])
        
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        file_stream = io.BytesIO()
        blob.download_to_file(file_stream)
        file_stream.seek(0)
        
        return self._extract_text(file_stream, blob.name.split('.')[-1])

    def process_uploaded_file(self, uploaded_file):
        """Process locally uploaded files"""
        file_stream = io.BytesIO(uploaded_file.getvalue())
        return self._extract_text(file_stream, uploaded_file.type.split('/')[-1])

    def _extract_text(self, file_stream, file_type):
        """Universal text extraction with improved error handling"""
        try:
            if file_type == "pdf":
                reader = PdfReader(file_stream)
                return "\n".join(page.extract_text() for page in reader.pages)
            elif file_type in ["docx", "vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                doc = docx.Document(file_stream)
                return "\n".join(para.text for para in doc.paragraphs)
            elif file_type == "txt":
                return file_stream.read().decode()
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise RuntimeError(f"Text extraction failed: {str(e)}")

    def _clean_text(self, text):
        """Enhanced text cleaning"""
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII
        return text.strip()