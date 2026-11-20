# build_manuscript_nihd.py — NIHD 원저 원고 조립(이중 익명: 익명 본문 + 제목면 별도).
#  규격: 본문 ≤3,500(제목면·초록·참고문헌·표·그림 범례 제외), 구조 초록 ≤250(Background/Methods/Results/Conclusions), 키워드 1-4, 표+그림 ≤6, 참고 ≤30,
#   번호 절(1, 1.1 …), 위첨자 번호 인용(쉼표, 3개 이상 연속은 하이픈), 참고문헌 등장순 1. 2. …(쪽 번호 전체), 익명 본문에 저자·기관·감사 없음,
#   제목면 = 제목·저자·소속·교신 주소·감사·이해상충·연구비·윤리·자료·AI 고지·기여.
import os, re, json, subprocess
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm
from jkms_engine import JKMS
from british import brit
import content_nihd as C
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out_ms"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_nihd.json"), encoding="utf-8"))
DRAFT = os.path.join(MS, "draft", "03_manuscript.md")
_zf = os.path.join(OUT, "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "[ZENODO DOI]"
REPO = "non-ischaemic-heart-mortality-certification-korea"; GITHUB = f"https://github.com/Seongdae-Kim-Hongik/{REPO}"
TITLE = C.TITLE; ORCID = "0000-0002-1525-0091"
PHONE = os.environ.get("MS_PHONE", "")   # 교신 전화번호는 공개 코드에 두지 않음(로컬 빌드 때 환경변수)
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
AI_STATEMENT = "During the preparation of this work the author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. After using these tools, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article."
IRB = "The Institutional Review Board of Hongik University approved the study on 4 November 2025 (7002340-202511-HR-012) and its continuing review on 3 November 2026 (7002340-202611-HR-040), and waived informed consent because only published aggregate statistics were used."
FUNDING = "This research received no grant from any funding agency in the public, commercial or not-for-profit sectors."
CONTRIB = "SK conceived and designed the study, curated the data, performed the analysis, wrote the code, prepared the figures and tables, and wrote and revised the manuscript. SK is the guarantor and accepts full responsibility for the work and the conduct of the study, had access to the data and controlled the decision to publish."
def data_statement(): return f"All source data are publicly available aggregate statistics from Statistics Korea, the Ministry of the Interior and Safety, the national public sports facility register, the National Health Screening statistics and the Community Health Survey, as cited in the Methods. The analysis code and the scripts that generate every number, table and figure are openly available on Zenodo (https://doi.org/{ZENODO}). The processed district-year analytic data are available from the author on reasonable request."

def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def pandoc_cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: "{{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)
def strip(t): return re.sub(r"\{\{[^}]+\}\}|<[^>]+>", "", re.sub(r"\s*\[@[^\]]+\]", "", t))
def all_keys():
    src = open(os.path.join(HERE, "content_nihd.py"), encoding="utf-8").read() + open(DRAFT, encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys()

def _acc(d):   # "12 November 2026" -> "12.11.26"
    import datetime as _dt; t = _dt.datetime.strptime(d, "%d %B %Y"); return t.strftime("%d.%m.%y")
def _elide(p):   # (미사용) 쪽 번호 축약
    m = re.fullmatch(r"([A-Za-z]*)(\d+)-([A-Za-z]*)(\d+)", str(p))
    if not m or m.group(1) != m.group(3) or len(m.group(2)) != len(m.group(4)): return p
    a, b = m.group(2), m.group(4); k = 0
    while k < len(a) - 1 and a[k] == b[k]: k += 1
    return f"{m.group(1)}{a}-{b[k:]}"
def ref(k):   # Vancouver(Index Medicus): 저자 6명 이하 전원, 7명 이상 6명 + et al. 학술지 연;권:쪽. doi
    r = REFS[k]
    if r["type"] == "web": return f"{r['authors']}. {r['title'].rstrip('.')}, {r['url']}; {r['year']} [accessed {_acc(r['accessed'])}]."
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:6]) + ", et al"
    t = r["title"].rstrip("."); t = t + ("" if t.endswith(("?", "!")) else ".")
    s = f"{a}. {t} {r['journal']} {r['year']}"
    if r.get("vol"): s += f";{r['vol']}"
    if r.get("pages"): s += f":{r['pages']}"
    return s + (f". doi:{r['doi']}" if r.get("doi") else (f". PMID:{r['pmid']}" if r.get("pmid") else "")) + "."

class TX(JKMS):
    raw = False
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = brit(text); text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)   # 영국식 철자, 음수는 U+2212
        return super()._emit(p, text, sz, bold, italic)
    def head(self, text, level=1):   # 1단계 볼드, 2단계 이탤릭
        if level == 2: return super().head(f"<i>{text}</i>", 2)
        return super().head(text, level)

TAB1_COV = [("pop80_share", "Population aged 80 years or older, %"), ("urban_population_share", "Urban population share, %"),
            ("walking_practice_rate", "Walking, %"), ("moderate_pa_rate", "Moderate-or-higher physical activity, %"), ("public_sports_facilities_per_100k", "Public sports facilities per 100,000"),
            ("screening_suspected_diabetes_share", "Suspected diabetes at screening, %"), ("screening_suspected_hypertension_share", "Suspected hypertension at screening, %"),
            ("screening_abdominal_obesity_share", "Abdominal obesity at screening, %"), ("current_smoking_rate", "Current smoking, %"), ("basic_livelihood_rate", "Basic livelihood recipients, %"),
            ("im_specialists_per_100k", "Internal medicine specialists per 100,000"), ("older_single_household_share", "Older-adult single-person households, %"), ("ill_defined_death_share", "Ill-defined causes, % of all deaths")]
def table1():
    T = N["T1"]; cols = ["W1_2011-15", "W2_2016-19", "W3_2020-24", "2011-2024"]
    rows = [["__H__", "Deaths"],
            ["  District-years, n"] + [f"{T[c]['n']:,}" for c in cols],
            ["  Deaths, n"] + [f"{T[c]['cases']:,}" for c in cols],
            ["  Share of circulatory deaths, %"] + [f"{T[c]['circ']:.1f}" for c in cols],
            ["  Crude rate per 100,000"] + [f"{T[c]['crude']:.1f}" for c in cols],
            ["  Age-standardised rate per 100,000*"] + [f"{T[c]['asr']:.1f}" for c in cols],
            ["  District standardised mortality ratio, median†"] + [f"{T[c]['sir_med']:.2f}" for c in cols],
            ["  District standardised mortality ratio, 10th-90th percentile†"] + [f"{T[c]['sir_p10']:.2f}-{T[c]['sir_p90']:.2f}" for c in cols],
            ["__H__", "District characteristics, mean (standard deviation)"]]
    for v, lab in TAB1_COV:
        mx = max(abs(T[c]['cov'][v][0]) for c in cols); dp = 0 if mx >= 100 else (2 if mx < 1 else 1)
        rows.append([f"  {lab}"] + [f"{T[c]['cov'][v][0]:,.{dp}f} ({T[c]['cov'][v][1]:,.{dp}f})" for c in cols])
    foot = (f"*Direct standardisation to the 2015 national population in seventeen 5-year age groups and an open-ended group aged 85 years or older; window values are means of annual rates ({N['asr_2011']:.1f} in 2011 and {N['asr_2024']:.1f} in 2024). "
            "†Observed over indirectly age-standardised expected deaths summed over the window. Non-ischaemic heart disease, International Classification of Diseases, 10th revision, I26-I51; ill-defined causes, R00-R99.")
    return (f"Table 1 Non-ischaemic heart disease deaths and district characteristics by calendar window, {N['n_rows']:,} district-years in {N['n_districts']} districts, South Korea, 2011-2024", ["Characteristic", "2011-2015", "2016-2019", "2020-2024", "2011-2024"], rows, foot)

GROUPS = [("Physical activity and facilities", ["walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k", "village_sports_facilities_per_100k"]),
          ("Cardiometabolic risk", ["screening_suspected_hypertension_share", "screening_suspected_diabetes_share", "screening_abdominal_obesity_share", "current_smoking_rate", "high_risk_drinking_rate"]),
          ("Access and social conditions", ["basic_livelihood_rate", "im_specialists_per_100k", "older_single_household_share"]),
          ("Certification", ["ill_defined_death_share"]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {"walking_practice_rate": "Walking", "moderate_pa_rate": "Moderate-or-higher physical activity", "public_sports_facilities_per_100k": "Public sports facilities per 100,000",
         "village_sports_facilities_per_100k": "Village sports facilities per 100,000", "screening_suspected_hypertension_share": "Suspected hypertension at screening",
         "screening_suspected_diabetes_share": "Suspected diabetes at screening", "screening_abdominal_obesity_share": "Abdominal obesity at screening", "current_smoking_rate": "Current smoking",
         "high_risk_drinking_rate": "High-risk drinking", "basic_livelihood_rate": "Basic livelihood recipients", "im_specialists_per_100k": "Internal medicine specialists per 100,000",
         "older_single_household_share": "Older-adult single-person households", "ill_defined_death_share": "Ill-defined causes of death",
         "urban_population_share": "Urban population share", "physicians_per_1000": "Physicians per 1,000", "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal autonomy", "pop80_share": "Population aged 80 years or older"}
BEST_KH = "KH_typeIV"; assert min(N["s43_waic"][a] for a in C.KH) == N["s43_waic"][BEST_KH]
def table2():
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"] and set(LABEL) == set(N["main"])
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v); k = N["s43"][(BEST_KH, v)]
            rows.append([f"  {LABEL[v]}", f"{m['IRR']:.3f} ({m['lo']:.3f}-{m['hi']:.3f})", f"{100*mv['cred_frac']:.1f}" if mv else "Forced", f"{k[0]:.3f} ({k[1]:.3f}-{k[2]:.3f})"])
    foot = (f"CrI, credible interval; RR, rate ratio per 1 standard deviation; forced, in every specification. Principal model, negative binomial with a Besag-York-Mollié 2 district effect and random-walk and independent year effects (n={N['n_rows']:,} district-years). "
            f"*Share of the 200 covariate-subset fits containing the covariate in which the CrI excluded 1. "
            f"†Principal model plus a Knorr-Held type IV space-time interaction, the best-fitting interaction model (widely applicable information criterion {-C.dW(BEST_KH):,.0f} lower than the principal model).")
    return (f"Table 2 District characteristics and non-ischaemic heart disease mortality in the principal and type IV space-time interaction models, {N['cases_total']:,} deaths in {N['n_rows']:,} district-years of {N['n_districts']} districts, South Korea, 2011-2024", ["Characteristic", "Principal model RR (95% CrI)", "Subsets credible, %*", "Type IV RR (95% CrI)†"], rows, foot)

FIGCAP = {   # 짧은 제목 + 2-3문장 설명
 1: (f"Residual geography and national trends of non-ischaemic heart disease mortality in South Korea, 2011-2024",
     f"(A) Residual spatial rate ratio by district ({N['cases_total']:,} deaths in 229 districts), the posterior mean of the exponentiated Besag-York-Mollié 2 district effect from the principal model; outlined districts above 1 are residual hot spots (posterior probability of a ratio above 1 greater than 0.95) and outlined districts below 1 are cold spots (less than 0.05), with thick lines for province boundaries and district boundaries as of 2024. "
     "(B) National crude and directly age-standardised (2015 population) death rates per 100,000 population. (C) Non-ischaemic and ischaemic heart disease as shares of circulatory deaths.", None),
 2: ("Rate ratios for four district characteristics across model specifications",
     "Rate ratios per 1 standard deviation with 95% credible intervals for suspected diabetes at screening, current smoking, the ill-defined share of deaths and public sports facilities, 3,206 district-years in 229 districts, South Korea, 2011-2024, from the principal model, the principal model with Knorr-Held type II and type IV space-time interactions, refits in 2011-2015, 2016-2019 and 2020-2024, and, post hoc, a broad outcome that added ill-defined deaths (R00-R99) without the ill-defined share as a covariate. "
     "The vertical line marks a ratio of 1, and the horizontal axis is on a log scale.", None),
}
def foot_row(J, text, sz=9, ls=15):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=9):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=True); foot_row(J, t[3], 8); J.counting = c
def tables_doc():   # 표는 각각 별도 쪽, 제목은 위, 설명·약어는 아래(별도 파일)
    T = TX(cite="sup"); T.raw = False
    for k, t in enumerate((table1(), table2())):
        if k: T.page_break()
        put_table(T, t)
    return T

def build(bw=0, aw=0):   # 익명 본문
    D = read_draft(); J = TX(cite="sup")
    J.para(f"<b>{TITLE}</b>")
    J.para(f"<b>Keywords</b> {C.KEYWORDS}", before=6)
    J.page_break(); J.head("Abstract", 1)
    for p in D["Abstract"]:
        m = re.match(r"^(Background|Methods|Results|Conclusions):\s*(.*)$", p, re.S); J.para(f"<b>{m.group(1)}</b>"); J.para(m.group(2))
    J.page_break(); J.counting = True
    def sec(n, h, paras):
        J.head(f"{n}. {h}", 1)
        for p in paras: J.para(pandoc_cites(p), indent=True)
    sec(1, "Introduction", D["Introduction"])
    J.head("2. Methods", 1)
    for i, x in enumerate(C.METHODS, 1):
        J.head(f"2.{i} {x[0]}", 2)
        for p in x[1:]: J.para(pandoc_cites(p), indent=True)
    J.head("3. Results", 1)
    for i, x in enumerate(C.RESULTS, 1):
        J.head(f"3.{i} {x[0]}", 2)
        for p in x[1:]: J.para(pandoc_cites(p), indent=True)
    J.head("4. Discussion", 1); k = 0
    for p in D["Discussion"]:
        if p.startswith("### "): k += 1; J.head(f"4.{k} {p[4:].strip()}", 2); continue
        J.para(pandoc_cites(p), indent=True)
    sec(5, "Conclusions", D["Conclusions"])
    J.head("Declaration of generative AI and AI-assisted technologies in the manuscript preparation process", 1); J.para(AI_STATEMENT)
    J.counting = False
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for i, k in enumerate(J.cites, 1): s = f"{i}. " + ref(k); rl.append(s); J.para(s)
    J.raw = False
    J.page_break(); J.head("Figure legends", 1)
    for k in sorted(FIGCAP):
        t, c, ab = FIGCAP[k]; J.para(f"<b>Figure {k}.</b> {t}.", before=6); J.para(c + (f" Abbreviations: {ab}." if ab else ""))
    return J, rl, D

def title_page(bw, aw):
    assert PHONE, "MS_PHONE 환경변수 필요(제목면 교신 전화)"
    J = TX(cite="sup"); J.para(f"<b>{TITLE}</b>")
    J.para("Seongdae Kim, PhD", before=6); J.para(AFFIL)
    J.para(f"<b>Corresponding author</b> Seongdae Kim, PhD, {ADDRESS}. Telephone: {PHONE}. E-mail: kimsd@hongik.ac.kr. ORCID: {ORCID}", before=6)
    J.para(f"<b>Word count</b> {bw:,} words (excluding title page, abstract, references, tables and figure legends); abstract {aw} words; {len(KEYS)} references; 2 tables; 2 figures.", before=6)
    J.para(f"<b>Keywords</b> {C.KEYWORDS}", before=6)
    for h, t in (("Acknowledgements", "None."), ("Funding", FUNDING), ("Declaration of competing interests", "The author declares that there is no conflict of interest."),
                 ("Ethics approval", IRB), ("Data availability", data_statement()), ("Author contributions", CONTRIB),
                 ("Declaration of generative AI and AI-assisted technologies in the manuscript preparation process", AI_STATEMENT)):
        J.head(h, 1); J.para(t)
    return J

def docx_bw(path):   # 단어 수: Introduction ~ AI 선언 끝(References 직전), 표·범례 제외
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    return len(t[t.find("\n1. Introduction\n"):t.find("\nReferences\n")].split())
def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    fixed = set()
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_nihd_ms", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads:   # 쪽 끝에 제목이 연달아 걸리면(RESULTS + Deaths and trends) 맨 앞 제목 앞에서 나눈다
                k = len(ls) - 1
                while k > 0 and ls[k - 1] in heads: k -= 1
                orphan = ls[k]; break
        if orphan is None: return
        if orphan in fixed: print("orphan persists, stop:", orphan); return
        fixed.add(orphan); d = Document(path)
        for p in d.paragraphs:
            if p.text.strip() == orphan:   # 빈 문단에 쪽 바꿈을 넣어 제목 앞에 둔다(같은 문단 안 런은 LibreOffice·Word에서 제목 뒤로 밀림)
                np_ = OxmlElement("w:p"); r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); np_.append(r); p._p.addprevious(np_); break
        d.save(path); print("orphan fixed:", orphan)

if __name__ == "__main__":
    p = os.path.join(OUT, "Manuscript.docx"); D = read_draft()
    AB = [re.sub(r"^(Background|Methods|Results|Conclusions):\s*", "", x) for x in D["Abstract"]]; aw = sum(len(x.split()) for x in AB) + 4
    assert aw <= 250, aw
    J, rl, D = build(); J.doc_title = "Manuscript"; J.save(p); bw = docx_bw(p)
    assert bw <= 3500 and len(KEYS) <= 30, (bw, len(KEYS))
    J, rl, D = build(bw, aw); J.doc_title = "Manuscript"; J.save(p); assert docx_bw(p) == bw
    heads = {"Abstract", "References", "Figure legends"} | {f"{i}. {h}" for i, h in enumerate(["Introduction", "Methods", "Results", "Discussion", "Conclusions"], 1)}
    heads |= {f"2.{i} {x[0]}" for i, x in enumerate(C.METHODS, 1)} | {f"3.{i} {x[0]}" for i, x in enumerate(C.RESULTS, 1)} | {f"4.{i} {x[4:].strip()}" for i, x in enumerate([x for x in D["Discussion"] if x.startswith("### ")], 1)}
    fix_orphans(p, heads)
    tp = title_page(bw, aw); tp.doc_title = "Title page"; tp.save(os.path.join(OUT, "Title_Page.docx"))
    subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_nihd_ms", "--convert-to", "pdf", "--outdir", OUT, os.path.join(OUT, "Title_Page.docx")], check=True, capture_output=True)
    T = tables_doc(); T.doc_title = "Tables"; T.save(os.path.join(OUT, "Tables.docx"))
    subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_nihd_ms", "--convert-to", "pdf", "--outdir", OUT, os.path.join(OUT, "Tables.docx")], check=True, capture_output=True)
    K = TX(cite="sup"); K.para("<b>Declaration of interests</b>"); K.para(f"Manuscript: {TITLE}")
    K.para("\u2612 The author declares that there are no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.")
    K.para("Seongdae Kim, Hongik University, Seoul, Republic of Korea")
    K.doc_title = "Declaration of interests"; K.save(os.path.join(OUT, "Declaration_of_Interests.docx"))
    open(os.path.join(OUT, "wordcount.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=2\nfigures=2\ntitle_words={len(TITLE.split())}\n")
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)} | title words {len(TITLE.split())}")
