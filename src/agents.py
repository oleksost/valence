import os
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
import backoff
from rdkit import Chem
import concurrent.futures


class QaAgent:
    """
    Question-Answering Agent that uses a language model and document embeddings for retrieval-based QA.

    Args:
        documents (list): List of documents to be used for retrieval.
        llm (LanguageModel): Language model used for generating responses.
        embeddings_provider (EmbeddingsProvider): Embeddings provider used for document embeddings.
        n_docs (int, optional): Number of documents to be used for retrieval. Defaults to 10.
    """

    def __init__(
        self, documents, llm, embeddings_provider, doc_limit = None, vector_path=None) -> None:
        # check if file exists
        if vector_path and os.path.exists(vector_path):
            self.vector = FAISS.load_local(
                vector_path, embeddings_provider, allow_dangerous_deserialization=True
            )
        else:
            text_splitter = RecursiveCharacterTextSplitter()
            documents = text_splitter.split_documents(documents)
            if doc_limit:
                documents = documents[:doc_limit]
            self.vector = FAISS.from_documents(
                documents, embedding=embeddings_provider
            )
            if vector_path:
                self.vector.save_local(vector_path)

        prompt_template = """Answer the following question based only on the provided context:
                            <context>
                            {context}
                            </context>
                            Question: {input}"""
        prompt = ChatPromptTemplate.from_template(prompt_template)

        self.chain = create_stuff_documents_chain(
            llm, prompt
        )  # chain the LLM to the prompt
        retriever = self.vector.as_retriever()
        self.retrieval_chain = create_retrieval_chain(retriever, self.chain)

    def answer(self, question):
        """
        Answer a given question based on the provided context.

        Args:
            question (str): The question to be answered.

        Returns:
            str: The answer to the question.
        """
        response = self.retrieval_chain.invoke({"input": question})
        return response["answer"]


class SmilesFilterAgent:
    """A class for filtering SMILES strings."""

    def __init__(self):
        pass

    def _is_valid_smiles(self, token):
        """Check if the token is a valid SMILES string."""
        return token if Chem.MolFromSmiles(token) else None

    def filter(self, text):
        """Filter out invalid SMILES strings from the given text.

        Args:
            text (str): The input text containing SMILES strings.

        Returns:
            list: A list of valid SMILES strings.
        """
        tokens = text.split()
        smiles_tokens = []

        # Use a multiprocessing pool to process tokens in parallel
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Map the function over all tokens and filter out None results
            results = executor.map(self._is_valid_smiles, tokens)
            smiles_tokens = [result for result in results if result is not None]

        return smiles_tokens
