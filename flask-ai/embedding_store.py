from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama


from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.llms import Ollama
from llama_index.core.text_splitter import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from dotenv import load_dotenv
import os

# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")

import re

def format_response_for_browser(response_text):
    lines = response_text.strip().split('\n')
    formatted = []

    for line in lines:
        stripped = line.strip()

        # Numbered sections
        if re.match(r'^\d+\.\s+.+', stripped):
            formatted.append(f'<p style="margin-top: 1em;"><strong>🔹 {stripped}</strong></p>')
        # Headers
        elif stripped.startswith("##") or stripped.endswith(":"):
            clean = stripped.strip("# ").rstrip(":")
            formatted.append(f'<h3 style="color:#1e88e5;">{clean}</h3>')
        # Bullets
        elif stripped.startswith("*") or stripped.startswith("-"):
            formatted.append(f'<li>{stripped[1:].strip()}</li>')
        # Normal paragraph
        else:
            formatted.append(f'<p>{stripped}</p>')

    # Wrap <li> in <ul> if any
    html_output = []
    in_list = False
    for line in formatted:
        if line.startswith("<li>") and not in_list:
            html_output.append("<ul>")
            in_list = True
        elif not line.startswith("<li>") and in_list:
            html_output.append("</ul>")
            in_list = False
        html_output.append(line)
    if in_list:
        html_output.append("</ul>")

    return "\n".join(html_output)


def embed_and_search(docs, question):
    # 1. Set up the embedding model
    embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    # Settings.llm = Ollama(model="llama3")
    Settings.embed_model = embed_model
    llm = llm = Ollama(model="gemma:2b", request_timeout=300, temperature=0.3, streaming=False)

    Settings.llm = llm
    Settings.text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)

    # 2. Service context
    # service_context = ServiceContext.from_defaults(
    #     embed_model=embed_model,
    #     text_splitter=SentenceSplitter(chunk_size=512, chunk_overlap=50),
    # )

    # 3. Create the index
    index = VectorStoreIndex.from_documents(docs)
    

    # 4. Create a retriever-based query engine
    retriever = index.as_retriever(similarity_top_k=4)
    concise_question = f"{question.strip()} Explain neatly in a length that is suitable for the question, so that a beginner can understand. The main goal is making a user ready to work with this repo. Use the necessary files to answer this. If it is about the entire repository, refer all the files in the repository and answer. If asked for workflow or any similar question explain with the help of all files, including all the functionalities and features and how they work together."

    query_engine = RetrieverQueryEngine.from_args(retriever)
    print(f"Concise question: {concise_question}")

    # 5. Query the index
    response = query_engine.query(concise_question)
    formatted_response = format_response_for_browser(str(response))

    return str(response)


def synthesize_project_summary(docs):
    """
    Generate a basic summary and feature list from filenames, folder names, and code comments
    as a fallback if embeddings-based search returns poor/no results.
    """
    from collections import Counter

    file_names = [doc.metadata.get('file_path', '') for doc in docs]
    main_files = [fn for fn in file_names if os.path.basename(fn).lower() in ['app.js', 'main.py', 'index.js', 'server.js', 'index.py']]
    config_files = [fn for fn in file_names if os.path.basename(fn).lower() in ['package.json', 'requirements.txt', 'pyproject.toml']]
    test_files = [fn for fn in file_names if 'test' in os.path.basename(fn).lower()]
    src_files = [fn for fn in file_names if fn.startswith('src/') or fn.startswith('src\\')]
    doc_files = [fn for fn in file_names if os.path.splitext(fn)[1] in ['.md', '.rst', '.txt']]

    # Heuristic: count file types
    ext_counter = Counter(os.path.splitext(f)[1] for f in file_names)

    summary_lines = []
    summary_lines.append("This project contains the following key files and folders:")
    if main_files:
        summary_lines.append(f"- Main application files: {', '.join(main_files)}")
    if config_files:
        summary_lines.append(f"- Configuration files: {', '.join(config_files)}")
    if src_files:
        summary_lines.append(f"- Source code is organized in a `src/` directory.")
    if test_files:
        summary_lines.append(f"- Includes test files: {', '.join(test_files[:3])}" + (f" and {len(test_files)-3} more" if len(test_files) > 3 else ""))

    # Features from code comments (very basic!)
    feature_lines = []
    for doc in docs:
        # Try to extract lines starting with "#", "//", or "/*" for Python/JS
        for line in doc.text.split('\n'):
            l = line.strip()
            if l.startswith("#") or l.startswith("//") or l.startswith("/*"):
                comment = l.lstrip("#/ ").strip()
                if len(comment) > 12 and "copyright" not in comment.lower():
                    feature_lines.append(f"- {comment}")
            if len(feature_lines) > 5:
                break
        if len(feature_lines) > 5:
            break

    fallback_description = "\n".join(summary_lines) if summary_lines else "No clear project summary found."
    fallback_features = "\n".join(feature_lines) if feature_lines else "- No explicit features found in code comments."

    return fallback_description, fallback_features

def get_file_tree(docs, max_files=10):
    """Return a markdown list of up to max_files files in the repo."""
    files = [doc.metadata.get('file_path', '') for doc in docs]
    files = sorted(files)
    if len(files) > max_files:
        return "\n".join(f"- `{f}`" for f in files[:max_files]) + f"\n- ...and {len(files)-max_files} more"
    return "\n".join(f"- `{f}`" for f in files)

def generate_readme_sections(docs):
    """
    Generate all main README sections using embed_and_search and fallback logic.
    Returns a dict of {section_name: content}.
    """
    # Section prompts
    prompts = {
        "description": "What is this project about? What does it do? Provide a brief overview of its main purpose and functionality in 2-3 sentences.",
        "features": "What are the main features and capabilities of this project? List 3-5 key functionalities as bullet points.",
        "installation": "How does a user install and set up this project? List all dependencies and setup steps.",
        "usage": "How does a user run or use this project? Show usage example(s).",
        "contributing": "How can someone contribute to this project? List basic steps.",
        "license": "Which license does this project use? If you find a LICENSE file, specify the type.",
    }

    sections = {}

    # 1. Description and Features (with fallback)
    desc = embed_and_search(docs, prompts["description"])
    feat = embed_and_search(docs, prompts["features"])
    if not desc or "context does not provide" in desc.lower():
        desc, _ = synthesize_project_summary(docs)
    if not feat or "context does not provide" in feat.lower():
        _, feat = synthesize_project_summary(docs)

    sections["description"] = desc
    sections["features"] = feat

    # 2. File tree/project structure
    sections["structure"] = get_file_tree(docs)

    # 3. Other sections (installation, usage, contributing, license)
    for section in ["installation", "usage", "contributing", "license"]:
        ans = embed_and_search(docs, prompts[section])
        if not ans or "context does not provide" in ans.lower():
            # Fallbacks for install, usage, contributing, license:
            if section == "installation":
                ans = "See the project files above for configuration files like `requirements.txt` or `package.json`. Typical steps: clone repo, install dependencies, and run main file."
            elif section == "usage":
                ans = "Typical usage: install dependencies, then run the main application file. See source files for details."
            elif section == "contributing":
                ans = "1. Fork the repository\n2. Create a feature branch\n3. Commit your changes\n4. Open a Pull Request."
            elif section == "license":
                ans = "See LICENSE file in repository for license type."
        sections[section] = ans

    return sections