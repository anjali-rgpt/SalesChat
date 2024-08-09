import os
import config

from langchain.indexes import VectorstoreIndexCreator
from langchain_community.utilities import ApifyWrapper
from langchain_core.document_loaders.base import Document
from langchain_openai import OpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

os.environ["OPENAI_API_KEY"] = config.open_ai_key
os.environ["APIFY_API_TOKEN"] = config.apify_token

apify = ApifyWrapper()

loader = apify.call_actor(
    actor_id = "apify/website-content-crawler",
    run_input={"startUrls": [{"url": "https://www.artisan.co"}], "maxCrawlPages": 10, "crawlerType": "cheerio"},
    dataset_mapping_function=lambda item: Document(
        page_content=item["text"] or "", metadata={"source": item["url"]}
    ),
)

index = VectorstoreIndexCreator(embedding=OpenAIEmbeddings()).from_loaders([loader])

query = "I need some help with setting up my campaign."
result = index.query_with_sources(query, llm=OpenAI())

print("answer:", result["answer"])
print("source:", result["sources"])

