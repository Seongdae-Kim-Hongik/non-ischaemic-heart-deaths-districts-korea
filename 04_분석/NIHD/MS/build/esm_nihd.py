# esm_nihd.py — NIHD 온라인 보충자료(단일 파일: Online Appendix A·Online Tables 1-4·Online Figure 1·Online Appendix B STROBE).
#  수치는 결과 CSV에서만. 영국식 철자(TX가 brit 적용), 표 제목 쌍점 금지. 사후 검정은 post hoc 표기.
import os, re, json, subprocess, pandas as pd
from docx.shared import Cm
import content_nihd as C
from build_manuscript_nihd import LABEL, GROUPS, TX, TITLE as DTITLE, foot_row, read_draft
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); OUT = os.path.join(MSD, "out_ms"); B = os.path.dirname(MSD); RS = os.path.join(B, "results_std3")
N = C.N
st = lambda t: f"{t[0]:.3f} ({t[1]:.3f}-{t[2]:.3f})"
J = TX(cite="bracket")
def TF(title, header, rows, foot="", fs=8):
    J.page_break(); J.table_fit(title, header, rows, "", fs_max=fs, title_bold=True)
    if foot: foot_row(J, foot, 8, 12)
J.para("<b>Online supplementary material</b>"); J.para(f"Supplementary material for the manuscript entitled \"{DTITLE}\"")
J.para("Contents. Online Appendix A (supplementary methods, panel checks and additional results); Online Tables 1-4; Online Figure 1; Online Appendix B (STROBE checklist).")
_MT = pd.read_csv(os.path.join(B, "panel_META_NIHD_std3.csv"), encoding="utf-8-sig").set_index("variable")
_imp = lambda v: int(_MT.loc[v, "n_imputed_interp"] + _MT.loc[v, "n_imputed_sgg_mean"] + _MT.loc[v, "n_imputed_year_mean"])
assert int(_MT.loc["older_single_household_share", "obs_year_min"]) == 2015 and int(_MT.loc["screening_abdominal_obesity_share", "obs_year_min"]) == 2013
gate = open(os.path.join(B, "data_gate_NIHD_std3_261112.txt"), encoding="utf-8").read(); nwarn = int(re.search(r"경고 (\d+)건", gate).group(1))
two = re.findall(r"\[연도 간 평균 2배 이상 차이\] (\S+):", gate); cnt = lambda tag: len(re.findall(r"\[" + re.escape(tag) + r"\]", gate))
assert nwarn == 3 + len(two) + cnt("비율형인데 100 초과") + cnt("전 연도 0인 지역"), (nwarn, len(two))
_vif = _MT.vif_final.dropna().sort_values(ascending=False)
J.page_break(); J.head("Online Appendix A. Supplementary methods, panel checks and additional results", 2)
SM = [("Outcome.", "Annual deaths with non-ischaemic heart disease as the underlying cause (International Classification of Diseases, 10th revision, I26-I51) by district of residence were obtained as heart disease deaths (I20-I51 in the 104-item cause list) minus ischaemic heart disease deaths (I20-I25), and matched the published item for other heart diseases (I26-I51) in every district-year. The source tables do not split I26-I51 into heart failure (I50) and other codes. Districts were harmonised to the 229 units of 2024 (urban wards of metropolitan cities, cities and counties); merged or split districts were aggregated to their 2024 boundaries. Deaths with ill-defined causes (R00-R99) and all-cause deaths came from the same tables."),
      ("Expected deaths.", f"National non-ischaemic heart disease deaths by 5-year age group (0-4 to 80-84 years and 85 years or older, both sexes combined) came from the national cause-of-death table by cause, sex and age. District populations by 5-year age group came from resident registration statistics; the 2023 age-specific populations of Changwon, which repeated the 2022 values in the source file, were replaced with the official 2023 values (total 1,009,038) before expected deaths and population-based covariates were computed. An alternative standardisation used ten age groups (sensitivity analysis)."),
      ("Covariates.", "Walking, moderate-or-higher physical activity, current smoking and high-risk drinking were age-standardised district rates from the Community Health Survey; moderate physical activity was missing for one survey year and was interpolated within districts. Public and village sports facilities came from the national public sports facility register. Suspected hypertension, suspected diabetes and abdominal obesity were crude (not age-standardised) shares of national general health screening participants classified by the programme from measured blood pressure, fasting glucose and waist circumference; abdominal obesity was published from 2013, and earlier years carried district means. Basic livelihood security recipients and internal medicine specialists came from a harmonised public district panel; recipient shares that collapsed in 2021-2023 for districts of cities with general wards were corrected in 33 cells with the published city totals. The share of older-adult single-person households was published from 2015; earlier years carried district means. The ill-defined share was R00-R99 deaths over all deaths of residents, times 100."),
      ("Panel checks before modelling.", f"An automated gate run on the analytic panel before any model was fitted reported {nwarn} flags (Online Table 2). Most flagged standardised columns whose yearly means were near 0 (a ratio artefact) or the post-2020 indicator (constant by design); the remaining flag was the sex ratio above 100 (men per 100 women). Final variance inflation factors were below 10 except for {LABEL.get(_vif.index[0], _vif.index[0]).lower()} ({_vif.iloc[0]:.2f}), which was retained and omitted in a post hoc refit (Online Table 3, Q6)."),
      ("Models.", f"Software: R 4.6.0 with R-INLA; Python 3.9 for data preparation and figures. The negative binomial likelihood was chosen because its widely applicable information criterion (WAIC) for the forced-controls model was lower than that of a Poisson likelihood ({C._LK['nbinomial']:,.1f} vs {C._LK['poisson']:,.1f}). Fixed effects had normal priors with mean 0 and precision 4 (intercept precision 0.001). The Besag-York-Mollié 2 district effect used penalised-complexity priors (P(σ>0.5)=0.01; P(φ<0.5)=2/3) on a 593-edge district adjacency graph with Jeju Island as a separate component; the random-walk and independent year effects used penalised-complexity priors (P(σ>0.5)=0.01). Covariate subsets for the multiverse were drawn with a fixed seed, each characteristic entering with probability 0.5, excluding empty and duplicate subsets. A characteristic was considered subset-stable when its interval excluded 1 in at least 75% of the subsets containing it, with the same sign in at least 95%. Knorr-Held interactions used Kronecker-product structures (type I: independent; II: random walk in time by independent districts; III: independent years by intrinsic conditional autoregressive districts; IV: random walk by intrinsic conditional autoregressive districts). The queen-contiguity sensitivity graph (577 edges) omits the 16 audited contact links of the principal graph. The Spatial+-type method regressed each standardised covariate on the lowest-frequency eigenvectors of the graph Laplacian and restandardised the residuals. Between- and within-district components were the district mean and the deviation from district and year means, entered together and each standardised by its own standard deviation. E-values were computed for the rate ratio and for the interval limit closer to 1."),
      ("Post hoc certification analyses.", "Added after the inverse association of the ill-defined share was seen: (Q1) the principal model without the ill-defined share; (Q2) the ill-defined share with the forced controls only; (Q3) the ill-defined share split into its district mean (between) and the deviation from it (within); (Q4) a broad outcome, non-ischaemic heart disease plus ill-defined deaths, with expected deaths recomputed for the broad outcome and without the ill-defined share; (Q5) the broad outcome with the ill-defined share, which is mechanically positive because ill-defined deaths are part of the outcome; and (Q6) the principal model without internal medicine specialists and older-adult single-person households.")]
for h, t in SM: J.para(f"<b>{h}</b> {t}")
_ci = N["covid_int"]; _cred_int = [LABEL[v].lower() for v, t in _ci.items() if t[3] and v in LABEL]
J.para("<b>Additional results.</b> " + f"Kendall's W of annual rankings was {N['kendall_W']:.2f} over 2011-2024. With hot spots defined by posterior probabilities above 0.975 or 0.99, there were {N['hot_strict'][0.975][0]} and {N['hot_strict'][0.99][0]} hot spots and {N['hot_strict'][0.975][1]} and {N['hot_strict'][0.99][1]} cold spots. "
       f"The COVID-19 period (2020 onward) main effect was {st(N['covid_main'])}; interactions with the period were credible for {', '.join(_cred_int[:-1]) + ' and ' + _cred_int[-1] if len(_cred_int) > 1 else (_cred_int[0] if _cred_int else 'no covariate')}. "
       f"Posterior predictive 95% intervals covered {100*N['ppc']['coverage95']:.1f}% of district-years; for 2024, predicted from a model fitted to 2011-2023, the 95% intervals covered {100*N['oos']['coverage95']:.1f}% of districts.")
# ── Table S1 ──
DIR = {"walking_practice_rate": "−", "moderate_pa_rate": "−", "public_sports_facilities_per_100k": "−", "village_sports_facilities_per_100k": "−", "screening_suspected_hypertension_share": "+",
       "screening_suspected_diabetes_share": "+", "screening_abdominal_obesity_share": "+", "current_smoking_rate": "+", "high_risk_drinking_rate": "+", "basic_livelihood_rate": "+",
       "im_specialists_per_100k": "−", "older_single_household_share": "+", "ill_defined_death_share": "+"}
SRCN = {"walking_practice_rate": "Community Health Survey", "moderate_pa_rate": "Community Health Survey", "public_sports_facilities_per_100k": "Sports facility register", "village_sports_facilities_per_100k": "Sports facility register",
        "screening_suspected_hypertension_share": "National health screening", "screening_suspected_diabetes_share": "National health screening", "screening_abdominal_obesity_share": "National health screening",
        "current_smoking_rate": "Community Health Survey", "high_risk_drinking_rate": "Community Health Survey", "basic_livelihood_rate": "District panel", "im_specialists_per_100k": "District panel",
        "older_single_household_share": "KOSIS local indicators", "ill_defined_death_share": "Cause-of-death statistics", "urban_population_share": "KOSIS local indicators", "physicians_per_1000": "KOSIS local indicators",
        "sex_ratio": "KOSIS local indicators", "fiscal_independence": "KOSIS local indicators", "pop80_share": "Resident registration"}
UNIT = {"walking_practice_rate": "%", "moderate_pa_rate": "%", "public_sports_facilities_per_100k": "per 100,000", "village_sports_facilities_per_100k": "per 100,000", "screening_suspected_hypertension_share": "% of participants",
        "screening_suspected_diabetes_share": "% of participants", "screening_abdominal_obesity_share": "% of participants", "current_smoking_rate": "%", "high_risk_drinking_rate": "%", "basic_livelihood_rate": "%",
        "im_specialists_per_100k": "per 100,000", "older_single_household_share": "%", "ill_defined_death_share": "% of deaths", "urban_population_share": "%", "physicians_per_1000": "per 1,000", "sex_ratio": "ratio",
        "fiscal_independence": "%", "pop80_share": "%"}
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs:
        m = _MT.loc[v]; rows.append([f"  {LABEL[v]}", UNIT[v], SRCN[v], f"{int(m.obs_year_min)}-{int(m.obs_year_max)}", ("Forced" if m.role == "forced" else DIR[v]), f"{_imp(v):,}"])
TF("Online Table 1 Source, unit, observed years, expected direction and filled cells for each district characteristic, 229 districts, South Korea, 2011-2024", ["Characteristic", "Unit", "Source", "Years", "Direction", "Filled cells"], rows,
   "KOSIS, Korean Statistical Information Service; ratio, men per 100 women; forced, in every model. Expected directions were set from the heart failure literature before any covariate model was fitted. Filled cells of 3,206 district-years: interpolation within districts, district means or yearly means.")
# ── Table S2 ──
ext = json.load(open(os.path.join(RS, "S41_extreme_flags.json"))); impc = json.load(open(os.path.join(RS, "S41_imputed_cells.json")))
rows = [["Year with all districts zero or missing", "≥98% of districts", "1 (post-2020 indicator)", "None (by design)"],
        ["Constant within a year", "1 value in a year", "1 (same indicator)", "None (by design)"],
        ["Year explains most variance", "Year R² ≥ 0.80", "1 (same indicator)", "None (by design)"],
        ["Yearly means differ twofold or more", "Max/min yearly mean ≥ 2", f"{len(two)} (mostly standardised, mean near 0)", "Checked against sources; retained"],
        ["Ratio-type column above 100", "Maximum > 100", f"{cnt('비율형인데 100 초과')} (sex ratio, men per 100 women)", "Retained (definition)"],
        ["Extreme district-years", ">5 IQR beyond quartiles", f"{sum(ext.values())} cells in {sum(1 for v in ext.values() if v)} covariates", "Refilled in one alternative specification"],
        ["Missing district-years", "No observation", f"{sum(impc.values()):,} cells across {len(impc)} covariates", "Filled within districts"],
        ["Duplicated population block", "Repeats 2022", "1 district-year (Changwon, 2023)", "Replaced with official total"],
        ["Collapsed recipient shares", "Below 0.2% in city wards, 2021-2023", "33 cells", "Corrected with city totals"]]
TF("Online Table 2 Panel checks before modelling, with rules, thresholds, flags and actions, 3,206 district-years, South Korea, 2011-2024", ["Check", "Threshold", "Flags in this panel", "Action"], rows,
   "Checks were run on the analytic panel before any model was fitted. IQR, interquartile range.")
# ── Table S3: 사후 사망진단 검정 ──
DM, SMK, ILL, FAC = C.DM, C.SMK, C.ILL, C.FAC
QN = [("Q0_main_refit", "Q0 Principal model (refit)"), ("Q1_without_illdefined", "Q1 Without ill-defined share"), ("Q2_illdefined_alone", "Q2 Ill-defined share with forced controls"),
      ("Q4_broad_outcome", "Q4 Broad outcome, without ill-defined share"), ("Q5_broad_plus_illdefined", "Q5 Broad outcome with ill-defined share"), ("Q6_access_axis_removed", "Q6 Without specialists and older adults living alone")]
VS = [DM, SMK, ILL, FAC, C.BLS]; VH = ["Suspected diabetes", "Current smoking", "Ill-defined causes", "Public sports facilities", "Basic livelihood recipients"]
qg = lambda a, v: st(N["q"][(a, v)]) if (a, v) in N["q"] else "–"
rows = [[lab] + [qg(a, v) for v in VS] for a, lab in QN]
rows.append(["Q3 Ill-defined share, between districts", "–", "–", qg("Q3_between_within", "ill_between"), "–", "–"])
rows.append(["Q3 Ill-defined share, within districts", "–", "–", qg("Q3_between_within", "ill_within"), "–", "–"])
TF("Online Table 3 Post hoc analyses of death certification, rate ratios per 1 standard deviation, 229 districts, South Korea, 2011-2024", ["Analysis"] + VH, rows,
   f"Post hoc analyses added after the inverse association of the ill-defined share was seen; the principal model was not changed. Q0 refits the principal model with the post hoc script; differences from Table 2 in the third decimal reflect numerical approximation. Q3 splits the ill-defined share into its district mean and the deviation from it (district-mean centring only), which differs from the two-way decomposition reported in the main text. Broad outcome, non-ischaemic heart disease (I26-I51) plus ill-defined (R00-R99) deaths, with its own expected deaths. In Q5, the ill-defined share is mechanically associated with the broad outcome because ill-defined deaths are part of it. Spearman correlation of district residual rate ratios with the principal model: {N['q_rho_noill']:.2f} without the ill-defined share and {N['q_rho_broad']:.2f} for the broad outcome. –, not in the model.", fs=7)
# ── Table S4: 사양 ──
DM, SMK, ILL, FAC = C.DM, C.SMK, C.ILL, C.FAC
NAMES = [("principal", "Principal model"), ("KH_typeI", "Knorr-Held type I"), ("KH_typeII", "Knorr-Held type II"), ("KH_typeIII", "Knorr-Held type III"), ("KH_typeIV", "Knorr-Held type IV"),
         ("icar_besag", "ICAR district effect"), ("iid_only", "IID district effect"), ("no_spatial", "No district effect"), ("knn3", "3 nearest neighbours"), ("knn4", "4 nearest neighbours"), ("knn5", "5 nearest neighbours"),
         ("pc_phi_flat", "Flat prior on mixing"), ("pc_relaxA", "Relaxed priors A"), ("pc_relaxB", "Relaxed priors B"),
         ("B3_smooth_forced", "Smoothed sex ratio"), ("C1_poisson_lognormal", "Poisson, observation effect"), ("C2_rw2_year", "RW2 year effect"), ("C3_ar1_year", "AR1 year effect"), ("C4_sido_year_iid", "Province-by-year effect"), ("D1_spatial_plus", "Spatial+-type"),
         ("E0_nolag_from2012", "No lag, from 2012"), ("E1_lag1", "Lag 1 year"), ("E0_nolag_from2013", "No lag, from 2013"), ("E2_lag2", "Lag 2 years"), ("F3_extreme_R7", "Extreme values refilled"), ("G1_kchs_ma3", "Survey 3-year averages"), ("H4_odd_years", "Odd years only"), ("H4_even_years", "Even years only"),
         ("s8", "Ten age groups in E"), ("s2", "Share aged 80+ omitted"), ("s577", "Queen graph, 577 edges"),
         ("H1_nco_INFECT", "Infectious diseases (comparison)"), ("H1_nco_GCA", "Stomach cancer (comparison)")]
SS = {**N["s43"], **N["s41"]}; WA = {**N["s43_waic"], **N["s41_waic"]}
for v in ("s577", "s2", "s8"): SS.update({(v, c): t for c, t in N["sens_main"][v].items()}); WA[v] = float(pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_fit.csv")).WAIC.iloc[0])
WA["principal"] = N["waic_main"]; SS.update({("principal", c): (r["IRR"], r["lo"], r["hi"], r["cred"]) for c, r in N["main"].items()})
def cell(a, v): t = SS.get((a, v)); return "–" if t is None else st(t)
ALT = set(N["alt"]); assert ALT <= {a for a, _ in NAMES}, sorted(ALT - {a for a, _ in NAMES})
HN = {DM: "Suspected diabetes", SMK: "Current smoking", ILL: "Ill-defined causes", FAC: "Public sports facilities"}
_F3 = f"Values are rate ratios (95% credible intervals) per 1 standard deviation; –, not computed. *One of the {len(ALT)} alternative specifications counted in the text. For the Spatial+-type model, rate ratios are per 1 standard deviation of the residualised covariate. Comparison outcomes were fitted with the same covariates and model. WAIC, widely applicable information criterion (not comparable across different outcomes or numbers of years); ICAR, intrinsic conditional autoregressive; IID, independent and identically distributed; RW2, second-order random walk; AR1, first-order autoregressive; E, expected deaths."
for part, cols in (("A", [DM, SMK]), ("B", [ILL, FAC])):
    rows = [[lab + ("*" if a in ALT else "")] + ([f"{WA[a]:,.0f}" if a in WA and not a.startswith("H1_") else "–"] if part == "A" else []) + [cell(a, v) for v in cols] for a, lab in NAMES]
    TF(f"Online Table 4{part.lower()} Rate ratios per 1 standard deviation across alternative specifications and comparison outcomes, 229 districts, South Korea, 2011-2024 (part {part})", ["Specification"] + (["WAIC"] if part == "A" else []) + [HN[v] for v in cols], rows, _F3, fs=8)
# ── Figure S1 ──
J.page_break(); _pp = J.para(""); _pp.add_run().add_picture(os.path.join(HERE, "figs", "FigS1.png"), width=Cm(16))
J.para("<b>Online Figure 1 Persistence of the district pattern of non-ischaemic heart disease mortality, 229 districts, South Korea, 2011-2024.</b> (A) Emerging hot spot analysis (Getis-Ord Gi* with Mann-Kendall trend) of empirical Bayes smoothed standardised mortality ratios; numbers of districts in parentheses. (B) Number of calendar windows (2011-2015, 2016-2019, 2020-2024) in which each district was a residual hot or cold spot in the window refits.")
# ── STROBE ──
DS = [x[4:].strip() for x in read_draft()["Discussion"] if x.startswith("### ")]; MH = [x[0] for x in C.METHODS]; RH = [x[0] for x in C.RESULTS]
CK = [("Title and abstract", "1", "Title page; Abstract"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"), ("Study design", "4", f"Methods, {MH[0]}"), ("Setting", "5", f"Methods, {MH[0]}"),
      ("Participants", "6", f"Methods, {MH[0]} (district populations; ecological)"), ("Variables", "7", f"Methods, {MH[1]}; {MH[2]}; Online Table 1"), ("Data sources/measurement", "8", "Methods; Online Appendix A; Online Table 2"),
      ("Bias", "9", f"Methods, {MH[3]}; Online Tables 3-4"), ("Study size", "10", f"Methods, {MH[0]} (all 229 districts)"), ("Quantitative variables", "11", f"Methods, {MH[2]}"),
      ("Statistical methods", "12", f"Methods, {MH[3]}"), ("Participants (flow)", "13", "Not applicable (aggregate district data; no exclusions)"), ("Descriptive data", "14", f"Results, {RH[0]}; Table 1"), ("Outcome data", "15", f"Results, {RH[0]}; Table 1"),
      ("Main results", "16", f"Results, {RH[2]}; Table 2; Figures 1-2"), ("Other analyses", "17", f"Results, {RH[3]}; Online Tables 3-4; Online Figure 1"),
      ("Key results", "18", "Discussion, Main findings"), ("Limitations", "19", "Discussion, Strengths and limitations"), ("Interpretation", "20", "Discussion"), ("Generalisability", "21", "Discussion, Strengths and limitations"),
      ("Funding", "22", "Funding statement on the title page")]
assert "Strengths and limitations" in DS and "Main findings" in DS
# 항목별 쪽 번호(최종 원고 PDF에서 절 제목 위치로 자동 산출)
_pages = subprocess.run(["pdftotext", "-layout", os.path.join(OUT, "Manuscript.pdf"), "-"], capture_output=True, text=True).stdout.split("\f")
def _c(l): return re.sub(r"^\d+(\.\d+)*\.?\s+", "", re.sub(r"^\d+\s+", "", l.strip()))
def _pg(h, start=1, prefix=False):
    for i, pg in enumerate(_pages, 1):
        if i < start: continue
        if any((_c(l).startswith(h) if prefix else _c(l) == h) for l in pg.split("\n")): return i
    raise AssertionError(h)
_ab, _in = _pg("Abstract"), _pg("Introduction"); _me, _re, _di = _pg("Methods", _in), _pg("Results", _in), _pg("Discussion", _in)
_rf = _pg("References") - 1
PG = {"1": f"1, {_ab}", "2": f"{_in}", "3": f"{_me - 1 if _me > _in else _in}", "4": f"{_pg(MH[0])}", "5": f"{_pg(MH[0])}", "6": f"{_pg(MH[0])}", "7": f"{_pg(MH[1])}-{_pg(MH[2]) + 1}", "8": f"{_pg(MH[0])}-{_pg(MH[3])}",
      "9": f"{_pg(MH[3])}-{_pg(MH[4])}", "10": f"{_pg(MH[0])}", "11": f"{_pg(MH[2])}", "12": f"{_pg(MH[3])}-{_pg(MH[4])}", "13": "–", "14": f"{_pg(RH[0], _re)}", "15": f"{_pg(RH[0], _re)}",
      "16": f"{_pg(RH[2], _re)}-{_pg(RH[3], _re)}", "17": f"{_pg(RH[3], _re)}-{_di}", "18": f"{_pg('Main findings')}", "19": f"{_pg('Strengths and limitations')}", "20": f"{_di}-{_pg('Conclusions', _di)}", "21": f"{_pg('Strengths and limitations')}", "22": "–"}
CK = [(a, b, c + ("" if PG[b] == "–" else f" ({'pages' if ('-' in PG[b] or ',' in PG[b]) else 'page'} {PG[b]})")) for a, b, c in CK]
J.page_break()
J.table_fit("Online Appendix B STROBE checklist for this ecological study", ["Item", "No.", "Where reported (page in main manuscript)"], [[a, b, c] for a, b, c in CK], "", fs_max=8, title_bold=True)
foot_row(J, "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology.", 8, 12)
ps = os.path.join(OUT, "Supplementary_Material.docx"); J.doc_title = "Supplementary material"; J.save(ps)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_nihd_esm", "--convert-to", "pdf", "--outdir", OUT, ps], check=True, capture_output=True)
print("saved", os.path.basename(ps))
