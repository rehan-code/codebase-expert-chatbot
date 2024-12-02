# -*- coding: utf-8 -*-
"""Codebase_RAG_Completed.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/github/team-headstart/CodebaseRAG/blob/main/Codebase_RAG_Completed.ipynb

![Img](https://app.theheadstarter.com/static/hs-logo-opengraph.png)

# Headstarter Codebase RAG Project

![Screenshot 2024-11-25 at 7 12 58 PM](https://github.com/user-attachments/assets/0bd67cf0-43d5-46d2-879c-a752cae4c8e3)

# Install Necessary Libraries
"""

# ! pip install pygithub langchain langchain-community openai tiktoken pinecone-client langchain_pinecone sentence-transformers

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_pinecone import PineconeVectorStore
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
# from google.colab import userdata
from pinecone import Pinecone
import os
import tempfile
from github import Github, Repository
from git import Repo
from openai import OpenAI
from pathlib import Path
from langchain.schema import Document
from pinecone import Pinecone

"""# Clone a GitHub Repo locally"""

def clone_repository(repo_url):
    """Clones a GitHub repository to a temporary directory.

    Args:
        repo_url: The URL of the GitHub repository.

    Returns:
        The path to the cloned repository.
    """
    repo_name = repo_url.split("/")[-1]  # Extract repository name from URL
    repo_path = f"/content/{repo_name}"
    Repo.clone_from(repo_url, str(repo_path))
    return str(repo_path)

# path = clone_repository("https://github.com/CoderAgent/SecureAgent")
path = "content/SecureAgent"

# print(path)

SUPPORTED_EXTENSIONS = {'.py', '.js', '.tsx', '.jsx', '.ipynb', '.java',
                         '.cpp', '.ts', '.go', '.rs', '.vue', '.swift', '.c', '.h'}

IGNORED_DIRS = {'node_modules', 'venv', 'env', 'dist', 'build', '.git',
                '__pycache__', '.next', '.vscode', 'vendor'}

def get_file_content(file_path, repo_path):
    """
    Get content of a single file.

    Args:
        file_path (str): Path to the file

    Returns:
        Optional[Dict[str, str]]: Dictionary with file name and content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get relative path from repo root
        rel_path = os.path.relpath(file_path, repo_path)

        return {
            "name": rel_path,
            "content": content
        }
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return None


def get_main_files_content(repo_path: str):
    """
    Get content of supported code files from the local repository.

    Args:
        repo_path: Path to the local repository

    Returns:
        List of dictionaries containing file names and contents
    """
    files_content = []

    try:
        for root, _, files in os.walk(repo_path):
            # Skip if current directory is in ignored directories
            if any(ignored_dir in root for ignored_dir in IGNORED_DIRS):
                continue

            # Process each file in current directory
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.splitext(file)[1] in SUPPORTED_EXTENSIONS:
                    file_content = get_file_content(file_path, repo_path)
                    if file_content:
                        files_content.append(file_content)

    except Exception as e:
        print(f"Error reading repository: {str(e)}")

    return files_content

file_content = get_main_files_content(path)

# file_content

"""# Embeddings"""

def get_huggingface_embeddings(text, model_name="sentence-transformers/all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)
    return model.encode(text)

# text = "I am a programmer"

# embeddings = get_huggingface_embeddings(text)

# embeddings



"""# Setting up Pinecone
**1. Create an account on [Pinecone.io](https://app.pinecone.io/)**

**2. Create a new index called "codebase-rag" and set the dimensions to 768. Leave the rest of the settings as they are.**

![Screenshot 2024-11-24 at 10 58 50 PM](https://github.com/user-attachments/assets/f5fda046-4087-432a-a8c2-86e061005238)



**3. Create an API Key for Pinecone**

![Screenshot 2024-11-24 at 10 44 37 PM](https://github.com/user-attachments/assets/e7feacc6-2bd1-472a-82e5-659f65624a88)


**4. Store your Pinecone API Key within Google Colab's secrets section, and then enable access to it (see the blue checkmark)**

![Screenshot 2024-11-24 at 10 45 25 PM](https://github.com/user-attachments/assets/eaf73083-0b5f-4d17-9e0c-eab84f91b0bc)


"""

# Set the PINECONE_API_KEY as an environment variable
# pinecone_api_key = userdata.get("PINECONE_API_KEY")
# os.environ['PINECONE_API_KEY'] = pinecone_api_key

# Initialize Pinecone
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"),)

# Connect to your Pinecone index
pinecone_index = pc.Index("codebase-chatbot")

vectorstore = PineconeVectorStore(index_name="codebase-chatbot", embedding=HuggingFaceEmbeddings())

documents = []

for file in file_content:
    doc = Document(
        page_content=f"{file['name']}\n{file['content']}",
        metadata={"source": file['name']}
    )

    documents.append(doc)


vectorstore = PineconeVectorStore.from_documents(
    documents=documents,
    embedding=HuggingFaceEmbeddings(),
    index_name="codebase-chatbot",
    namespace="https://github.com/CoderAgent/SecureAgent"
)



"""# Perform RAG

1. Get your Groq API Key [here](https://console.groq.com/keys)

2. Paste your Groq API Key into your Google Colab secrets, and make sure to enable permissions for it

![Screenshot 2024-11-25 at 12 00 16 AM](https://github.com/user-attachments/assets/e5525d29-bca6-4dbd-892b-cc770a6b281d)

"""

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

# query = "How are python files parsed?"

# raw_query_embedding = get_huggingface_embeddings(query)

# raw_query_embedding

# # Feel free to change the "top_k" parameter to be a higher or lower number
# top_matches = pinecone_index.query(vector=raw_query_embedding.tolist(), top_k=5, include_metadata=True, namespace="https://github.com/CoderAgent/SecureAgent")

# top_matches

# contexts = [item['metadata']['text'] for item in top_matches['matches']]

# contexts

# augmented_query = "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[ : 10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query

# print(augmented_query)

# system_prompt = f"""You are a Senior Software Engineer, specializing in TypeScript.

# Answer any questions I have about the codebase, based on the code provided. Always consider all of the context provided when forming a response.
# """

# llm_response = client.chat.completions.create(
#     model="llama-3.1-70b-versatile",
#     messages=[
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": augmented_query}
#     ]
# )

# response = llm_response.choices[0].message.content

# response



"""# Putting it all together"""

def perform_rag(query):
    raw_query_embedding = get_huggingface_embeddings(query)

    top_matches = pinecone_index.query(vector=raw_query_embedding.tolist(), top_k=5, include_metadata=True, namespace="https://github.com/CoderAgent/SecureAgent")

    # Get the list of retrieved texts
    contexts = [item['metadata']['text'] for item in top_matches['matches']]

    augmented_query = "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[ : 10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query
    print(augmented_query)
    # Modify the prompt below as need to improve the response quality
    system_prompt = f"""You are a Senior Software Engineer, specializing in TypeScript.

    Answer any questions I have about the codebase, based on the code provided. Always consider all of the context provided when forming a response.
    """

    llm_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": augmented_query}
        ]
    )

    return llm_response.choices[0].message.content

# response = perform_rag("How is the javascript parser used?")

# print(response)



