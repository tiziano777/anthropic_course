# Retriever implementation

import random, string, json
from typing import Any, List, Dict, Tuple, Protocol, Optional, Callable

from chat_template.chat_functions import chat, add_user_message, add_assistant_message, text_from_message

# Reranker function
def reranker_fn(docs, query_text, k):
    joined_docs = "\n".join(
        [
            f"""
        <document>
        <document_id>{doc["id"]}</document_id>
        <document_content>{doc["content"]}</document_content>
        </document>
        """
            for doc in docs
        ]
    )

    prompt = f"""
    You are about to be given a set of documents, along with an id of each.
    Your task is to select and sort the {k} most relevant documents to answer the user's question.

    Here is the user's question:
    <question>
    {query_text}
    </question>
    
    Here are the documents to select from:
    <documents>
    {joined_docs}
    </documents>

    Respond in the following format:
    ```json
    {{
        "document_ids": str[] # List document ids, {k} elements long, sorted in order of decreasing relevance to the user's query. The most relevant documents should be listed first.
    }}
    ```
    """

    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")

    result = chat(messages, stop_sequences=["```"])

    # Note: updated to use 'text_from_message' helper fn
    return json.loads(text_from_message(result))["document_ids"]
    

# TYPING FUNCTIONAL PROTOCOL FOR INDEXES
class SearchIndex(Protocol):
    def add_document(self, document: Dict[str, Any]) -> None: ...
    def add_documents(self, documents: List[Dict[str, Any]]) -> None: ...
    def search(
        self, query: Any, k: int = 1
    ) -> List[Tuple[Dict[str, Any], float]]: ...



class Retriever:
    def __init__(
        self,
        *indexes: SearchIndex,
        reranker_fn: Optional[
            Callable[[List[Dict[str, Any]], str, int], List[str]]
        ] = reranker_fn,
    ):
        if len(indexes) == 0:
            raise ValueError("At least one index must be provided")
        self._indexes = list(indexes)
        self._reranker_fn = reranker_fn

    def add_document(self, document: Dict[str, Any]):
        if "id" not in document:
            document["id"] = "".join(
                random.choices(string.ascii_letters + string.digits, k=4)
            )

        for index in self._indexes:
            index.add_document(document)

    # Added the 'add_documents' method to avoid rate limiting errors from VoyageAI
    def add_documents(self, documents: List[Dict[str, Any]]):
        for index in self._indexes:
            index.add_documents(documents)

    def search(
        self, query_text: str, k: int = 1, k_rrf: int = 60
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not isinstance(query_text, str):
            raise TypeError("Query text must be a string.")
        if k <= 0:
            raise ValueError("k must be a positive integer.")
        if k_rrf < 0:
            raise ValueError("k_rrf must be non-negative.")

        all_results = [
            index.search(query_text, k=k * 5) for index in self._indexes
        ]

        doc_ranks = {}
        for idx, results in enumerate(all_results):
            for rank, (doc, _) in enumerate(results):
                doc_id = id(doc)
                if doc_id not in doc_ranks:
                    doc_ranks[doc_id] = {
                        "doc_obj": doc,
                        "ranks": [float("inf")] * len(self._indexes),
                    }
                doc_ranks[doc_id]["ranks"][idx] = rank + 1

        def calc_rrf_score(ranks: List[float]) -> float:
            return sum(1.0 / (k_rrf + r) for r in ranks if r != float("inf"))

        scored_docs: List[Tuple[Dict[str, Any], float]] = [
            (ranks["doc_obj"], calc_rrf_score(ranks["ranks"]))
            for ranks in doc_ranks.values()
        ]

        filtered_docs = [
            (doc, score) for doc, score in scored_docs if score > 0
        ]
        filtered_docs.sort(key=lambda x: x[1], reverse=True)

        result = filtered_docs[:k]

        if self._reranker_fn is not None:
            docs_only = [doc for doc, _ in result]

            for doc in docs_only:
                if "id" not in doc:
                    doc["id"] = "".join(
                        random.choices(
                            string.ascii_letters + string.digits, k=4
                        )
                    )

            doc_lookup = {doc["id"]: doc for doc in docs_only}
            reranked_ids = self._reranker_fn(docs_only, query_text, k)

            new_result = []
            original_scores = {id(doc): score for doc, score in result}

            for doc_id in reranked_ids:
                if doc_id in doc_lookup:
                    doc = doc_lookup[doc_id]
                    score = original_scores.get(id(doc), 0.0)
                    new_result.append((doc, score))

            result = new_result

        return result
