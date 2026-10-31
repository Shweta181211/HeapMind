"""Ingest only user-supplied PDFs, retaining file, page, and section citations."""
from __future__ import annotations
import hashlib, json, re, shutil
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"source_files"
ARCHIVE=ROOT/"archive"
DATA=ROOT/"data"
TOKEN_RE=re.compile(r"\w+|[^\w\s]", re.UNICODE)
MAX_TOKENS, OVERLAP=250,40

def clean_text(text:str)->str:
    text=text.replace("\x00"," ").replace("\u00ad","")
    text=re.sub(r"(?<=\w)-\s*\n\s*(?=\w)","",text)
    text=re.sub(r"[ \t]+"," ",text)
    text=re.sub(r"\n{3,}","\n\n",text)
    return text.strip()

def token_windows(text:str,size:int=MAX_TOKENS,overlap:int=OVERLAP):
    """Return exact character spans for 200-300 lexical token chunks with overlap."""
    spans=[(m.start(),m.end()) for m in TOKEN_RE.finditer(text)]
    n_tokens=len(spans)
    if not n_tokens:return []
    if n_tokens<=300:return [(spans[0][0],spans[-1][1])]
    count=max(1,(n_tokens-overlap+(300-overlap)-1)//(300-overlap))
    chunk_size=(n_tokens+(count-1)*overlap+count-1)//count
    if chunk_size<200 and n_tokens>300:
        count=max(1,(n_tokens-200+300-1)//300)
        chunk_size=(n_tokens+(count-1)*overlap+count-1)//count
    stride=chunk_size-overlap
    windows=[]
    for i in range(count):
        start=i*stride;end=min(start+chunk_size,n_tokens)
        if start>=n_tokens:break
        windows.append((spans[start][0],spans[end-1][1]))
    return windows

def chunk_words(text:str,size:int=MAX_TOKENS,overlap:int=OVERLAP):
    """Compatibility helper used by tests; each chunk keeps original substring text."""
    return [text[a:b] for a,b in token_windows(text,size,overlap)]

def page_section(page,page_no,filename,previous=""):
    if "transcript" in filename.lower():
        return previous or "Transcript (source has no section headings)"
    candidates=[]
    for block in page.get_text("dict").get("blocks",[]):
        for line in block.get("lines",[]):
            spans=[s for s in line.get("spans",[]) if s.get("text","").strip()]
            if not spans:continue
            size=max(s.get("size",0) for s in spans)
            text="".join(s["text"] for s in spans).strip()
            top=min(s.get("bbox",[0,0])[1] for s in spans)
            if size>=28 and top<180 and len(text)<180:candidates.append((top,-size,text))
    return sorted(candidates)[0][2] if candidates else (previous or f"Page {page_no} (no heading detected)")

def extract():
    try:import fitz
    except ImportError as e:raise RuntimeError("PyMuPDF is required; install requirements.txt") from e
    pdfs=sorted(SOURCE.glob("*.pdf"))
    if not pdfs:raise FileNotFoundError(f"No source PDFs found in {SOURCE}.")
    (ARCHIVE/"pdfs").mkdir(parents=True,exist_ok=True);DATA.mkdir(exist_ok=True)
    docs=[];manifest_sources=[]
    for src in pdfs:
        dest=ARCHIVE/"pdfs"/src.name
        if src.resolve()!=dest.resolve():shutil.copy2(src,dest)
        pdf=fitz.open(src)
        full_text="\n".join(p.get_text() for p in pdf)
        first_pages=clean_text("\n".join(p.get_text() for p in pdf[:min(3,len(pdf))]))
        lines=[s.strip() for s in first_pages.splitlines() if s.strip()]
        pdf_meta={k:pdf.metadata.get(k) for k in ("title","author","subject","creationDate") if pdf.metadata.get(k)}
        lecture_title=pdf_meta.get("title") or next((x for x in lines if "heaps and heap sort" in x.lower()),"NOT FOUND IN FILE TEXT")
        flattened=re.sub(r"\s+"," ",full_text)
        course_matches=re.findall(r"6\.006\s*[-–:]?\s*Introduction to Algorithms(?:\s+Fall\s+\d{4})?",flattened,re.I)
        course_line=next((x for x in course_matches if re.search(r"Fall\s+\d{4}",x,re.I)),course_matches[0] if course_matches else "NOT FOUND IN FILE TEXT")
        instructor_lines=[]
        for j,line in enumerate(lines):
            if re.search(r"instructor|author",line,re.I):instructor_lines.extend([line,*lines[j+1:j+5]])
        if pdf_meta.get("author"):instructor_lines.insert(0,"PDF author metadata: "+pdf_meta["author"])
        urls=sorted(set(u.rstrip(".,);]}") for u in re.findall(r"https?://[^\s<>]+",full_text)))
        transcript=("transcript" in src.stem.lower()) or ("MITOCW |" in full_text[:1200] and "PROFESSOR:" in full_text)
        time_pattern=r"(?<!\d)(?:\d{1,2}:)?\d{1,2}:\d{2}(?!\d)"
        has_times=bool(transcript and re.search(time_pattern,full_text))
        section="";page_entries=[]
        for page_no,page in enumerate(pdf,start=1):
            text=clean_text(page.get_text())
            if not text:continue
            section=page_section(page,page_no,src.name,section)
            page_entries.append({"page":page_no,"section":section,"text":text})
        joined="\n\n".join(x["text"] for x in page_entries)
        ranges=[];cursor=0
        for entry in page_entries:
            ranges.append({"page":entry["page"],"section":entry["section"],"start":cursor,"end":cursor+len(entry["text"])})
            cursor+=len(entry["text"])+2
        for part_no,(lo,hi) in enumerate(token_windows(joined)):
            related=[r for r in ranges if r["start"]<hi and r["end"]>lo]
            pages=[r["page"] for r in related]
            sections=list(dict.fromkeys(r["section"] for r in related))
            page_meta=pages[0] if len(pages)==1 else f"{pages[0]}-{pages[-1]}"
            docs.append({"id":f"{src.stem}-p{pages[0]}-p{pages[-1]}-c{part_no}","text":joined[lo:hi],
                "metadata":{"file":src.name,"page":page_meta,"pages":pages,"section":"; ".join(sections),
                            "sections":sections,"part":part_no,"token_count":len(TOKEN_RE.findall(joined[lo:hi]))}})
        manifest_sources.append({"file":src.name,"sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"pages":len(pdf),
            "pdf_metadata":pdf_meta,"lecture_title_extracted":lecture_title,"course_line_extracted":course_line,
            "instructor_text_extracted":instructor_lines or ["NOT FOUND IN FILE TEXT"],"urls_found_in_pdf":urls,
            "is_transcript_document":transcript,"has_timestamp_pattern":has_times,"opening_text_for_verification":first_pages[:5000]})
    (DATA/"chunks.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in docs),encoding="utf-8")
    names=sorted(set(y for x in manifest_sources for y in x["instructor_text_extracted"] if y!="NOT FOUND IN FILE TEXT"))
    transcript_files=[x for x in manifest_sources if x["is_transcript_document"]]
    if transcript_files and any(x["has_timestamp_pattern"] for x in transcript_files):
        timestamp_status="Timestamp-like strings detected; verify manually before using them. Per citation policy, cite lecture + page only unless transcript timing is visually verified."
    elif transcript_files:timestamp_status="No timestamp pattern found in transcript; cite lecture title + page only."
    else:timestamp_status="Transcript file was not identifiable by filename; do not use timestamp citations."
    course=next((x["course_line_extracted"] for x in manifest_sources if re.search(r"Fall\s+\d{4}",x["course_line_extracted"],re.I)),
                next((x["course_line_extracted"] for x in manifest_sources if x["course_line_extracted"]!="NOT FOUND IN FILE TEXT"),"NOT FOUND IN FILE TEXT"))
    manifest={"created_date":date.today().isoformat(),"knowledge_base_policy":"Only the two user-supplied PDFs are ingested.",
        "course_title_extracted_from_pdf":course,"lecture_title_extracted_from_files":[x["lecture_title_extracted"] for x in manifest_sources],
        "instructor_text_from_pdf_metadata_or_opening_pages":names or "NOT FOUND IN FILE TEXT",
        "instructor_identification_note":"User identifies this lecture as taught by Srini Devadas. Transcript labels speaker only as PROFESSOR; notes PDF author metadata lists multiple people including Srini Devadas.",
        "lecture_resource_url":"UNVERIFIED: no lecture-specific URL is present in the supplied PDFs",
        "general_urls_found_in_pdf":sorted(set(u for x in manifest_sources for u in x["urls_found_in_pdf"])),
        "transcript_timestamp_status":timestamp_status,"sources":manifest_sources,
        "task_page_mismatch":"Task page names Erik Demaine and Srini Devadas; the supplied lecture material is Fall 2011 Lecture 4 and its notes PDF metadata lists multiple authors. Verify this course/lecture choice against the task page.",
        "citation_policy":"Cite the lecture title and PDF page number; do not use video IDs, YouTube URLs, or timestamps."}
    (ARCHIVE/"source_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    readme=["# Source archive","","Knowledge base: only the two PDFs supplied by the user.",""]
    for x in manifest_sources:readme.append(f"- `pdfs/{x['file']}` — {x['pages']} pages; SHA-256 `{x['sha256']}`; extracted title: {x['lecture_title_extracted']}")
    readme += ["","The transcript contains no timestamps; citations use lecture title + page. See `source_manifest.json` for PDF metadata and URL limitations."]
    (ARCHIVE/"README.md").write_text("\n".join(readme)+"\n",encoding="utf-8")
    print(f"Ingested {len(manifest_sources)} supplied PDFs; extracted {len(docs)} source chunks.")
    return docs,manifest

if __name__=="__main__":extract()
