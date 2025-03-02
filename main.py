import streamlit as st
from utils.gcp_utils import GCPDocumentProcessor
from utils.ai_processor import DueDiligenceAnalyzer
from utils.report_generator import ReportGenerator
import os
from dotenv import load_dotenv
import base64

# Initialize configuration
load_dotenv()

st.set_page_config(
    page_title="AI Due Diligence Platform",
    layout="wide",
    page_icon="🔍"
)

# Session state initialization
if 'processing' not in st.session_state:
    st.session_state.processing = False

def initialize_services():
    return {
        'processor': GCPDocumentProcessor(),
        'analyzer': DueDiligenceAnalyzer(),
        'report_gen': ReportGenerator()
    }

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def main():
    st.title("🔍 AI-Powered Due Diligence Platform")
    st.markdown("---")
    
    services = initialize_services()
    
    # File Upload Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("1. Document Input")
        upload_method = st.radio(
            "Select input method:",
            ["GCP Bucket", "Local Upload"],
            horizontal=True
        )

        document_path = None
        uploaded_file = None
        
        if upload_method == "GCP Bucket":
            document_path = st.text_input(
                "GCS Document Path",
                value="documents/example.pdf",
                help="Format: gs://bucket-name/path/to/file.pdf"
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload Document",
                type=["pdf", "docx", "txt"],
                help="Supported formats: PDF, DOCX, TXT"
            )

    with col2:
        st.header("2. Configuration")
        analysis_type = st.selectbox(
            "Analysis Depth",
            ["Basic Review", "Comprehensive Due Diligence"],
            index=1
        )
        st.checkbox("Enable Advanced NLP", value=True)
        st.checkbox("Include Risk Analysis", value=True)

    st.markdown("---")
    
    # Processing Section
    if st.button("🚀 Start Analysis", type="primary"):
        if not (document_path or uploaded_file):
            st.error("Please provide a document!")
            return
            
        try:
            st.session_state.processing = True
            progress_bar = st.progress(0)
            
            # Document Processing
            with st.spinner("📄 Processing document..."):
                if uploaded_file:
                    text_content = services['processor'].process_uploaded_file(uploaded_file)
                else:
                    text_content = services['processor'].process_gcp_document(document_path)
                progress_bar.progress(30)
            
            # AI Analysis
            with st.spinner("🤖 Analyzing content..."):
                structured_data = services['analyzer'].analyze_document(text_content)
                progress_bar.progress(60)
            
            # Report Generation
            with st.spinner("📊 Generating report..."):
                report_content = services['report_gen'].generate_report(
                    structured_data, 
                    analysis_type=analysis_type
                )
                progress_bar.progress(90)
                
                # Save and display report
                report_path = "due_diligence_report.md"
                with open(report_path, "w") as f:
                    f.write(report_content)
                
                progress_bar.progress(100)
                st.success("✅ Analysis completed!")
                
                # Show results
                st.markdown("### Final Report")
                st.download_button(
                    label="📥 Download Report",
                    data=report_content,
                    file_name=report_path,
                    mime="text/markdown"
                )
                
                with st.expander("View Report Preview"):
                    st.markdown(report_content)
                
                if uploaded_file and uploaded_file.type == "application/pdf":
                    st.markdown("### Document Preview")
                    show_pdf(uploaded_file.name)

        except Exception as e:
            st.error(f"🚨 Error: {str(e)}")
            st.exception(e)
        finally:
            st.session_state.processing = False

if __name__ == "__main__":
    main()