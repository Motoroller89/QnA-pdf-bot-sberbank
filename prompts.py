from langchain.prompts import PromptTemplate

template = """Given the following extracted parts of a long document and a question.
The entire document is the 2022 Annual Report of SberBank. 
Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Answers in Russian.

QUESTION: {question}
=========
{summaries}
=========
FINAL ANSWER:"""

PROMPT = PromptTemplate(
    template=template, input_variables=["summaries", "question"]
)

EXAMPLE_PROMPT = PromptTemplate(
    template="Content: {page_content}\nPage: {page_number}",
    input_variables=["page_content", "page_number"],
)
