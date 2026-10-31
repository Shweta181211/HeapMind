"""Create a Hindi-narrated MP4 from generated heap scenes and real app captures."""
import asyncio,math,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables/video';FRAMES=OUT/'frames';SCREENS=ROOT/'deliverables/screens'
SCRIPT=OUT/'script_hi.md';MP4=OUT/'heapmind_hi.mp4';AUDIO=OUT/'narration_hi.mp3';SRT=OUT/'heapmind_hi.srt'
W,H=1920,1080

def ffmpeg_bin():
 exe=shutil.which('ffmpeg')
 if exe:return exe
 try:
  import imageio_ffmpeg
  return imageio_ffmpeg.get_ffmpeg_exe()
 except Exception:raise RuntimeError('ffmpeg is unavailable; install FFmpeg (or imageio-ffmpeg), then rerun.')

def srt_time(seconds):
 ms=int(seconds*1000);h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000;s=ms//1000;ms%=1000
 return f'{h:02}:{m:02}:{s:02},{ms:03}'

def write_srt(words,duration,text):
 # Edge supplies audio-timed boundaries; gTTS fallback estimates cues across the measured audio length.
 cues=[];group=[]
 if not words:
  tokens=text.split()
  for i in range(0,len(tokens),7):cues.append(tokens[i:i+7])
 else:
  for item in words:
   group.append(item)
   if len(group)>=7 or item[2].endswith(('।','!','?','.')):
    cues.append(group);group=[]
  if group:cues.append(group)
 if not cues:return
 out=[]
 if words:
  for i,c in enumerate(cues,1):out.append(f"{i}\n{srt_time(c[0][0])} --> {srt_time(c[-1][1])}\n{''.join(x[2] for x in c).strip()}\n")
 else:
  total=sum(len(x) for x in cues);cursor=0
  for i,c in enumerate(cues,1):
   end=duration*sum(len(x) for x in cues[:i])/total
   out.append(f"{i}\n{srt_time(cursor)} --> {srt_time(end)}\n{' '.join(c)}\n");cursor=end
 SRT.write_text('\n'.join(out),encoding='utf-8')

async def edge_voice(text):
 import edge_tts
 communicate=edge_tts.Communicate(text,'hi-IN-SwaraNeural')
 words=[]
 with open(AUDIO,'wb') as f:
  async for chunk in communicate.stream():
   if chunk['type']=='audio':f.write(chunk['data'])
   elif chunk['type']=='WordBoundary':
    start=chunk['offset']/10_000_000;end=(chunk['offset']+chunk['duration'])/10_000_000;words.append((start,end,chunk['text']))
 return words

def voice(text):
 try:
  words=asyncio.run(edge_voice(text));return words,'edge-tts hi-IN-SwaraNeural'
 except Exception as exc:
  try:
   from gtts import gTTS
   gTTS(text=text,lang='hi',slow=False).save(str(AUDIO));return [],f'gTTS fallback after {type(exc).__name__}'
  except Exception as fallback:raise RuntimeError(f'Edge TTS failed ({type(exc).__name__}) and gTTS fallback failed ({type(fallback).__name__}). Check internet and install edge-tts/gTTS.')

def load_font(size):
 for path in ['/System/Library/Fonts/Supplemental/Kohinoor Devanagari.ttc','/System/Library/Fonts/Supplemental/Arial Unicode.ttf','/System/Library/Fonts/Supplemental/Arial.ttf']:
  if Path(path).exists():
   try:return ImageFont.truetype(path,size)
   except Exception:pass
 return ImageFont.load_default()

def base(title,subtitle='MIT 6.006 · Fall 2011 · Lecture 4'):
 im=Image.new('RGB',(W,H),'#081827');d=ImageDraw.Draw(im);d.rectangle((0,0,24,H),fill='#26a69a')
 d.text((100,65),'HEAPMIND',font=load_font(38),fill='#8dd3ce');d.text((100,170),title,font=load_font(68),fill='white');d.text((100,270),subtitle,font=load_font(32),fill='#b5c6d6')
 return im,d

def diagrams():
 FRAMES.mkdir(parents=True,exist_ok=True);items=[]
 heap=[17,12,15,5,9,11,3];sorted_suffix=[];heap_end=len(heap)
 def draw_heap(step,label):
  im,d=base('Heap sort: tree and array',label)
  d.text((110,375),'Max-heap',font=load_font(34),fill='white')
  for i,v in enumerate(heap):
   if i>=heap_end:continue
   level=int(math.log2(i+1));pos=i-(2**level-1);x=570+((pos+.5)/(2**level)-.5)*700;y=480+level*145
   if i:
    p=(i-1)//2;pl=int(math.log2(p+1));pp=p-(2**pl-1);px=570+((pp+.5)/(2**pl)-.5)*700;py=480+pl*145;d.line((px,py+54,x,y-54),fill='#758aa2',width=5)
   color='#f08c46' if i==0 and heap_end>0 else '#148f77';d.ellipse((x-50,y-50,x+50,y+50),fill=color);d.text((x-19,y-21),str(v),font=load_font(34),fill='white')
  d.text((110,935),'Heap array:  ['+', '.join(map(str,heap[:heap_end]))+']',font=load_font(34),fill='#8dd3ce')
  d.text((1100,935),'Sorted suffix:  ['+', '.join(map(str,sorted_suffix))+']',font=load_font(34),fill='#f3b562')
  fp=FRAMES/f'heap-{step:02}.png';im.save(fp);items.append(fp)
 draw_heap(0,'Build max-heap from the array')
 for step in range(1,7):
  maximum=heap[0];heap[0],heap[heap_end-1]=heap[heap_end-1],heap[0];sorted_suffix.insert(0,maximum);heap_end-=1
  i=0
  while 2*i+1<heap_end:
   c=2*i+1
   if c+1<heap_end and heap[c+1]>heap[c]:c+=1
   if heap[i]>=heap[c]:break
   heap[i],heap[c]=heap[c],heap[i];i=c
  draw_heap(step,f'Step {step}: move maximum to sorted suffix')
 for i in range(5):
  im,d=base('Hybrid RAG pipeline','Only the supplied lecture notes and transcript')
  labels=['PDFs','PyMuPDF chunks','Embeddings + BM25','RRF','Grounded answer']
  for j,label in enumerate(labels):
   x=110+j*350;d.rounded_rectangle((x,500,x+280,680),radius=24,fill='#148f77' if j<=i else '#26394b');d.text((x+24,565),label,font=load_font(25),fill='white')
   if j<4:d.line((x+285,590,x+340,590),fill='#f3b562',width=7)
  fp=FRAMES/f'rag-{i:02}.png';im.save(fp);items.append(fp)
 return items

def duration_seconds(exe,path):
 probe=shutil.which('ffprobe')
 if probe:
  result=subprocess.run([probe,'-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(path)],capture_output=True,text=True,check=True)
  return float(result.stdout.strip())
 result=subprocess.run([exe,'-i',str(path),'-f','null','-'],capture_output=True,text=True)
 match=re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)',result.stderr)
 if not match:raise RuntimeError('Could not determine audio duration; install ffprobe.')
 return int(match.group(1))*3600+int(match.group(2))*60+float(match.group(3))

def main():
 caps=sorted(SCREENS.glob('*.png'))
 if len(caps)<3:raise SystemExit('Need at least 3 real app screenshots in deliverables/screens/. Run: python scripts/take_screenshots.py')
 content=SCRIPT.read_text(encoding='utf-8').split('## English translation')[0]
 text=re.sub(r'^#.*$','',content,flags=re.M).strip()
 words,voice_name=voice(text)
 ff=ffmpeg_bin();duration=duration_seconds(ff,AUDIO)
 if not 120<=duration<=180:print(f'WARNING: voice-over duration is {duration:.1f}s, outside requested 120–180s.')
 write_srt(words,duration,text)
 scene_paths=diagrams()+caps
 FRAMES.mkdir(parents=True,exist_ok=True)
 tmp=OUT/'scene_list.txt';scene_len=duration/len(scene_paths)
 with tmp.open('w',encoding='utf-8') as f:
  for path in scene_paths:f.write(f"file '{path.resolve()}'\nduration {scene_len:.6f}\n")
  f.write(f"file '{scene_paths[-1].resolve()}'\n")
 silent=OUT/'silent_scenes.mp4'
 subprocess.run([ff,'-y','-f','concat','-safe','0','-i',str(tmp),'-vf','scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1','-pix_fmt','yuv420p','-c:v','libx264','-r','30',str(silent)],check=True)
 subtitles=str(SRT.resolve()).replace(':','\\:')
 vf=f"scale=1920:1080,subtitles='{subtitles}':force_style='FontName=Arial,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=44'"
 subprocess.run([ff,'-y','-i',str(silent),'-i',str(AUDIO),'-vf','scale=1920:1080','-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(MP4)],check=True)
 probe=shutil.which('ffprobe')
 if probe:
  result=subprocess.run([probe,'-v','error','-show_entries','format=duration:stream=codec_name,width,height,codec_type','-of','json',str(MP4)],capture_output=True,text=True,check=True)
  print(f'VOICE={voice_name}; voice_duration_s={duration:.2f}; ffprobe={result.stdout.strip()}; file={MP4}')
 else:print(f'VOICE={voice_name}; voice_duration_s={duration:.2f}; MP4_RENDERED_UNVERIFIED: ffprobe missing. Run: ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of json {MP4}')
if __name__=='__main__':main()
