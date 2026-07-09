import chromadb
from embedding import get_embedding

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    "selleros_docs"
)

def semantic_search(query, top_k=5):

    print("\nSEARCH QUERY:")
    print(repr(query))

    query_embedding = get_embedding(query)

    if query_embedding is None:
        raise Exception("Embedding generation failed.")

    print("Embedding length:", len(query_embedding))

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results

def metadata_search(
    query,
    file_name,
    top_k=5
):

    query_embedding = get_embedding(
        query
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "source": file_name
        }
    )

    return results


import requests

def generate_answer(
    question,
    contexts
):
    context = "\n\n".join(contexts)
    prompt = f"""You are SellerOS, an AI assistant for Indian marketplace sellers.
    You must answer ONLY from the Knowledge Base provided below.
    -------------------------
    Knowledge Base
    -------------------------
    {context}
    -------------------------
      User Question
    -------------------------
    {question}
    Rules:
    1. Use ONLY the Knowledge Base and never invent information.
    2. Summarize the information instead of copying it.
    3. Use bullet points whenever appropriate.
    4. If there are steps, present them as a numbered list.
    5. Keep the answer concise (maximum 8 bullet points).
    6. Mention important documents, eligibility, timelines, or requirements if present.
    7. If the Knowledge Base does not contain the answer, reply exactly:
    I couldn't find this information in the SellerOS knowledge base.
    Answer:
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":"llama3.2:1b",
                "prompt": prompt,
                "stream":False
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception:
        return "Sorry, I couldn't generate an answer right now."
