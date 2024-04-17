import pytest
from langchain.llms.fake import FakeListLLM
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.document_loaders import WebBaseLoader


def test_qa_agent():
    from agents import QaAgent

    llm = FakeListLLM(name="fakeGPT", responses=["I am fine, thank you!"])

    embeddings_provider = FakeEmbeddings(size=10)
    loader = WebBaseLoader("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8264982/")
    docs = loader.load()  # load parse text

    qa = QaAgent(docs, llm, embeddings_provider)
    answer = qa.answer("Test question?")

    assert answer == "I am fine, thank you!"


def test_smiles_filter_agent():
    from agents import SmilesFilterAgent

    smiles_filter = SmilesFilterAgent()
    smiles_tokens = smiles_filter.filter("blabla bla ADFAD C1=CC=CC=C1")
    assert smiles_tokens == ["C1=CC=CC=C1"]


if __name__ == "__main__":
    pytest.main([__file__])
