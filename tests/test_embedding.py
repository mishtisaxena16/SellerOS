from ollama import Client

client = Client(host="http://localhost:11434")

print("Testing embedding model...")

response = client.embeddings(
    model="qwen3-embedding:0.6b",
    prompt="What is Amazon account health?"
)

print("Success!")
print(f"Embedding dimensions: {len(response['embedding'])}")