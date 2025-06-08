import streamlit as st
import requests
import pandas as pd
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="MediDoc Organizer",
    page_icon="🩺",
    layout="wide"
)

# --- Backend API URL ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- Helper Functions ---
def check_backend_connection():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# --- Main Application ---
st.title("🩺 MediDoc Organizer")
st.write("Your intelligent assistant for organizing and understanding medical reports.")

# --- Check Backend Connection ---
if not check_backend_connection():
    st.error("Backend server is not running. Please start the FastAPI server first.")
    st.code("python main.py")
    st.stop()

# --- Sidebar ---
st.sidebar.title("User Profile")
user_name = st.sidebar.text_input("Enter your name", value="Arnav Bansal")
st.sidebar.write(f"Welcome, **{user_name}**!")

# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs(["Upload Documents", "View Documents", "Search History"])

# --- Tab 1: Upload Documents ---
with tab1:
    st.header("Upload Your Medical Documents")
    st.write("Upload PDF files and images of your medical documents for automatic processing.")

    uploaded_files = st.file_uploader(
        "Choose your medical documents",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )
    
    if st.button("Upload and Process"):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    
                    try:
                        response = requests.post(f"{BACKEND_URL}/upload/", files=files, timeout=60)
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"Successfully processed {uploaded_file.name}")
                            
                            # Show extracted information
                            info = result.get('info', {})
                            st.write(f"**Category:** {info.get('category', 'N/A')}")
                            st.write(f"**Date:** {info.get('document_date', 'N/A')}")
                            st.write(f"**Doctor:** {info.get('doctor_name', 'N/A')}")
                            st.write(f"**Hospital:** {info.get('hospital_name', 'N/A')}")
                            st.write(f"**Summary:** {info.get('summary', 'N/A')}")
                            st.write("---")
                        else:
                            st.error(f"Error processing {uploaded_file.name}: {response.text}")
                            
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        else:
            st.warning("Please select files to upload.")

# --- Tab 2: View Documents ---
with tab2:
    st.header("Your Medical Documents")
    
    try:
        response = requests.get(f"{BACKEND_URL}/documents/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            if documents:
                st.write(f"Found {len(documents)} documents")
                
                # Create a simple table
                for doc in documents:
                    st.write("**File:**", doc.get('filename', 'Unknown'))
                    st.write("**Category:**", doc.get('category', 'N/A'))
                    st.write("**Date:**", doc.get('document_date', 'N/A'))
                    st.write("**Doctor:**", doc.get('doctor_name', 'N/A'))
                    st.write("**Hospital:**", doc.get('hospital_name', 'N/A'))
                    st.write("**Summary:**", doc.get('summary', 'N/A'))
                    st.write("---")
            else:
                st.info("No documents uploaded yet.")
        else:
            st.error("Could not retrieve documents from the backend.")
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

# --- Tab 3: Search History ---
with tab3:
    st.header("Search Your Medical History")
    st.write("Ask questions about your medical history in natural language.")
    
    # Example queries
    st.write("**Example questions:**")
    st.write("- What was the result of my latest blood test?")
    st.write("- Show me all prescriptions from Dr. Smith")
    st.write("- What medications am I currently taking?")
    
    search_query = st.text_input("Enter your question:")

    if st.button("Search"):
        if search_query.strip():
            with st.spinner("Searching through your medical records..."):
                try:
                    response = requests.get(
                        f"{BACKEND_URL}/search/", 
                        params={"query": search_query},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        
                        st.write("### Search Results")
                        
                        # Display the answer
                        if results.get("answer"):
                            st.write("**Answer:**")
                            st.write(results['answer'])
                            
                            # Display sources
                            sources = results.get("sources", [])
                            if sources:
                                st.write("**Sources:**")
                                for source in sources:
                                    st.write(f"- {source['filename']}")
                                    if 'summary' in source:
                                        st.write(f"  Summary: {source['summary']}")
                        else:
                            st.warning("Could not find an answer. Try rephrasing your question.")
                    else:
                        st.error(f"Search failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)}")
        else:
            st.warning("Please enter a search query.")

# --- Footer ---
st.write("---")
st.write("MediDoc Organizer - Built for better healthcare management")