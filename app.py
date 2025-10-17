"""
LifeLink AI - Health Report Analyzer
A GenAI-powered health report summarizer with multi-language support
Enhanced with PDF export and Text-to-Speech features
"""

import streamlit as st
import google.generativeai as genai
import pdfplumber
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from gtts import gTTS
import base64
from datetime import datetime

# ========================================
# CONFIGURATION
# ========================================

# Insert your Gemini API key here
GEMINI_API_KEY = "AIzaSyDlqjHFgaXKrVrfseD5vlbIjCMUl9FVrlw"

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
    """Extract text content from uploaded PDF file"""
    try:
        text = ""
        pdf_file.seek(0)  # Reset file pointer
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")


def generate_health_summary(report_text, language):
    """Send extracted text to Gemini API and get health summary"""
    language_instruction = ""
    if language != "English":
        language_instruction = f"\n\nIMPORTANT: Translate the entire summary into {language} language. Use simple, everyday {language} words that anyone can understand."
    
    prompt = f"""You are a helpful medical assistant for LifeLink AI, a health monitoring system.

Analyze the following health report and provide a clear, easy-to-understand summary for the patient.

Health Report:
{report_text}

Please provide:
1. Key Findings: Main health indicators and their values
2. What This Means: Explain in simple, non-technical language what these results indicate
3. Recommendations: Basic health advice based on the report (general wellness tips only, not medical prescriptions)
4. Important Notes: Any values that seem out of normal range (mark with ⚠ if concerning)

Write in a friendly, reassuring tone. Avoid complex medical jargon. Use bullet points for clarity.{language_instruction}

Note: This is an AI-generated summary and should not replace professional medical advice."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")


def create_pdf_summary(summary_text, language):
    """Create a PDF file from the health summary with Unicode support"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=40
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#667EEA',
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#666666',
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=16
        )
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor='#CC0000',
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        
        # Add title
        elements.append(Paragraph("LifeLink AI - Health Report Summary", title_style))
        elements.append(Spacer(1, 12))
        
        # Add metadata
        elements.append(Paragraph(f"Language: {language}", subtitle_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        elements.append(Paragraph("Generated by LifeLink AI", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Process summary text
        # Remove markdown and clean text
        clean_text = summary_text.replace('**', '').replace('*', '').replace('#', '')
        
        # Split into paragraphs
        paragraphs = clean_text.split('\n')
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Escape special XML characters
                para = para.replace('&', '&amp;')
                para = para.replace('<', '&lt;')
                para = para.replace('>', '&gt;')
                
                # Try to encode safely for PDF
                try:
                    # For non-ASCII characters, encode them as Unicode entities
                    safe_para = para.encode('ascii', 'xmlcharrefreplace').decode('ascii')
                    elements.append(Paragraph(safe_para, body_style))
                except Exception:
                    # Fallback: just use ASCII
                    safe_para = para.encode('ascii', 'ignore').decode('ascii')
                    if safe_para:
                        elements.append(Paragraph(safe_para, body_style))
            else:
                elements.append(Spacer(1, 8))
        
        # Add disclaimer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "DISCLAIMER: This is an AI-generated summary and should not replace professional medical advice. "
            "Always consult with your healthcare provider for medical decisions.",
            disclaimer_style
        ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    except Exception as e:
        raise Exception(f"Error creating PDF: {str(e)}")


def text_to_speech(text, language):
    """Convert text to speech using gTTS"""
    try:
        lang_map = {
            "English": "en",
            "Hindi": "hi",
            "Marathi": "mr",
            "Kannada": "kn"
        }
        
        # Clean text for TTS
        clean_text = text.replace('**', '').replace('*', '').replace('#', '')
        clean_text = clean_text.replace('⚠', 'Warning: ')
        
        # Generate speech
        tts = gTTS(text=clean_text, lang=lang_map.get(language, "en"), slow=False)
        
        # Save to BytesIO
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        return audio_bytes
    
    except Exception as e:
        raise Exception(f"Error generating audio: {str(e)}")


def get_audio_player_html(audio_base64):
    """Create custom HTML5 audio player with controls"""
    html = f"""
    <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin: 10px 0;">
        <audio id="audioPlayer" controls style="width: 100%; margin-bottom: 10px;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
            <button onclick="document.getElementById('audioPlayer').playbackRate = 0.75" 
                    style="padding: 8px 16px; background: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
                🐢 0.75x
            </button>
            <button onclick="document.getElementById('audioPlayer').playbackRate = 1.0" 
                    style="padding: 8px 16px; background: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
                ▶️ 1.0x
            </button>
            <button onclick="document.getElementById('audioPlayer').playbackRate = 1.25" 
                    style="padding: 8px 16px; background: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
                🐰 1.25x
            </button>
            <button onclick="document.getElementById('audioPlayer').playbackRate = 1.5" 
                    style="padding: 8px 16px; background: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
                ⚡ 1.5x
            </button>
        </div>
    </div>
    """
    return html


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
    
    # Initialize session state
    if 'summary' not in st.session_state:
        st.session_state['summary'] = None
    if 'audio_generated' not in st.session_state:
        st.session_state['audio_generated'] = False
    
    # Header
    st.title("🏥 LifeLink AI")
    st.subheader("Health Report Analyzer")
    st.markdown("Upload your health report PDF and get an easy-to-understand summary powered by AI")
    st.markdown("---")
    
    # Check if API key is configured
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        st.error("⚠ Please configure your Gemini API key in the code before using this app.")
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
                    report_text = extract_text_from_pdf(uploaded_file)
                    
                    if not report_text or len(report_text) < 50:
                        st.error("❌ Could not extract sufficient text from the PDF. Please ensure the PDF contains readable text.")
                        st.stop()
                    
                    # Show extracted text in expander
                    with st.expander("📄 View Extracted Text"):
                        st.text_area("Report Content", report_text, height=200, key="extracted_text")
                    
                except Exception as e:
                    st.error(f"❌ Error reading PDF: {str(e)}")
                    st.stop()
            
            with st.spinner(f"Generating {language} summary using Gemini AI..."):
                try:
                    summary = generate_health_summary(report_text, language)
                    
                    st.session_state['summary'] = summary
                    st.session_state['language'] = language
                    st.session_state['audio_generated'] = False
                    
                except Exception as e:
                    st.error(f"❌ Error generating summary: {str(e)}")
                    st.info("Please check your API key and internet connection.")
                    st.stop()
    
    # Display summary if available
    if st.session_state['summary'] is not None:
        summary = st.session_state['summary']
        language = st.session_state['language']
        
        # Display summary
        st.markdown("---")
        st.markdown("## 📊 Health Report Summary")
        st.markdown(summary)
        
        # Action buttons
        st.markdown("---")
        st.markdown("### 📥 Download Options")
        
        col1, col2 = st.columns(2)
        
        # Text download button
        with col1:
            st.download_button(
                label="📄 Download as Text",
                data=summary,
                file_name=f"health_summary_{language.lower()}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_txt"
            )
        
        # PDF download button
        with col2:
            try:
                pdf_bytes = create_pdf_summary(summary, language)
                st.download_button(
                    label="📕 Download as PDF",
                    data=pdf_bytes,
                    file_name=f"health_summary_{language.lower()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_pdf"
                )
            except Exception as e:
                st.error(f"PDF generation error: {str(e)}")
        
        # Audio section
        st.markdown("---")
        st.markdown("### 🔊 Audio Summary")
        
        if st.button("🎵 Generate Audio", use_container_width=True, type="primary", key="generate_audio"):
            with st.spinner("Generating audio... This may take a moment..."):
                try:
                    audio_bytes = text_to_speech(summary, language)
                    audio_data = audio_bytes.read()
                    audio_base64 = base64.b64encode(audio_data).decode()
                    
                    st.session_state['audio_data'] = audio_data
                    st.session_state['audio_base64'] = audio_base64
                    st.session_state['audio_generated'] = True
                    
                    st.success("✅ Audio generated successfully!")
                    
                except Exception as e:
                    st.error(f"Audio generation error: {str(e)}")
                    st.info("Text-to-speech may not be available for all languages.")
        
        # Display audio player if audio is generated
        if st.session_state.get('audio_generated', False):
            st.markdown("#### 🎧 Listen to Your Summary")
            audio_html = get_audio_player_html(st.session_state['audio_base64'])
            st.markdown(audio_html, unsafe_allow_html=True)
            
            # Download audio button
            st.download_button(
                label="💾 Download Audio File",
                data=st.session_state['audio_data'],
                file_name=f"health_summary_{language.lower()}.mp3",
                mime="audio/mp3",
                use_container_width=True,
                key="download_audio"
            )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <p>⚕ This is an AI-powered tool and should not replace professional medical advice.</p>
        <p>Always consult with your healthcare provider for medical decisions.</p>
        <p style='margin-top: 10px;'><strong>LifeLink AI</strong> | Powered by Google Gemini</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
