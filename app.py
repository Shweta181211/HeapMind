"""HeapMind: Gradio interface for source-only lecture RAG."""
import json, os, socket, time
from pathlib import Path
import gradio as gr
from rag.engine import HybridRetriever, generate, should_refuse

ROOT=Path(__file__).resolve().parent
_manifest=json.loads((ROOT/"archive/source_manifest.json").read_text(encoding="utf-8"))
_titles={s["file"]:s.get("lecture_title_extracted","Lecture 4: Heaps and Heap Sort") for s in _manifest.get("sources",[])}
_retriever=None

def get_retriever():
    global _retriever
    if _retriever is None:_retriever=HybridRetriever()
    return _retriever

def _rate(state):
    now=time.time();state=state or {"timestamps":[]};stamps=[x for x in state.get("timestamps",[]) if now-x<3600]
    if len(stamps)>=15:return False,{"timestamps":stamps}
    stamps.append(now);return True,{"timestamps":stamps}

def _render_sources(hits):
    blocks=[]
    for i,h in enumerate(hits,1):
        m=h["metadata"];title=_titles.get(m.get("file"),"MIT 6.006 Lecture 4: Heaps and Heap Sort")
        page=m.get("page",m.get("pages","unknown"));section=m.get("section","Lecture passage")
        blocks.append(f"[{i}] {title} · PDF page {page} · {section}\n{h['text']}")
    return "\n\n".join(blocks) or "No passages retrieved."

def respond(message,history,language,mode,state):
    allowed,new_state=_rate(state)
    if not allowed:return history+[{"role":"user","content":message},{"role":"assistant","content":"Session limit reached (15 questions per hour). Please try again later."}],"", "Rate limited", "",new_state
    try:
        hits=get_retriever().retrieve(message,k=5)
        refusal=should_refuse(hits,message)
        answer,provider=generate(message,hits,language,mode)
        badge="🛑 **Not covered in lecture**" if refusal or answer.strip()=="This is not covered in the lecture material." else "✅ **Lecture-grounded response**"
        conf=f"Top cosine: {hits[0]['confidence']:.3f} · Lexical overlap: {max((__import__('rag.engine',fromlist=['lexical_overlap']).lexical_overlap(message,h['text']) for h in hits[:3]),default=0):.2f} · Provider: **{provider}**" if hits else f"Provider: **{provider}**"
        return history+[{"role":"user","content":message},{"role":"assistant","content":answer}],_render_sources(hits),conf,badge,new_state
    except Exception as exc:
        return history+[{"role":"user","content":message},{"role":"assistant","content":f"The lecture index is unavailable ({type(exc).__name__}). Please retry."}],"Index unavailable.","Retrieval unavailable","⚠️ **Index unavailable**",new_state

VISUALIZER=r'''<div id="heapmind-viz" style="font-family:system-ui;background:#101827;color:#eaf0f8;padding:18px;border-radius:14px">
<h3>Heap visualizer</h3><p>Enter comma-separated values. Tree and array stay synchronized.</p>
<input id="hm-input" value="17, 12, 15, 5, 9, 11, 3" style="width:70%;padding:8px">
<button onclick="hmBuild()">Build heap</button> <button onclick="hmInsert()">Insert</button> <button onclick="hmExtract()">Extract-max</button> <button onclick="hmSortStart()">Start heap sort</button> <button onclick="hmSortStep()">Next sort step</button>
<p id="hm-msg"></p><svg id="hm-tree" width="100%" height="260" viewBox="0 0 760 260"></svg><div><b>Heap array:</b> <span id="hm-array"></span></div><div><b>Sorted suffix:</b> <span id="hm-sorted"></span></div></div>
<script>
(()=>{let a=[],sortEnd=0;const el=id=>document.getElementById(id);function render(){let svg=el('hm-tree');svg.innerHTML='';let n=a.length;for(let i=0;i<n;i++){let level=Math.floor(Math.log2(i+1)),pos=i-(2**level-1),x=760*(pos+.5)/(2**level),y=30+level*55;if(i){let p=Math.floor((i-1)/2),pl=Math.floor(Math.log2(p+1)),pp=p-(2**pl-1),px=760*(pp+.5)/(2**pl),py=30+pl*55;svg.insertAdjacentHTML('beforeend',`<line x1="${px}" y1="${py+18}" x2="${x}" y2="${y-18}" stroke="#63738a"/>`)}svg.insertAdjacentHTML('beforeend',`<circle cx="${x}" cy="${y}" r="18" fill="${i>=sortEnd?'#68778c':'#16a085'}"/><text x="${x}" y="${y+5}" text-anchor="middle" fill="white">${a[i]}</text>`)}el('hm-array').textContent='['+a.join(', ')+']'}function down(i,n=a.length){while(2*i+1<n){let c=2*i+1;if(c+1<n&&a[c+1]>a[c])c++;if(a[i]>=a[c])break;[a[i],a[c]]=[a[c],a[i]];i=c}}function up(i){while(i>0){let p=Math.floor((i-1)/2);if(a[p]>=a[i])break;[a[p],a[i]]=[a[i],a[p]];i=p}}window.hmBuild=()=>{a=(el('hm-input').value.match(/-?\d+/g)||[]).map(Number);for(let i=Math.floor(a.length/2)-1;i>=0;i--)down(i);sortEnd=0;el('hm-msg').textContent='Bottom-up build complete';el('hm-sorted').textContent='';render()};window.hmInsert=()=>{let v=prompt('Value to insert');if(v===null||!Number.isFinite(Number(v)))return;a.push(Number(v));up(a.length-1);el('hm-msg').textContent='Inserted '+v;render()};window.hmExtract=()=>{if(!a.length)return;let v=a[0];a[0]=a[a.length-1];a.pop();down(0);el('hm-msg').textContent='Extracted maximum '+v;render()};window.hmSortStart=()=>{window.hmBuild();sortEnd=a.length;el('hm-msg').textContent='Heap built. Press Next sort step to move one maximum.'};window.hmSortStep=()=>{if(sortEnd<=1){el('hm-msg').textContent='Heap sort complete';return}let end=--sortEnd;[a[0],a[end]]=[a[end],a[0]];down(0,sortEnd);el('hm-sorted').textContent=a.slice(sortEnd).join(', ');el('hm-msg').textContent='Moved current maximum to sorted suffix';render()};window.hmBuild()})();
</script>'''

with gr.Blocks(title="HeapMind · MIT 6.006 Lecture 4",theme=gr.themes.Soft()) as demo:
    gr.Markdown("# HeapMind\nAsk questions grounded only in the supplied MIT 6.006 Fall 2011 Lecture 4 transcript and notes.")
    gr.Markdown("**Source scope:** MIT 6.006 Introduction to Algorithms, Fall 2011, Lecture 4: “Heaps and Heap Sort.” User identifies Srini Devadas as instructor; transcript speaker label is only PROFESSOR. Task page lists Erik Demaine and Srini Devadas; please verify this course match.")
    with gr.Row():language=gr.Dropdown(["English","Hindi","Hinglish"],value="English",label="Answer language");mode=gr.Dropdown(["Answer","Explain like I'm new","Quiz me"],value="Answer",label="Response mode")
    chatbot=gr.Chatbot(type="messages",height=400,label="Chat")
    with gr.Row():msg=gr.Textbox(placeholder="Ask about heaps or heap sort…",scale=8,label="Question");send=gr.Button("Ask",variant="primary")
    badge=gr.Markdown("**Grounding status:** waiting");confidence=gr.Markdown("**Retrieval:** waiting");session=gr.State({"timestamps":[]})
    with gr.Accordion("Sources · exact retrieved passages",open=False):sources=gr.Textbox(lines=18,interactive=False,label="Lecture title, PDF page, and verbatim passage")
    gr.Examples(["What is the max-heap property?","Why is BUILD-MAX-HEAP O(n)?","How does heap sort move the maximum?"],inputs=msg,label="Example questions")
    with gr.Accordion("Interactive heap visualizer",open=False):gr.HTML('<iframe srcdoc="'+__import__("html").escape(VISUALIZER,quote=True)+'" style="width:100%;height:600px;border:0;border-radius:14px"></iframe>')
    msg.submit(respond,[msg,chatbot,language,mode,session],[chatbot,sources,confidence,badge,session]).then(lambda:"",None,msg)
    send.click(respond,[msg,chatbot,language,mode,session],[chatbot,sources,confidence,badge,session]).then(lambda:"",None,msg)
    gr.Markdown("---\nMIT OpenCourseWare · 6.006 Introduction to Algorithms · Fall 2011 · Lecture 4: “Heaps and Heap Sort.” Attribution: CC BY-NC-SA 4.0. The transcript has no timestamps; citations use lecture title and PDF page numbers.")

def _choose_port():
    for name in ("GRADIO_SERVER_PORT","PORT"):
        raw=os.getenv(name)
        if raw:
            port=int(raw)
            if not 1<=port<=65535:raise ValueError(f"{name} must be a TCP port from 1 to 65535")
            try:
                with socket.socket() as sock:sock.bind(("0.0.0.0",port))
            except OSError as exc:raise RuntimeError(f"Configured port {port} is not available: {type(exc).__name__}") from exc
            return port
    try:
        with socket.socket() as sock:sock.bind(("0.0.0.0",0));return sock.getsockname()[1]
    except OSError as exc:raise RuntimeError(f"Cannot reserve a local listening port in this environment: {type(exc).__name__}") from exc

if __name__=="__main__":demo.launch(server_name="0.0.0.0",server_port=_choose_port(),show_error=False,share=True)
