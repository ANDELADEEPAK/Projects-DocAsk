import chromadb
import hashlib
import time

from google.genai import types

from backend.embeddings import (
    create_embedding,
    client as gemini_client
)


# ChromaDB initialization

chroma_client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="docask_documents",
    metadata={"hnsw:space": "cosine"}
)


# Store document chunks

def store_chunks(chunks, filename):

    if not chunks:
        return 0

    # Remove previous chunks belonging to this filename

    collection.delete(
        where={"filename": filename}
    )

    batch_size = 50

    for start in range(0, len(chunks), batch_size):

        batch = chunks[start:start + batch_size]

        print(
            f"Generating embeddings for chunks "
            f"{start + 1} to {start + len(batch)}..."
        )

        start_time = time.time()

        # Batch embedding request

        response = gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=batch,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            )
        )

        print(
            "Embedding time:",
            round(time.time() - start_time, 2),
            "seconds"
        )

        embeddings = [
            item.values for item in response.embeddings
        ]

        ids = [
            hashlib.sha256(
                f"{filename}:{start + i}:{chunk}".encode()
            ).hexdigest()
            for i, chunk in enumerate(batch)
        ]

        metadatas = [
            {
                "filename": filename,
                "chunk_index": start + i
            }
            for i in range(len(batch))
        ]

        collection.upsert(
            ids=ids,
            documents=batch,
            embeddings=embeddings,
            metadatas=metadatas
        )

    print("All chunks stored successfully!")

    return len(chunks)


# Retrieve relevant chunks

def search_chunks(question, filename, top_k=2):

    print("Generating question embedding...")

    start_time = time.time()

    question_embedding = create_embedding(
        question,
        task_type="RETRIEVAL_QUERY"
    )

    print(
        "Question embedding time:",
        round(time.time() - start_time, 2),
        "seconds"
    )

    existing = collection.get(
        where={"filename": filename},
        include=["metadatas"]
    )

    total_chunks = len(existing["ids"])

    if total_chunks == 0:
        return []

    print("Searching ChromaDB...")

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(top_k, total_chunks),
        where={"filename": filename}
    )

    return results["documents"][0]


# Generate answer

def generate_answer(question, filename):

    print("Retrieving relevant information...")

    documents = search_chunks(
        question,
        filename,
        top_k=2
    )

    if not documents:

        return "No relevant information found in this document."

    context = "\n\n".join(documents)

    prompt = f"""
You are DocAsk, an AI document assistant.

Answer the question using ONLY the supplied document context.

Rules:
1. Give accurate and clear answers.
2. Do not invent information.
3. If the answer is missing, say it is not available
   in the uploaded document.

DOCUMENT CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    print("Generating answer using Gemini...")

    start_time = time.time()

    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=512
        )
    )

    print(
        "Gemini generation time:",
        round(time.time() - start_time, 2),
        "seconds"
    )

    return response.text