# Langchain Web Scraping Q & A tutorial over specific website

import os
import config

from langchain.indexes import VectorstoreIndexCreator
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.utilities import ApifyWrapper
from langchain_core.document_loaders.base import Document
from langchain_openai import OpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

from scraper import scrape_dynamic_content

os.environ["OPENAI_API_KEY"] = config.open_ai_key
os.environ["APIFY_API_TOKEN"] = config.apify_token

URL = "https://www.artisan.co"

def create_index(url = URL):
    """For specific url, call Apify to crawl the web"""
    apify = ApifyWrapper()

    loader = apify.call_actor(
        actor_id = "apify/website-content-crawler",
        run_input={"startUrls": [{"url": URL}], "maxCrawlPages": 20,  "crawlerType": "cheerio"},
        dataset_mapping_function=lambda item: Document(
            page_content=item["text"] or "", metadata={"source": item["url"]}
        ),
    )

    # Custom script for artisan to retrieve dynamic content 
    home_page_dynamic = scrape_dynamic_content(URL)
    
    # Add crawled data to dynamic scraped data
    documents_all = loader.load()
    documents_all.extend(home_page_dynamic)
    
    # Split and embed documents, store in FAISS datastore for easy access
    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(documents_all)
    embeddings = OpenAIEmbeddings(model = "text-embedding-3-small")

    vectorstore = FAISS.from_documents(documents, embeddings)

    vectorstore.save_local("vector_store")

    print("Saved")



