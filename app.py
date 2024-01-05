import chainlit as cl

from langchain.retrievers import ParentDocumentRetriever
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.storage._lc_store import create_kv_docstore
from langchain.storage import LocalFileStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.retrievers.multi_vector import SearchType

from prompts import EXAMPLE_PROMPT, PROMPT

from dotenv import load_dotenv 
import os

load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")


def create_retriever():
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

    vectorstore = Chroma(
        collection_name="full_documents", embedding_function=OpenAIEmbeddings(),persist_directory="db/vector_store"
    )

    fs = LocalFileStore("db/chroma_db_filestore")
    store = create_kv_docstore(fs)

    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
    )

    retriever.search_type = SearchType.similarity
    retriever.search_kwargs= {"k": 6}

    return retriever

@cl.on_chat_start
async def on_chat_start():
    retriver = create_retriever()
    
    llm = ChatOpenAI(
        model="gpt-3.5-turbo-16k-0613", temperature=0, streaming=True
    )
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriver,
        chain_type_kwargs={"prompt": PROMPT, "document_prompt": EXAMPLE_PROMPT},
        return_source_documents=True,
    )

    cl.user_session.set("chain", chain)

@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")  
    response = await chain.acall(
        message.content,
        callbacks=[cl.AsyncLangchainCallbackHandler(stream_final_answer=True)],
    )

    answer = response["answer"]
    source_elements = []
    found_page = []

    for doc in response['source_documents']:
        page_content = doc.page_content
        page_number = doc.metadata['page_number']

        source_elements.append(cl.Text(content=page_content, name=page_number))
        found_page.append(page_number)

    if found_page:
            answer += f"\nPages: {', '.join(map(str, found_page))}"
    else:
        answer += "\nNo Pages found"


    await cl.Message(content=answer, elements=source_elements).send()