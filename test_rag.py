from langchain_groq import ChatGroq
from src import rag_engine, config

llm = ChatGroq(model=config.GROQ_MODEL, groq_api_key=config.GROQ_API_KEY)

while True:
    query = input("\nQuery: ").strip()
    if not query or query.lower() in ["q", "exit", "quit"]:
        break

    context = rag_engine.retrieve_context(query)
    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    print("\n", llm.invoke(prompt).content)
