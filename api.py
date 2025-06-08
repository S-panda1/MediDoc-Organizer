from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from groq import Groq
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
DATABASE = "medidoc.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Groq Client Initialization ---
# Use environment variable for API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# --- Database Setup ---
def init_db():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT,
            document_date TEXT,
            doctor_name TEXT,
            hospital_name TEXT,
            summary TEXT,
            content TEXT
        )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

init_db()

# --- FastAPI App ---
app = FastAPI(title="MediDoc API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
def extract_text_from_file(filepath: str) -> str:
    """Extract text from PDF or image files"""
    try:
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return ""
            
        if filepath.lower().endswith(".pdf"):
            pages = convert_from_path(filepath)
            text = ""
            for page in pages:
                text += pytesseract.image_to_string(page) + "\n"
            return text.strip()
        else:
            # Handle image files
            with Image.open(filepath) as img:
                text = pytesseract.image_to_string(img)
            return text.strip()
            
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {e}")
        return ""

def process_with_llm(text: str) -> dict:
    """Analyze medical text using Groq's Llama model"""
    if not text.strip():
        return {
            "category": "Empty Document",
            "document_date": "N/A",
            "doctor_name": "N/A",
            "hospital_name": "N/A",
            "summary": "Document appears to be empty or text could not be extracted.",
        }
    
    system_prompt = """
    You are an expert medical data extraction assistant. Analyze the provided text from a medical document and extract key information.
    Respond ONLY with a valid JSON object containing exactly these keys:
    - "category": Choose from "Prescription", "Lab Report", "Medical Bill", "Pharmacy Bill", "Discharge Summary", "Consultation Notes", "Other"
    - "document_date": Date in YYYY-MM-DD format. If not found, use "N/A"
    - "doctor_name": Full name of the doctor. If not found, use "N/A"
    - "hospital_name": Name of hospital/clinic. If not found, use "N/A"
    - "summary": A brief, clear summary in 1-2 sentences describing what this document is about

    Return only the JSON object, no other text.
    """
    
    fallback_response = {
        "category": "Other",
        "document_date": "N/A",
        "doctor_name": "N/A",
        "hospital_name": "N/A",
        "summary": "Medical document processed but specific information could not be extracted.",
    }

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Medical document text:\n\n{text[:2000]}"}  # Limit text length
            ],
            temperature=0.1,
            max_tokens=300,
            top_p=1,
            stream=False,
        )
        
        response_content = completion.choices[0].message.content.strip()
        
        # Clean up the response
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        response_content = response_content.strip()
        
        parsed_response = json.loads(response_content)
        
        # Validate required keys
        required_keys = ["category", "document_date", "doctor_name", "hospital_name", "summary"]
        for key in required_keys:
            if key not in parsed_response:
                parsed_response[key] = "N/A"
        
        return parsed_response

    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {e}\nRaw Response: {response_content}")
        return fallback_response
    except Exception as e:
        logger.error(f"Error with Groq API: {e}")
        return fallback_response

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "MediDoc API is running"}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a medical document"""
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only PDF and image files are allowed")
        
        # Save uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(filepath, "wb") as buffer:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            buffer.write(content)
        
        logger.info(f"File saved: {filepath}")
        
        # Extract text
        text = extract_text_from_file(filepath)
        if not text.strip():
            # Clean up the file
            os.remove(filepath)
            raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file")

        # Process with LLM
        processed_data = process_with_llm(text)
        
        # Save to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO documents 
               (filename, category, document_date, doctor_name, hospital_name, summary, content) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                file.filename,
                processed_data.get("category", "N/A"),
                processed_data.get("document_date", "N/A"),
                processed_data.get("doctor_name", "N/A"),
                processed_data.get("hospital_name", "N/A"),
                processed_data.get("summary", "N/A"),
                text
            ),
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Document processed successfully: {file.filename}")
        return {"filename": file.filename, "info": processed_data, "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing the file")

@app.get("/documents/")
def get_documents():
    """Retrieve all processed documents"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, category, document_date, doctor_name, hospital_name, summary 
            FROM documents 
            ORDER BY 
                CASE WHEN document_date = 'N/A' THEN 1 ELSE 0 END,
                document_date DESC
        """)
        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve documents")

class SearchResult(BaseModel):
    answer: str
    sources: list

@app.get("/search/", response_model=SearchResult)
def search_medical_history(query: str):
    """Search through medical documents using natural language"""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT filename, content, summary, category FROM documents")
        all_docs = cursor.fetchall()
        conn.close()

        if not all_docs:
            return {"answer": "No documents have been uploaded yet. Please upload some medical documents first.", "sources": []}

        # Prepare context for the AI
        context_parts = []
        for i, doc in enumerate(all_docs):
            filename, content, summary, category = doc
            context_parts.append(f"Document {i+1}: {filename}\nCategory: {category}\nSummary: {summary}\nContent: {content[:1500]}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        system_prompt = f"""
        You are a medical assistant helping a patient understand their medical history. 
        Answer the user's question based ONLY on the provided medical documents.
        
        Guidelines:
        - Provide a clear, helpful answer
        - Mention specific document names when referencing information
        - If information is not available in the documents, say so clearly
        - Be concise but informative
        - Use medical terminology appropriately but explain complex terms
        
        Available Documents:
        {context}
        """

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.2,
            max_tokens=800,
        )
        
        answer = completion.choices[0].message.content
        
        # Find relevant sources mentioned in the answer
        sources = []
        for doc in all_docs:
            filename = doc[0]
            if filename.lower() in answer.lower():
                sources.append({
                    "filename": filename,
                    "summary": doc[2],
                    "category": doc[3]
                })
        
        return {"answer": answer, "sources": sources}
        
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail="Search service is currently unavailable")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
