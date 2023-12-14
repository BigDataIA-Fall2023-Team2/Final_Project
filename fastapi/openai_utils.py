from dotenv import load_dotenv
import openai, pathlib, os


env_path = pathlib.Path('.') / '.env.fastapi'
load_dotenv(dotenv_path=env_path)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
GPT_MODEL = os.getenv("GPT_MODEL")

def generate_embeddings(query):
    response = openai.Embedding.create(
        input=query,
        model="text-embedding-ada-002" 
    )
    return response["data"][0]["embedding"]

    
def build_prompt(context: str, user_query: str) -> str:
    return (f"The following is the content for your reference:\n"
                   f"{context}\n\n"
                   f"Based on the above content, please answer the question below concisely and clearly. "
                   f"If the information isn't available in the content, just summarize the content provided to you in very short."
                   f"Do not use your own knowledge, If found, Ensure the answer in not more than 100 tokens.\n\n"
                   f"Question:\n{user_query}")
    
def ask_openai_model(prompt: str)-> str:
    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )
    return response['choices'][0]['message']["content"]