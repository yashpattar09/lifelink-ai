"""
LifeLink AI - Health Report Analyzer
A GenAI-powered health report summarizer with multi-language support
"""

import streamlit as st
import google.generativeai as genai
import pdfplumber
from io import BytesIO
import os

# ========================================
# CONFIGURATION
# ========================================

# Insert your Gemini API key here
GEMINI_API_KEY = "AIzaSyDlqjHFgaXKrVrfseD5vlbIjCMUl9FVrlw"  # Replace with your actual API key
# Alternatively, use environment variable: os.getenv("GEMINI_API_KEY")

# Configure Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API Configuration Error: {str(e)}")

# ========================================
# HELPER FUNCTIONS
# ========================================

def extract_text_from_pdf(pdf_file):
    """
    Extract text content from uploaded PDF file using pdfplumber
    Args:
        pdf_file: Uploaded PDF file object
    Returns:
        Extracted text as string
    """
    try:
        text = ""
        with pdfplumber.open(BytesIO(pdf_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")


def generate_health_summary(report_text, language):
    """
    Send extracted text to Gemini API and get health summary
    Args:
        report_text: Extracted text from health report
        language: Target language for summary
    Returns:
        Generated health summary
    """
    # Create prompt based on selected language
    language_instruction = ""
    if language != "English":
        language_instruction = f"\n\nIMPORTANT: Translate the entire summary into {language} language. Use simple, everyday {language} words that anyone can understand."
    
    prompt = f"""You are a helpful medical assistant for LifeLink AI, a health monitoring system.

Analyze the following health report and provide a clear, easy-to-understand summary for the patient.

Health Report:
{report_text}

Please provide:
1. **Key Findings**: Main health indicators and their values
2. **What This Means**: Explain in simple, non-technical language what these results indicate
3. **Recommendations**: Basic health advice based on the report (general wellness tips only, not medical prescriptions)
4. **Important Notes**: Any values that seem out of normal range (mark with ⚠️ if concerning)

Write in a friendly, reassuring tone. Avoid complex medical jargon. Use bullet points for clarity.{language_instruction}

Note: This is an AI-generated summary and should not replace professional medical advice."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")


# ========================================
# STREAMLIT UI
# ========================================

def main():
    # Page configuration
    st.set_page_config(
        page_title="LifeLink AI - Health Report Analyzer",
        page_icon="🏥",
        layout="centered"
    )
    
    # Header
    st.title("🏥 LifeLink AI")
    st.subheader("Health Report Analyzer")
    st.markdown("Upload your health report PDF and get an easy-to-understand summary powered by AI")
    st.markdown("---")
    
    # Check if API key is configured
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        st.error("⚠️ Please configure your Gemini API key in the code before using this app.")
        st.info("Get your free API key from: https://makersuite.google.com/app/apikey")
        st.stop()
    
    # Language selection
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Health Report (PDF)",
            type=['pdf'],
            help="Upload your medical test report in PDF format"
        )
    with col2:
        language = st.selectbox(
            "Output Language",
            ["English", "Hindi", "Marathi", "Kannada"],
            help="Choose the language for your summary"
        )
    
    # Process button
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        if st.button("🔍 Analyze Report", type="primary", use_container_width=True):
            with st.spinner("Extracting text from PDF..."):
                try:
                    # Extract text from PDF
                    report_text = extract_text_from_pdf(uploaded_file)
                    
                    if not report_text or len(report_text) < 50:
                        st.error("❌ Could not extract sufficient text from the PDF. Please ensure the PDF contains readable text.")
                        st.stop()
                    
                    # Show extracted text in expander (for verification)
                    with st.expander("📄 View Extracted Text"):
                        st.text_area("Report Content", report_text, height=200)
                    
                except Exception as e:
                    st.error(f"❌ Error reading PDF: {str(e)}")
                    st.stop()
            
            with st.spinner(f"Generating {language} summary using Gemini AI..."):
                try:
                    # Generate summary using Gemini
                    summary = generate_health_summary(report_text, language)
                    
                    # Display summary
                    st.markdown("---")
                    st.markdown("## 📊 Health Report Summary")
                    st.markdown(summary)
                    
                    # Download button for summary
                    st.download_button(
                        label="📥 Download Summary",
                        data=summary,
                        file_name=f"health_summary_{language.lower()}.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error generating summary: {str(e)}")
                    st.info("Please check your API key and internet connection.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <p>⚕️ This is an AI-powered tool and should not replace professional medical advice.</p>
        <p>Always consult with your healthcare provider for medical decisions.</p>
        <p style='margin-top: 10px;'><strong>LifeLink AI</strong> | Powered by Google Gemini</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()