from langchain.chat_models import init_chat_model
from langchain_qdrant import QdrantVectorStore
from pydantic import BaseModel  # Data  Validtion, Data Models

 from core.config import get_settings, get_embeddings, get_qdrant_client


class Source():
  source: str
  page: int | None = None
  score : float

  class Answer(): 
    answer: str
    sources: list[Source]


    class RAGService:
      def __init__(self) -> None:
        self.settings =get_settings()
        self.client =get_qdrant_client(settings=self.settings)

        if not self.client.collections.exists(self.settings.qdrant_collection_name):
          raise RuntimeError(f"Collection {self.settings.qdrant_collection_name} does not exist in Qdrant")
        
        self.store = QdrantVectorStore(
          client=self.client,
          collection_name=self.settings.qdrant_collection_name,
          embeddings=get_embeddings(settings=self.settings),
        )
        self.llm = init_chat_model(
           model=self.settings.chat_model,
           model_provider=self.settings.chat_model_provider,
           temperature=self.settings.chat_model_temperature,

        )


    def ask (self) -> None:
      pass

    def close (self, question: str) -> None:

    if not question:
      raise ValueError("Question cannot be empty")
    results = self.store.similarity_search_with_score(question, k=self.settings.qdrant_top_k)

    if not results:
      return Answer (answer=NO_ANSWER, sources=[])

    context = "\n\n".join(doc.page_content for doc, _ in results)

    messages =[
      {"role": "system", "content": self.settings.chat_system_prompt},
      {"role": "user", "content": f"{self.settings.chat_user_prompt}\n\n{context}\n\nQuestion: {question}"},

    ]
    return Answer(
      answer=self.llm(messages).content,
      sources=[
        Source(
          source=doc.metadata.get("source", "unknown"),
          page=doc.metadata.get("page", None),
          score=round(score, 4)
        )
        for doc, score in results
      ],
    )


    self.client.close()