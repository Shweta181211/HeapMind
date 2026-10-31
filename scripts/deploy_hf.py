"""Deploy the sanitized HeapMind folder and configure available Space secrets."""
import os
from pathlib import Path
try:
 from dotenv import load_dotenv
 load_dotenv(Path(__file__).resolve().parents[1]/'.env',override=False)
except ImportError:pass
repo=os.getenv('HF_SPACE_ID','').strip();token=os.getenv('HF_TOKEN','').strip()
if not repo or not token:raise SystemExit('Set HF_TOKEN and HF_SPACE_ID in environment or local .env before deploy.')
from huggingface_hub import HfApi
root=Path(__file__).resolve().parents[1]
api=HfApi(token=token)
api.create_repo(repo_id=repo,repo_type='space',space_sdk='gradio',exist_ok=True)
# API keys are transmitted only as Space secrets; never print their values.
for name in ('GEMINI_API_KEY','GROQ_API_KEY'):
 value=os.getenv(name,'').strip()
 if value:api.add_space_secret(repo_id=repo,key=name,value=value);print(f'Set Space secret: {name}')
 else:print(f'Space secret not set (missing locally): {name}')
for name in ('GEMINI_MODEL','GROQ_MODEL','MIN_RETRIEVAL_CONFIDENCE','MIN_LEXICAL_OVERLAP'):
 value=os.getenv(name,'').strip()
 if value:api.add_space_variable(repo_id=repo,key=name,value=value);print(f'Set Space variable: {name}')
ignore=['.git/**','.env','.env.*','.venv/**','venv/**','.cache/**','.build/**','.vendor/**','__pycache__/**','**/__pycache__/**','.pytest_cache/**','*.pyc','*.mp4','deliverables/video/**','deliverables/screens/**','data/answer_cache.sqlite3','source_files/**','eval/results/**','eval/dev_questions.json']
api.upload_folder(repo_id=repo,repo_type='space',folder_path=str(root),ignore_patterns=ignore)
print(f'Uploaded sanitized Space: https://huggingface.co/spaces/{repo}')
