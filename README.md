# MediDoc-Organizer

# MediDoc Organizer Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [API Documentation](#api-documentation)
5. [Frontend Documentation](#frontend-documentation)
6. [Database Schema](#database-schema)
7. [Configuration](#configuration)
8. [Usage Guide](#usage-guide)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)
11. [Development Notes](#development-notes)

## Overview

MediDoc Organizer is an intelligent medical document management system that helps users organize, process, and search through their medical documents using AI-powered text extraction and natural language processing.

### Key Features
- **Document Upload**: Support for PDF and image files (PNG, JPG, JPEG)
- **AI-Powered Processing**: Automatic extraction of medical information using Groq's Llama model
- **Document Categorization**: Automatic classification into medical document types
- **Natural Language Search**: Query medical history using conversational language
- **Web Interface**: User-friendly Streamlit-based frontend
- **RESTful API**: FastAPI backend for document processing and retrieval

### Technology Stack
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: SQLite
- **AI/ML**: Groq API (Llama 3.1-8B)
- **OCR**: Tesseract (via pytesseract)
- **PDF Processing**: pdf2image
- **Image Processing**: PIL (Pillow)

## Architecture

```
┌─────────────────┐    HTTP Requests    ┌─────────────────┐
│   Streamlit     │ ──────────────────► │   FastAPI       │
│   Frontend      │                     │   Backend       │
│   (Port 8501)   │ ◄────────────────── │   (Port 8000)   │
└─────────────────┘    JSON Responses   └─────────────────┘
                                                │
                                                ▼
                                        ┌─────────────────┐
                                        │   SQLite DB     │
                                        │   (medidoc.db)  │
                                        └─────────────────┘
                                                │
                                                ▼
                                        ┌─────────────────┐
                                        │   File Storage  │
                                        │   (uploads/)    │
                                        └─────────────────┘
                                                │
                                                ▼
                                        ┌─────────────────┐
                                        │   Groq API      │
                                        │   (AI Service)  │
                                        └─────────────────┘
```

## Installation & Setup

### Prerequisites

#### System Requirements
- Python 3.8+
- Tesseract OCR engine
- poppler-utils (for PDF processing)

#### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

**Windows:**
- Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download and install poppler from: https://blog.alivate.com.au/poppler-windows/

### Python Dependencies

Create and activate a virtual environment:
```bash
python -m venv medidoc_env
source medidoc_env/bin/activate  # On Windows: medidoc_env\Scripts\activate
```

Install required packages:
```bash
pip install fastapi uvicorn streamlit sqlite3 pytesseract pillow pdf2image groq requests pandas
```

### Environment Setup

1. **Groq API Key**: Set your Groq API key as an environment variable:
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

2. **Directory Structure**:
```
medidoc-organizer/
├── main.py          # FastAPI backend
├── app.py           # Streamlit frontend
├── uploads/         # Auto-created for file storage
├── medidoc.db       # Auto-created SQLite database
└── requirements.txt # Python dependencies
```

### Running the Application

1. **Start the Backend Server**:
```bash
python main.py
```
The API will be available at: http://localhost:8000

2. **Start the Frontend** (in a new terminal):
```bash
streamlit run app.py
```
The web interface will be available at: http://localhost:8501

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
- **GET** `/health`
- **Description**: Check if the API is running
- **Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### 2. Root Endpoint
- **GET** `/`
- **Description**: Basic API information
- **Response**:
```json
{
  "message": "MediDoc API is running"
}
```

#### 3. Upload Document
- **POST** `/upload/`
- **Description**: Upload and process a medical document
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: File upload (PDF, PNG, JPG, JPEG)
- **Response**:
```json
{
  "filename": "report.pdf",
  "info": {
    "category": "Lab Report",
    "document_date": "2024-01-15",
    "doctor_name": "Dr. Smith",
    "hospital_name": "City Hospital",
    "summary": "Blood test results showing normal values"
  },
  "status": "success"
}
```

#### 4. Get All Documents
- **GET** `/documents/`
- **Description**: Retrieve all processed documents
- **Response**:
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "report.pdf",
      "category": "Lab Report",
      "document_date": "2024-01-15",
      "doctor_name": "Dr. Smith",
      "hospital_name": "City Hospital",
      "summary": "Blood test results"
    }
  ],
  "count": 1
}
```

#### 5. Search Documents
- **GET** `/search/`
- **Description**: Search through documents using natural language
- **Parameters**:
  - `query`: Search query string
- **Response**:
```json
{
  "answer": "Based on your latest blood test from Dr. Smith...",
  "sources": [
    {
      "filename": "blood_test.pdf",
      "summary": "Blood test results",
      "category": "Lab Report"
    }
  ]
}
```

### Error Responses

The API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid file type, empty file, etc.)
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Frontend Documentation

### User Interface Components

#### 1. Main Navigation
- **Upload Documents**: Upload and process new medical files
- **View Documents**: Browse all processed documents
- **Search History**: Natural language search interface

#### 2. Upload Documents Tab
- **File Upload**: Drag-and-drop or browse for files
- **Supported Formats**: PDF, PNG, JPG, JPEG
- **Processing Status**: Real-time feedback during upload
- **Extracted Information Display**: Shows categorized information

#### 3. View Documents Tab
- **Document List**: All processed documents with metadata
- **Information Display**: Category, date, doctor, hospital, summary
- **Sorting**: Documents sorted by date (newest first)

#### 4. Search History Tab
- **Natural Language Interface**: Ask questions in plain English
- **Example Queries**: Pre-populated examples for guidance
- **Search Results**: AI-generated answers with source citations
- **Source Attribution**: Links back to original documents

### User Workflow

1. **Initial Setup**: Enter name in sidebar
2. **Document Upload**: 
   - Select files using file uploader
   - Click "Upload and Process"
   - Review extracted information
3. **Document Management**:
   - View all documents in organized list
   - Review document details and summaries
4. **Search and Query**:
   - Ask natural language questions
   - Review AI-generated responses
   - Check source documents for verification

## Database Schema

### Documents Table

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    category TEXT,
    document_date TEXT,
    doctor_name TEXT,
    hospital_name TEXT,
    summary TEXT,
    content TEXT
);
```

### Field Descriptions

- **id**: Unique document identifier
- **filename**: Original uploaded filename
- **category**: Document type (Prescription, Lab Report, Medical Bill, etc.)
- **document_date**: Date from document (YYYY-MM-DD format)
- **doctor_name**: Extracted doctor name
- **hospital_name**: Extracted hospital/clinic name
- **summary**: AI-generated document summary
- **content**: Full extracted text content

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Groq API key for AI processing | - | Yes |

### Application Settings

#### Backend Configuration (main.py)
```python
DATABASE = "medidoc.db"           # SQLite database file
UPLOAD_FOLDER = "uploads"         # File storage directory
BACKEND_URL = "http://127.0.0.1:8000"  # API base URL
```

#### Frontend Configuration (app.py)
```python
BACKEND_URL = "http://127.0.0.1:8000"   # Backend API URL
```

### Document Categories

The system automatically categorizes documents into:
- Prescription
- Lab Report
- Medical Bill
- Pharmacy Bill
- Discharge Summary
- Consultation Notes
- Other

## Usage Guide

### For End Users

#### Getting Started
1. Start the backend server: `python main.py`
2. Start the frontend: `streamlit run app.py`
3. Open http://localhost:8501 in your browser
4. Enter your name in the sidebar

#### Uploading Documents
1. Go to "Upload Documents" tab
2. Select one or more medical documents
3. Click "Upload and Process"
4. Review the extracted information
5. Repeat for additional documents

#### Searching Your Records
1. Go to "Search History" tab
2. Type a natural language question
3. Click "Search"
4. Review the AI-generated answer and sources

#### Example Search Queries
- "What was the result of my latest blood test?"
- "Show me all prescriptions from Dr. Smith"
- "What medications am I currently taking?"
- "When was my last visit to City Hospital?"
- "What were my cholesterol levels in the last test?"

### For Developers

#### Adding New Document Categories
Modify the system prompt in `process_with_llm()` function:
```python
system_prompt = """
# Add new categories to this list:
- "category": Choose from "Prescription", "Lab Report", "Medical Bill", "Pharmacy Bill", "Discharge Summary", "Consultation Notes", "New Category", "Other"
```

#### Customizing AI Processing
Adjust the Groq API parameters in `process_with_llm()`:
```python
completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",  # Model selection
    temperature=0.1,               # Response randomness
    max_tokens=300,                # Response length
    top_p=1,                      # Nucleus sampling
)
```

#### Adding New Endpoints
Follow FastAPI patterns:
```python
@app.get("/new-endpoint/")
def new_function():
    # Implementation
    return {"result": "data"}
```

## Troubleshooting

### Common Issues

#### Backend Won't Start
**Problem**: "Backend server is not running" error
**Solutions**:
1. Check if port 8000 is available
2. Verify Groq API key is set
3. Ensure all dependencies are installed
4. Check logs for specific error messages

#### OCR Not Working
**Problem**: "Could not extract text from the uploaded file"
**Solutions**:
1. Verify Tesseract is installed and in PATH
2. Check if image/PDF is readable
3. Try with a different file format
4. Ensure file is not corrupted

#### Database Errors
**Problem**: SQLite database connection issues
**Solutions**:
1. Check file permissions in the application directory
2. Ensure SQLite is available
3. Delete `medidoc.db` file to reset database
4. Verify disk space availability

#### Groq API Errors
**Problem**: AI processing failures
**Solutions**:
1. Verify API key is correct and active
2. Check internet connectivity
3. Monitor API rate limits
4. Review API documentation for changes

### Log Analysis

Enable detailed logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

Common log patterns:
- `INFO`: Normal operations
- `ERROR`: Failures requiring attention
- `WARNING`: Non-critical issues

### Performance Optimization

#### For Large Files
- Implement file size limits
- Add progress indicators
- Consider async processing for multiple files

#### For Many Documents
- Add pagination to document list
- Implement database indexing
- Consider full-text search optimization


### Recommended Production Changes
```python
# Update CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Development Notes

### Code Structure

#### Backend (main.py)
- **FastAPI Application**: RESTful API server
- **Database Operations**: SQLite CRUD operations
- **File Processing**: OCR and text extraction
- **AI Integration**: Groq API for document analysis

#### Frontend (app.py)
- **Streamlit Interface**: Multi-tab web application
- **API Communication**: HTTP requests to backend
- **User Interface**: Forms, file uploads, and result displays

### Extension Opportunities

#### Feature Enhancements
1. **User Authentication**: Multi-user support
2. **Document Versioning**: Track document updates
3. **Export Functionality**: PDF reports, CSV exports
4. **Advanced Search**: Filters, date ranges, categories
5. **Document Comparison**: Side-by-side analysis
6. **Appointment Scheduling**: Integration with calendar systems

#### Technical Improvements
1. **Async Processing**: Background task processing
2. **Caching**: Redis for improved performance
3. **Monitoring**: Health checks and metrics
4. **Testing**: Unit and integration tests
5. **Docker**: Containerization for deployment
6. **Cloud Deployment**: AWS, GCP, or Azure integration

### Contributing

#### Development Setup
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit pull request with documentation

#### Code Standards
- Follow PEP 8 for Python code
- Add docstrings for new functions
- Include error handling
- Update documentation for new features

