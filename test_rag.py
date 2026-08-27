from langchain_groq import ChatGroq
from src import rag_engine, config

llm = ChatGroq(
    model=config.GROQ_MODEL,
    groq_api_key=config.GROQ_API_KEY,
    temperature=0.0,
)

while True:
    query = input("\nEnter question (or 'q' to quit): ").strip()
    if not query or query.lower() in ["q", "exit", "quit"]:
        break

    context = rag_engine.retrieve_context(query, top_k=3)
    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    
    response = llm.invoke(prompt)
    print("\nAnswer:\n", response.content)
