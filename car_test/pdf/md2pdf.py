#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
md2pdf.py — 재사용 가능한 오프라인 Markdown → 정적 PDF 변환기.

특징
  - 로컬 mp4 영상 → cv2로 중간 프레임 추출 후 정지 스크린샷으로 삽입
  - 각 영상 아래에 GitHub asset 링크를 작은 캡션으로 유지
  - LaTeX 수식($…$, $$…$$) → vendored MathJax(tex-svg.js)로 GitHub과 동일 렌더 (완전 오프라인)
  - GFM 표 / <details> / 코드블록 / 이미지 지원
  - 모든 리소스를 HTML에 인라인(data URI / inline script) → 자기완결 → Chrome이 안정적으로 인쇄

일회성 준비(인터넷 1회):
    python md2pdf.py --setup           # MathJax(tex-svg.js) 다운로드 + markdown 라이브러리 확인
이후 변환(오프라인):
    python md2pdf.py "car_test/docs/[26-07-29]_disturb_switchpolicy.md"
    python md2pdf.py <md경로> [-o 출력폴더]

원본 .md 와 res 폴더는 읽기만 한다.
"""
import argparse
import base64
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MATHJAX_LOCAL = os.path.join(HERE, "mathjax", "tex-svg.js")
MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# 영상 블록 패턴:  ![](something.mp4)  [빈줄]  https://github.com/user-attachments/assets/XXXX
VIDEO_RE = re.compile(
    r'!\[[^\]]*\]\(\s*([^)]+?\.mp4)\s*\)'          # ![](path.mp4)
    r'(?:[ \t]*\r?\n)+'                             # blank line(s)
    r'(https://github\.com/user-attachments/assets/\S+)',  # bare asset URL
    re.IGNORECASE,
)
# github URL 뒤따르지 않는 단독 mp4 이미지도 처리
LONE_MP4_RE = re.compile(r'!\[[^\]]*\]\(\s*([^)]+?\.mp4)\s*\)', re.IGNORECASE)


def die(msg):
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def setup():
    os.makedirs(os.path.dirname(MATHJAX_LOCAL), exist_ok=True)
    if os.path.exists(MATHJAX_LOCAL) and os.path.getsize(MATHJAX_LOCAL) > 100000:
        print("MathJax 이미 존재:", MATHJAX_LOCAL)
    else:
        print("MathJax 다운로드 중:", MATHJAX_URL)
        urllib.request.urlretrieve(MATHJAX_URL, MATHJAX_LOCAL)
        print("저장:", MATHJAX_LOCAL, f"({os.path.getsize(MATHJAX_LOCAL)//1024} KB)")
    try:
        import markdown  # noqa
        print("markdown 라이브러리 OK")
    except ImportError:
        die("markdown 라이브러리 없음 →  python -m pip install markdown pymdown-extensions")
    try:
        import cv2  # noqa
        print("cv2 OK")
    except ImportError:
        die("cv2(OpenCV) 없음 →  python -m pip install opencv-python")
    print("준비 완료.")


def data_uri(path):
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def extract_mid_frame_datauri(mp4_path):
    import cv2
    cap = cv2.VideoCapture(mp4_path)
    if not cap.isOpened():
        return None
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    mid = max(0, total // 2)
    cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
    ok, frame = cap.read()
    if not ok:  # fallback: 처음부터 읽기
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    ok, buf = cv2.imencode(".png", frame)
    if not ok:
        return None
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def replace_videos(md_text, md_dir):
    """영상 블록을 <figure>(스크린샷 + github 캡션) HTML로 치환."""
    count = [0]

    def resolve(rel):
        return os.path.normpath(os.path.join(md_dir, rel))

    def figure_html(mp4_rel, url):
        abspath = resolve(mp4_rel)
        name = os.path.basename(mp4_rel)
        if os.path.exists(abspath):
            uri = extract_mid_frame_datauri(abspath)
        else:
            uri = None
        count[0] += 1
        if uri:
            img = f'<img class="vidshot" src="{uri}" alt="{name}">'
        else:
            img = f'<div class="missing">[영상 프레임 없음: {name}]</div>'
        cap = f'<figcaption>📹 <span class="fname">{name}</span>'
        if url:
            cap += f'<br><a class="vidurl" href="{url}">({url})</a>'
        cap += '</figcaption>'
        return f'\n\n<figure class="vid">{img}{cap}</figure>\n\n'

    md_text = VIDEO_RE.sub(lambda m: figure_html(m.group(1), m.group(2)), md_text)
    md_text = LONE_MP4_RE.sub(lambda m: figure_html(m.group(1), None), md_text)
    print(f"  영상 → 스크린샷 치환: {count[0]}개")
    return md_text


def inline_html_images(html, md_dir):
    """<img src="상대경로"> 의 로컬 이미지(png/jpg/gif)를 data URI 로 인라인."""
    def repl(m):
        pre, src, post = m.group(1), m.group(2), m.group(3)
        if src.startswith("data:") or src.startswith("http"):
            return m.group(0)
        abspath = os.path.normpath(os.path.join(md_dir, src))
        if os.path.exists(abspath):
            try:
                return f'<img {pre}src="{data_uri(abspath)}"{post}>'
            except Exception:
                return m.group(0)
        return m.group(0)
    return re.sub(r'<img\s+([^>]*?)src="([^"]+)"([^>]*?)>', repl, html)


CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
  font-size: 12px; line-height: 1.6; color: #1f2328; max-width: 820px; margin: 0 auto; padding: 24px; }
h1 { font-size: 1.9em; border-bottom: 2px solid #d0d7de; padding-bottom: .3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #d0d7de; padding-bottom: .3em; margin-top: 1.6em; }
h3 { font-size: 1.2em; margin-top: 1.3em; } h4 { font-size: 1.05em; }
table { border-collapse: collapse; margin: 1em 0; font-size: .95em; width: auto; }
th, td { border: 1px solid #d0d7de; padding: 6px 12px; vertical-align: top; }
th { background: #f6f8fa; }
code { background: #eff1f3; padding: .15em .35em; border-radius: 4px; font-size: .9em; }
pre { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #d0d7de; margin: .8em 0; padding: .2em 1em; color: #57606a; }
img { max-width: 100%; height: auto; }
figure.vid { margin: 1em 0; text-align: center; }
figure.vid img.vidshot { max-width: 480px; border: 1px solid #d0d7de; border-radius: 6px; }
figure.vid figcaption { font-size: .82em; color: #57606a; margin-top: 4px; }
figure.vid .fname { font-family: monospace; }
figure.vid a.vidurl { color: #0969da; font-family: monospace; font-size: .95em; word-break: break-all; }
.missing { color: #999; font-style: italic; padding: 20px; border: 1px dashed #ccc; }
details { margin: 1em 0; } summary { cursor: pointer; font-weight: 600; }
mjx-container { overflow-x: auto; overflow-y: hidden; }
@page { margin: 14mm; }
"""

HTML_TMPL = """<!doctype html>
<html><head><meta charset="utf-8">
<style>{css}</style>
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['$','$'],['\\\\(','\\\\)']],
          displayMath: [['$$','$$'],['\\\\[','\\\\]']] }},
  svg: {{ fontCache: 'global' }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }}
}};
</script>
<script>{mathjax}</script>
</head><body>
{body}
</body></html>
"""


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", nargs="?", help="변환할 markdown 파일 경로")
    ap.add_argument("-o", "--outdir", default=None, help="출력 폴더 (기본 car_test/pdf)")
    ap.add_argument("--setup", action="store_true", help="MathJax 다운로드 등 일회성 준비")
    args = ap.parse_args()

    if args.setup:
        setup()
        return
    if not args.md:
        die("md 경로를 지정하세요. (준비: python md2pdf.py --setup)")

    md_path = os.path.abspath(args.md)
    if not os.path.exists(md_path):
        die(f"파일 없음: {md_path}")
    md_dir = os.path.dirname(md_path)
    base = os.path.splitext(os.path.basename(md_path))[0]

    # 출력 폴더: 기본 car_test/pdf  (md가 car_test/docs/ 아래라고 가정, 아니면 md 옆 pdf/)
    if args.outdir:
        outdir = os.path.abspath(args.outdir)
    else:
        cand = os.path.normpath(os.path.join(md_dir, "..", "pdf"))
        outdir = cand
    os.makedirs(outdir, exist_ok=True)

    if not (os.path.exists(MATHJAX_LOCAL) and os.path.getsize(MATHJAX_LOCAL) > 100000):
        die(f"MathJax 없음: {MATHJAX_LOCAL}\n먼저 실행: python md2pdf.py --setup")
    try:
        import markdown
    except ImportError:
        die("markdown 라이브러리 없음 →  python -m pip install markdown pymdown-extensions")

    print(f"[1/4] 읽기: {md_path}")
    with open(md_path, encoding="utf-8") as f:
        text = f.read()

    print("[2/4] 영상 프레임 추출 + 치환")
    text = replace_videos(text, md_dir)

    print("[3/4] Markdown → HTML (수식/표/이미지 인라인)")
    html_body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "attr_list", "md_in_html", "sane_lists", "toc"],
    )
    html_body = inline_html_images(html_body, md_dir)

    with open(MATHJAX_LOCAL, encoding="utf-8") as f:
        mathjax_js = f.read()

    full = HTML_TMPL.format(css=CSS, mathjax=mathjax_js, body=html_body)
    html_out = os.path.join(outdir, base + ".html")
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(full)

    print("[4/4] HTML → PDF (Chrome headless)")
    chrome = find_chrome()
    if not chrome:
        die("Chrome/Edge 실행파일을 찾지 못함")
    pdf_out = os.path.join(outdir, base + ".pdf")
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=20000",
        f"--print-to-pdf={pdf_out}",
        "file:///" + html_out.replace("\\", "/"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    if not os.path.exists(pdf_out):
        die(f"PDF 생성 실패\nstdout:{r.stdout}\nstderr:{r.stderr}")
    print("완료:", pdf_out, f"({os.path.getsize(pdf_out)//1024} KB)")
    print("중간 HTML:", html_out)


if __name__ == "__main__":
    main()
