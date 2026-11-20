# content_nihd.py — 비허혈 심장질환 사망(NIHD, I26-I51) 원고의 Methods·Results 문장(수치는 numbers_nihd에서만).
#  원저 규칙: 본문 ≤3,500, 구조 초록 ≤250(Background/Methods/Results/Conclusions), 표+그림 ≤6, 참고문헌 ≤30, 위첨자 번호 인용, 이중 익명(기관명은 제목면),
#  약어 논문당 2-3개(여기서는 RR·CrI만, 첫 등장 때 풀어 씀), 결과를 말하는 제목 금지, 인과 표현 금지, 영국식 철자, PPI 소제목(Methods), SAGER(성별 미보고 이유).
#  인용 = [@key] 또는 [@web:...]. 단독 저자 → 1인칭 금지. 결과 절에 해석 금지. 제목 쌍점 금지, 시리즈 제목 틀 반복 금지.
#  역방향(불명확 사인) 사후 검정은 "post hoc" 표기, 주모형 교체 금지.
from numbers_nihd import load, ROB, RS
import os, math, pandas as pd
N = load()
def tci(t): return f"RR {t[0]:.3f}; 95% CrI {t[1]:.3f} to {t[2]:.3f}"
def ci(v): r = N["main"][v]; return tci((r["IRR"], r["lo"], r["hi"]))
M = N["main"]; T1 = N["T1"]
S43 = lambda a, v: N["s43"][(a, v)]
dW = lambda a: N["s43_waic"][a] - N["waic_main"]
S41 = lambda a, v: N["s41"][(a, v)]
Q = lambda a, v: N["q"][(a, v)]
SC = lambda s, v: N["sens_main"][s][v]
EN = {"강원도": "Gangwon", "충청남도": "South Chungcheong", "충청북도": "North Chungcheong", "경기도": "Gyeonggi", "서울시": "Seoul", "경상북도": "North Gyeongsang",
      "경상남도": "South Gyeongsang", "전라남도": "South Jeolla", "전라북도": "North Jeolla", "광주시": "Gwangju", "부산시": "Busan", "인천시": "Incheon", "울산시": "Ulsan",
      "대전시": "Daejeon", "세종시": "Sejong", "대구시": "Daegu", "제주도": "Jeju"}
def sidos(d, n):
    l = [f"{EN.get(k, k)} ({v})" for k, v in list(d.items())[:n]]; return ", ".join(l[:-1]) + " and " + l[-1]
KH = ("KH_typeI", "KH_typeII", "KH_typeIII", "KH_typeIV")
WALK, MPA, FAC, VIL, HTN, DM, OBE, SMK, ALC, BLS, IM, OS, ILL = ("walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k", "village_sports_facilities_per_100k",
    "screening_suspected_hypertension_share", "screening_suspected_diabetes_share", "screening_abdominal_obesity_share", "current_smoking_rate", "high_risk_drinking_rate",
    "basic_livelihood_rate", "im_specialists_per_100k", "older_single_household_share", "ill_defined_death_share")
TITLE = "A south-eastern excess of non-ischaemic heart disease deaths in South Korea and its inverse link with ill-defined death certification"   # 발견형, 쌍점 없음, ≤25단어
KEYWORDS = "Heart failure; Death certificates; Diabetes mellitus; Small-area analysis"
assert ":" not in TITLE and "2011" not in TITLE and "229" not in TITLE and "standardi" not in TITLE.lower() and "Korea" in TITLE and len(TITLE.split()) <= 25
assert len(KEYWORDS.split(";")) <= 4
_LK = pd.read_csv(os.path.join(RS, "S1_likelihood.csv")); _LK = _LK[_LK.set == "REF_forced_only"].set_index("family").WAIC
_FAM = pd.read_csv(os.path.join(RS, "S3_main_fit.csv")).family.iloc[0]
assert _FAM == "nbinomial" and _LK["nbinomial"] < _LK["poisson"] and abs(_LK["nbinomial"] - N["waic_forced"]) < 0.15
NHYP = N["n_hyp"]; assert NHYP == 13
SUP = {"methods": "Online Appendix A", "covariates": "Online Table 1", "datacheck": "Online Table 2", "coding": "Online Table 3", "specs": "Online Table 4", "persistence": "Online Figure 1", "strobe": "Online Appendix B"}   # 첫 인용 순서
def sup(k): return SUP[k]
WN = ("W1_2011-15", "W2_2016-19", "W3_2020-24"); WY = ("2011-2015", "2016-2019", "2020-2024")
def wt(v, w): return N["win_irr"][(v, w)]
RET = N["ret"]; NALT = len(N["alt"])
BEST = min(KH, key=lambda a: N["s43_waic"][a]); assert BEST == "KH_typeIV" and dW(BEST) < 0
BW = lambda v, part: N["bw"][f"{v}__{part}"]
_NC = lambda v: tci((N["negctl"][v]["IRR"], N["negctl"][v]["lo"], N["negctl"][v]["hi"]))
G = N["gap"]; G11, G24 = G[2011], G[2024]
MV = lambda v: (int(N["mv"][v]["n_specs"]), N["mv"][v]["cred_frac"])
CS = N["circ_share"]; IHS = N["ihd_share"]
Q1, Q2, Q3, Q4, Q5 = "Q1_without_illdefined", "Q2_illdefined_alone", "Q3_between_within", "Q4_broad_outcome", "Q5_broad_plus_illdefined"
def ev(r): r = 1 / r if r < 1 else r; return r + math.sqrt(r * (r - 1))

METHODS = [
("Design, setting and outcome",
 f"This ecological study covered all {N['n_districts']} districts (urban wards, cities and counties) of South Korea, harmonised to 2024 boundaries, over 2011-2024 ({N['n_rows']:,} district-years). The outcome was annual deaths with non-ischaemic heart disease (International Classification of Diseases, 10th revision, I26-I51: pulmonary heart disease, cardiomyopathy, valvular disease, conduction disorders and arrhythmias, and heart failure) as the underlying cause, by district of residence, from the national cause-of-death statistics, which cover all registered deaths [@web:kostat2026cause]. Resident populations by sex and 5-year age group were the denominators [@web:mois2026population] ({sup('methods')}). Data were extracted in October and November 2026."),
("Age standardisation",
 "Expected deaths were obtained by indirect standardisation: national age-specific death rates in seventeen 5-year age groups and an open-ended group aged 85 years or older were applied to each district's age structure each year. Observed over expected deaths gives the standardised mortality ratio. National trends were directly standardised to the 2015 population. Standardisation was by age, and the sex ratio was a forced control; district counts by sex were not modelled separately, so sex-specific estimates are not reported."),
("District characteristics",
 f"Thirteen district characteristics were selected from the heart failure literature and grouped a priori. Physical activity was represented by the age-standardised rates of walking and of moderate-or-higher intensity physical activity from the Community Health Survey [@kang2015korea], and by public and village sports facilities per 100,000 residents. Cardiometabolic risk was represented by the shares of participants in the national general health screening programme [@kang2022current] classified as suspected hypertension, suspected diabetes (by fasting glucose) and abdominal obesity, and by the survey rates of current smoking and high-risk drinking. Access and social conditions were represented by the share of basic livelihood security recipients, internal medicine specialists per 100,000 and the share of older-adult single-person households. Certification was represented by the share of all deaths whose underlying cause was ill-defined (R00-R99), which was expected to rise with non-ischaemic heart disease deaths because heart failure and ill-defined entries both mark poorly specified certification. Five forced controls were the urban population share, physicians per 1,000, the sex ratio, fiscal autonomy and the share aged 80 years or older. All covariates were standardised to mean 0 and standard deviation 1; sources, expected directions and filled cells are given in {sup('covariates')}, and panel checks run before any model was fitted in {sup('datacheck')}."),
("Statistical analysis",
 f"Models were negative binomial (a lower widely applicable information criterion than Poisson for the forced-controls model), with an offset of log expected deaths, a Besag-York-Mollié 2 district effect with penalised-complexity priors [@riebler2016intuitive], and random-walk and independent year effects, fitted by integrated nested Laplace approximation [@rue2009approximate]. Rate ratios (RRs) per 1 standard deviation are reported with 95% credible intervals (CrIs); an association was credible when the interval excluded 1. Residual hot spots, an exploratory description, were districts whose posterior probability of a residual spatial RR above 1 exceeded 0.95."
 f" Robustness was assessed across 200 covariate subsets [@steegen2016increasing]; four Knorr-Held space-time interactions [@knorrheld2000bayesian]; refits in three calendar windows; between-district and within-district components (district means and deviations from district and year means, entered together); {NALT} alternative specifications of likelihood, temporal structure, lags, spatial structure, spatial confounding and filled values; refits leaving out each province and year; an alternative neighbour graph, a model without the forced share aged 80 years or older and an alternative age standardisation. Hit-and-run traffic collisions, a traffic culture index and fires per 10,000 residents were negative control exposures [@lipsitch2010negative], and infectious disease and stomach cancer deaths, analysed with the same model, were comparison outcomes. Residual spatial RRs were compared with those for ischaemic heart disease and hypertensive diseases from models of the same design. E-values were calculated [@vanderweele2017sensitivity]."
 f" Because the ill-defined share was associated in the direction opposite to that expected, post hoc analyses examined certification: refits without it, with it and the forced controls only, split into between-district and within-district parts, for a broad outcome that added ill-defined deaths (R00-R99) to non-ischaemic heart disease deaths, and without the access and social characteristics ({sup('coding')})."),
("Ethics",
 "The study used only published aggregate statistics, and no individual could be identified. An institutional review board approved the study on 4 November 2025 and its continuing review on 3 November 2026 (institution and approval numbers on the title page), and waived informed consent. Reporting follows the Strengthening the Reporting of Observational Studies in Epidemiology statement [@vonelm2007strengthening] (Online Appendix B)."),
]

KH4 = lambda v: S43("KH_typeIV", v)
_HS3 = sum(N["hot_by_sido"].get(k, 0) for k in ("부산시", "경상남도", "경상북도")); assert _HS3 == 39
NCOF = lambda o, v: N["nco"][(o, v)]
LO = lambda st, v: N["leaveout"][(st, v)]
_PL = "C1_poisson_lognormal"
RESULTS = [
("Deaths and trends",
 f"Over 2011-2024, {N['cases_total']:,} non-ischaemic heart disease deaths occurred in {N['py']/1e6:.0f} million person-years (Table 1). The directly age-standardised rate was {N['asr_2011']:.1f} per 100,000 in 2011 and {N['asr_2024']:.1f} in 2024, and the crude rate rose from {N['crude_2011']:.1f} to {N['crude_2024']:.1f} (Figure 1B). The share of circulatory deaths that were non-ischaemic heart disease rose from {CS[2011]:.1f}% in 2011 to {CS[2024]:.1f}% in 2024, while the ischaemic share was {IHS[2011]:.1f}% and {IHS[2024]:.1f}% (Figure 1C). The share of deaths at 85 years or older rose from {100*N['share85_2011']:.1f}% to {100*N['share85_2024']:.1f}%. The ratio of the 90th to the 10th percentile of smoothed district standardised mortality ratios was {G11['ratio']:.2f} in 2011 and {G24['ratio']:.2f} in 2024 (Kendall's tau {N['gap_tau'][0]:.2f}, P={N['gap_tau'][1]:.2f})."),
("Geography",
 f"Moran's I was {N['moran_pooled']:.2f} for pooled log standardised mortality ratios and {N['moran_year_min']:.2f}-{N['moran_year_max']:.2f} annually, and the spatially structured fraction of the district effect was {N['phi'][0]:.2f} (95% CrI {N['phi'][1]:.2f} to {N['phi'][2]:.2f}). After adjustment, {N['n_hot']} districts were residual hot spots ({N['hot_strict'][0.975][0]} and {N['hot_strict'][0.99][0]} with posterior probability thresholds of 0.975 and 0.99), {_HS3} of them in Busan, South Gyeongsang and North Gyeongsang (Figure 1A). The residual spatial RRs had Spearman's rho of {N['overlap']['IHD'][0]:.2f} with those for ischaemic heart disease and {N['overlap']['HTND'][0]:.2f} with those for hypertensive diseases, and {N['overlap']['IHD'][1]} and {N['overlap']['HTND'][1]} of the {N['n_hot']} hot spots were also hot spots for those causes. Rank persistence across years was Kendall's W {N['kendall_W']:.2f} ({sup('persistence')})."),
("District characteristics",
 f"Adding the thirteen characteristics lowered the widely applicable information criterion from {N['waic_forced']:,.1f} to {N['waic_main']:,.1f} (Table 2, Figure 2). Deaths were higher with a 1 standard deviation higher share of screening participants with suspected diabetes ({ci(DM)}) and current smoking rate ({ci(SMK)}), and lower with more public sports facilities ({ci(FAC)}) and a higher ill-defined share ({ci(ILL)}). Walking ({ci(WALK)}), moderate-or-higher physical activity ({ci(MPA)}), village sports facilities, suspected hypertension, abdominal obesity, high-risk drinking, basic livelihood recipients, internal medicine specialists and older-adult single-person households ({ci(OS)}) had intervals that included 1. Among forced controls, a higher sex ratio was associated with more deaths ({ci('sex_ratio')}). Of the negative control exposures, fires were associated with more deaths ({_NC('fires_per_10000')}), and hit-and-run collisions ({_NC('hit_and_run_rate')}) and the traffic culture index ({_NC('traffic_culture_index')}) were not."),
("Robustness",
 f"Suspected diabetes was credible in all {MV(DM)[0]} subset fits that contained it, in the type I-III Knorr-Held models and, with a lower limit of 1.000 after rounding, in type IV, where it was halved (the best fitting, with an information criterion {-dW(BEST):,.0f} lower than the principal model; {tci(KH4(DM))}), in {RET[DM][0]} of {RET[DM][1]} alternative specifications (Poisson with an observation-level effect, which had a lower information criterion, {tci(S41(_PL, DM))}; 1-year lag, {tci(S41('E1_lag1', DM))}), in refits leaving out each province and year, and with each alternative graph, age standardisation and forced set, but in only one window ({WY[1]}, {tci(wt(DM, WN[1]))}). Its within-district component was credible ({tci(BW(DM, 'within'))}) and its between-district component was imprecise ({tci(BW(DM, 'between'))}). Current smoking was credible in all {MV(SMK)[0]} subset fits that contained it, in {RET[SMK][0]} of {RET[SMK][1]} alternative specifications, in both components (between, {tci(BW(SMK, 'between'))}; within, {tci(BW(SMK, 'within'))}) and in the type I and III models, but not in the type II ({tci(S43('KH_typeII', SMK))}) or type IV ({tci(KH4(SMK))}) models and only in {WY[0]} among the windows. The ill-defined share was credible in all {MV(ILL)[0]} subset fits, in each Knorr-Held model ({tci(KH4(ILL))}), in {RET[ILL][0]} of {RET[ILL][1]} alternative specifications, in both components (between, {tci(BW(ILL, 'between'))}; within, {tci(BW(ILL, 'within'))}) and in {WY[0]} and {WY[2]}. Public sports facilities were credible in {100*MV(FAC)[1]:.1f}% of the subset fits that contained them and in no window or Knorr-Held model, and were associated with both comparison outcomes (infectious disease, {tci(NCOF('INFECT', FAC))}; stomach cancer, {tci(NCOF('GCA', FAC))}); suspected diabetes, smoking and the ill-defined share were not associated with either. Village sports facilities were credible only in the type IV model ({tci(KH4(VIL))}) ({sup('specs')}).",
 f"Without the ill-defined share, the other estimates changed little (suspected diabetes {tci(Q(Q1, DM))}; smoking {tci(Q(Q1, SMK))}), and with the forced controls only it was {tci(Q(Q2, ILL))}. For the broad outcome that included ill-defined deaths, suspected diabetes was {tci(Q(Q4, DM))}, smoking {tci(Q(Q4, SMK))}, basic livelihood recipients {tci(Q(Q4, BLS))}, moderate-or-higher physical activity {tci(Q(Q4, MPA))} and public sports facilities {tci(Q(Q4, FAC))}; adding the ill-defined share to that model restored suspected diabetes ({tci(Q(Q5, DM))}). District residual RRs for the broad outcome correlated with those of the principal model at Spearman's rho {N['q_rho_broad']:.2f} ({sup('coding')}). Residual Moran's I was {N['moran_resid']:.3f} (P={N['moran_resid_p']:.2f}). E-values were {N['evalue'][DM]['E_point']:.2f} (limit {N['evalue'][DM]['E_limit']:.2f}) for suspected diabetes and {N['evalue'][SMK]['E_point']:.2f} (limit {N['evalue'][SMK]['E_limit']:.2f}) for smoking."),
]

# 문장 주장 대조(결과표와 어긋나면 빌드 중단)
H = [v for v in M if M[v]["role"] == "hypothesis"]
assert N["n_cred_hyp"] == 4 and {v for v in H if M[v]["cred"]} == {DM, SMK, FAC, ILL} and M[DM]["IRR"] > 1 and M[SMK]["IRR"] > 1 and M[FAC]["IRR"] < 1 and M[ILL]["IRR"] < 1
assert not any(M[v]["cred"] for v in (WALK, MPA, VIL, HTN, OBE, ALC, BLS, IM, OS)) and M["sex_ratio"]["cred"] and N["waic_main"] < N["waic_forced"]
assert N["negctl"]["fires_per_10000"]["cred"] and not N["negctl"]["hit_and_run_rate"]["cred"] and not N["negctl"]["traffic_culture_index"]["cred"]
assert all(S43(a, DM)[3] for a in KH) and all(S43(a, ILL)[3] for a in KH) and not S43("KH_typeII", SMK)[3] and not KH4(SMK)[3] and S43("KH_typeI", SMK)[3] and S43("KH_typeIII", SMK)[3]
assert not any(S43(a, FAC)[3] for a in KH[1:])
assert all(N["mv"][v]["cred_frac"] == 1 for v in ROB) and 0.4 < MV(FAC)[1] < 0.6
assert [wt(DM, w)[3] for w in WN] == [False, True, False] and [wt(SMK, w)[3] for w in WN] == [True, False, False] and [wt(ILL, w)[3] for w in WN] == [True, False, True] and not any(wt(FAC, w)[3] for w in WN)
assert all(SC(s, DM)[3] and SC(s, SMK)[3] and SC(s, ILL)[3] for s in ("s577", "s2", "s8"))
assert S41('C1_poisson_lognormal', DM)[3] and N['s41_waic']['C1_poisson_lognormal'] < N['waic_main'] and S41('E1_lag1', DM)[3] and KH4(VIL)[3] and not any(S43(a, VIL)[3] for a in KH[:3]) and not M[VIL]['cred'] and NCOF('INFECT', FAC)[3] and NCOF('GCA', FAC)[3] and not any(NCOF(o, v)[3] for o in ('INFECT', 'GCA') for v in ROB) and Q(Q5, DM)[3] and Q(Q4, MPA)[3] and Q(Q4, FAC)[3]
assert all(LO(st, DM)[0] == int(LO(st, DM)[1]) for st in ('province', 'year'))
assert BW(DM, 'within')[3] and not BW(DM, 'between')[3] and BW(SMK, 'within')[3] and BW(SMK, 'between')[3] and BW(ILL, 'within')[3] and BW(ILL, 'between')[3]
assert all(N['leaveout'][(x, DM)][0] == int(N['leaveout'][(x, DM)][1]) for x in ('province', 'year'))
assert Q(Q1, DM)[3] and Q(Q1, SMK)[3] and Q(Q2, ILL)[3] and Q(Q3, "ill_between")[3] and Q(Q3, "ill_within")[3] and not Q(Q4, DM)[3] and Q(Q4, SMK)[3] and Q(Q4, BLS)[3]

if __name__ == "__main__":
    import re
    for x in METHODS + RESULTS: print("##", x[0], "\n", "\n\n".join(x[1:]), "\n")
    print("words M", sum(len(re.sub(r"\[@[^\]]+\]", "", t).split()) for x in METHODS for t in x[1:]), "R", sum(len(re.sub(r"\[@[^\]]+\]", "", t).split()) for x in RESULTS for t in x[1:]))
