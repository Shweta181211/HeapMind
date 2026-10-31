"""List models available to this API key and recommend one supporting generateContent."""
import json, os, re, sys
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
try:
 from dotenv import load_dotenv
 load_dotenv(ROOT/'.env',override=False)
except ImportError:pass

def main():
 key=os.getenv('GEMINI_API_KEY','')
 if not key:raise SystemExit('GEMINI_API_KEY is not configured; add it to .env and rerun.')
 models=[];page_token=None
 for _ in range(20):
  params={'key':key,'pageSize':1000}
  if page_token:params['pageToken']=page_token
  try:r=requests.get('https://generativelanguage.googleapis.com/v1beta/models',params=params,timeout=20)
  except requests.RequestException as e:raise SystemExit(f'Could not reach Gemini models endpoint: {type(e).__name__}')
  if not r.ok:
   try:msg=r.json().get('error',{}).get('message','')
   except Exception:msg=''
   if key:msg=msg.replace(key,'[REDACTED]')
   raise SystemExit(f'Model listing failed with HTTP {r.status_code}'+(f': {msg[:200]}' if msg else ''))
  body=r.json()
  for m in body.get('models',[]):
   if 'generateContent' in m.get('supportedGenerationMethods',[]):models.append({'name':m.get('name',''),'displayName':m.get('displayName',''),'inputTokenLimit':m.get('inputTokenLimit'),'outputTokenLimit':m.get('outputTokenLimit')})
  page_token=body.get('nextPageToken')
  if not page_token:break
 models.sort(key=lambda x:(tuple(map(int,re.findall(r'\d+',x['name'])) or [0]),'preview' in x['name'].lower()),reverse=True)
 if not models:raise SystemExit('The key returned no models supporting generateContent.')
 flash=[m for m in models if 'flash' in m['name'].lower()]
 stable_flash=[m for m in flash if not any(tag in m['name'].lower() for tag in ('preview','experimental'))]
 chosen=(stable_flash or flash or models)[0]
 model_id=chosen['name'].removeprefix('models/')
 out={'models':models,'recommended_generate_content_model':model_id}
 (ROOT/'data/provider_models.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
 for m in models:print(f"{m['name']}\t{m['displayName']}")
 print(f"Recommended default from this live list: GEMINI_MODEL={model_id}")
 print('Saved recommendation to data/provider_models.json; override with GEMINI_MODEL in .env.')
if __name__=='__main__':main()
