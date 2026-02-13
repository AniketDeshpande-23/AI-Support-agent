from langchain_ollama import OllamaLLM, OllamaEmbeddings

# Shared LLM
llm = OllamaLLM(
    model="mistral",
    temperature=0.2,
    num_predict=150
)

# Shared embeddings
embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)
