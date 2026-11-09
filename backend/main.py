# from fastapi import FastAPI
# from pydantic import BaseModel
# # from fastapi import File, UploadFile
# from fastapi import File, UploadFile
# import shutil
# import os
# from backend.document import extract_text
# from backend.document import extract_text, chunk_text
# from backend.rag import store_chunks
# from backend.rag import store_chunks, generate_answer



# app = FastAPI()



# class Question(BaseModel):
#     question: str
#     filename: str

# # @app.post("/ask")
# # def ask_question(data: Question):
# #     return {
# #         "received_question": data.question,
# #         "message": "Question received successfully"
# #     }

# # @app.post("/ask")
# # def ask_question(data: Question):

# #     answer = generate_answer(data.question)

# #     return {
# #         "question": data.question,
# #         "answer": answer
# #     }
# @app.post("/ask")
# def ask_question(data: Question):

#     answer = generate_answer(
#         data.question,
#         data.filename
#     )

#     return {
#         "question": data.question,
#         "filename": data.filename,
#         "answer": answer
#     }




# @app.get("/")
# def home():
#     return {"message": "Welcome to DocAsk - AI Document Assistant"}

# @app.get("/health")
# def health():
#     return {"status": "healthy"}

# @app.get("/info")
# def info():
#     return {
#         "project": "DocAsk",
#         "description": "AI-powered PDF Question Answering System",
#         "version": "1.0"
#     }




# # @app.post("/upload")
# # def upload_pdf(file: UploadFile = File(...)):

# #     file_path = f"data/{file.filename}"

# #     with open(file_path, "wb") as buffer:
# #         shutil.copyfileobj(file.file, buffer)

# #     return {
# #         "filename": file.filename,
# #         "message": "PDF uploaded successfully"
# #     }

# # @app.post("/upload")
# # def upload_pdf(file: UploadFile = File(...)):
# #     file_path = f"data/{file.filename}"

# #     with open(file_path, "wb") as buffer:
# #         shutil.copyfileobj(file.file, buffer)

# #     extracted_text = extract_text(file_path)

# #     return {
# #         "filename": file.filename,
# #         "message": "PDF uploaded and text extracted successfully",
# #         "characters": len(extracted_text),
# #         "preview": extracted_text[:300]
# #     }


# # @app.post("/upload")
# # def upload_pdf(file: UploadFile = File(...)):
# #     file_path = f"data/{file.filename}"

# #     with open(file_path, "wb") as buffer:
# #         shutil.copyfileobj(file.file, buffer)

# #     extracted_text = extract_text(file_path)

# #     chunks = chunk_text(extracted_text)

# #     return {
# #         "filename": file.filename,
# #         "message": "PDF uploaded, text extracted and chunked successfully",
# #         "characters": len(extracted_text),
# #         "total_chunks": len(chunks),
# #         "first_chunk": chunks[0] if chunks else ""
# #     }

# @app.post("/upload")
# def upload_pdf(file: UploadFile = File(...)):

#     file_path = f"data/{file.filename}"

#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     extracted_text = extract_text(file_path)

#     chunks = chunk_text(extracted_text)

#     total_records = store_chunks(chunks, file.filename)

#     return {
#         "filename": file.filename,
#         "message": "PDF uploaded and stored successfully",
#         "characters": len(extracted_text),
#         "total_chunks": len(chunks),
#         "total_records_in_database": total_records
#     }


from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from pathlib import Path
import shutil

from backend.document import extract_text, chunk_text
from backend.rag import store_chunks, generate_answer


app = FastAPI(
    title="DocAsk API",
    description="AI-powered PDF Question Answering System",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Create data directory if it doesn't exist

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


# Home API

@app.get("/")
def home():

    return {
        "message": "Welcome to DocAsk - AI Document Assistant"
    }


# Health API

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# Project information API

@app.get("/info")
def info():

    return {
        "project": "DocAsk",
        "description": "AI-powered PDF Question Answering System",
        "version": "1.0"
    }


# Question model

class Question(BaseModel):

    question: str
    filename: str


# Upload PDF API

@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid PDF file."
        )

    filename = Path(file.filename).name
    file_path = DATA_DIR / filename

    try:

        # Save uploaded PDF

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        print("Extracting PDF text...")

        # Extract text

        extracted_text = extract_text(str(file_path))

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in this PDF."
            )

        print("Creating chunks...")

        # Split text into chunks

        chunks = chunk_text(extracted_text)

        print("Storing embeddings...")

        # Store chunks in ChromaDB

        total_records = store_chunks(
            chunks,
            filename
        )

        return {
            "filename": filename,
            "message": "PDF uploaded and processed successfully",
            "characters": len(extracted_text),
            "total_chunks": len(chunks),
            "total_records_in_database": total_records
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        file.file.close()


# Ask question API

@app.post("/ask")
def ask_question(data: Question):

    try:

        answer = generate_answer(
            data.question,
            data.filename
        )

        return {
            "question": data.question,
            "filename": data.filename,
            "answer": answer
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
