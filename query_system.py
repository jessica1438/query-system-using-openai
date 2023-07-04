# -*- coding: utf-8 -*-
"""Query System.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EbFP36UoIJJrFRsC40UjW9M6g21oi6PP
"""

!pip install --upgrade langchain openai -q
!pip install unstructured -q
!pip install unstructured[local-inference] -q
!pip install detectron2@git+https://github.com/facebookresearch/detectron2.git@v0.6#egg=detectron2 -q
!apt-get install poppler-utils

import os
import openai
from langchain.vectorstores import pinecone
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from openai.embeddings_utils import get_embedding
from tqdm import tqdm
import docx

!pip install openai pinecone-client python-docx

pip install --upgrade pillow==6.2.2

from google.colab import drive
drive.mount('/content/drive', force_remount=True)

docs_path = "/content/drive/My Drive/test"

import os
os.chdir("/content/drive/My Drive/test")
!ls

chunks=[]
for files in os.listdir(docs_path):
  document_path=os.path.join(docs_path,files)
  doc=docx.Document(document_path)
  print(document_path)
  for para in doc.paragraphs:
    chunks.append(para.text)

len(chunks)

print(chunks[2])

text_chunks = [string.strip().strip('\n') for string in chunks if len(string.split()) >= 10 ]

openai.api_key = "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"

embeddigns = []
for chunk in text_chunks:
  embedding = get_embedding(chunk, engine='text-embedding-ada-002')
  embeddigns.append({"text": chunk, "embedding": embedding})

len(embeddigns)

!pip install pinecone-client -q

import pinecone
pinecone.init(
    api_key="cd2a5fe1-d36c-4090-82aa-5f7de92a314b",
    environment="us-west1-gcp-free"
)

index_name = "model"

index = pinecone.Index(index_name)

for i in range(0, len(embeddigns), 64):
    data_batch = embeddigns[i: i+64]
    i_end = min(i+64, len(embeddigns))
    text_batch = [item['text'] for item in data_batch]
    ids_batch = [str(n) for n in range(i, i_end)]
    embeds = [item['embedding'] for item in data_batch]
    meta = [{'text': text_batch} for text_batch in zip(text_batch)] # you can add more fields here
    to_upsert = zip(ids_batch, embeds, meta)
    index.upsert(vectors=list(to_upsert))

def search_docs(query):
  xq = openai.Embedding.create(input=query, engine="text-embedding-ada-002")['data'][0]['embedding']
  res = index.query([xq], top_k=5, include_metadata=True)
  chosen_text = []
  for match in res['matches']:
    chosen_text = match['metadata']
  return res['matches']

def construct_prompt(query):
  matches = search_docs(query)

  chosen_text = []
  for match in matches:
    chosen_text.append(str(match['metadata']['text']))
  prompt += "Context: " + "\n".join(chosen_text)
  prompt += "Question: " + query
  prompt += "Answer: "
    return prompt


def answer_question(query):
  prompt = construct_prompt(query)
  res = openai.Completion.create(
      prompt=prompt,
      model="text-davinci-003",
      max_tokens=500,
      temperature=0.0,
  )

  return res.choices[0].text

print(answer_question("where is usa"))

