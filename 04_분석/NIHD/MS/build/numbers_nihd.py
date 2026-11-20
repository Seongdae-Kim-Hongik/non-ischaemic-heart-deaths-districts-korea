# numbers_nihd.py — 비허혈 심장질환 사망(NIHD, I26-I51) 원고의 모든 수치를 결과 CSV에서 읽는다(2026-11-12, numbers_drown.py 복제·수정). 기억·손입력 금지, assert로 정합 확인.
import os, re, glob, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
ROOT = os.path.dirname(os.path.dirname(B)); PAN = os.path.join(ROOT, "02_패널")
WIN = [("W1_2011-15", 2011, 2015), ("W2_2016-19", 2016, 2019), ("W3_2020-24", 2020, 2024)]
rd = lambda f, **k: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", **k)
ROB = ["screening_suspected_diabetes_share", "current_smoking_rate", "ill_defined_death_share"]
SHP = os.environ.get("ST_SHP", os.path.join(HERE, "..", "..", "..", "..", "data", "boundary", "final.shp"))
T1COV = ["pop80_share", "urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "walking_practice_rate", "moderate_pa_rate",
         "public_sports_facilities_per_100k", "village_sports_facilities_per_100k", "screening_suspected_hypertension_share", "screening_suspected_diabetes_share",
         "screening_abdominal_obesity_share", "current_smoking_rate", "high_risk_drinking_rate", "basic_livelihood_rate", "im_specialists_per_100k",
         "older_single_household_share", "ill_defined_death_share"]

def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_NIHD_std3.csv")); N["n_rows"] = len(P); N["n_districts"] = P.fbd_region.nunique()
    assert (N["n_rows"], N["n_districts"]) == (3206, 229)
    N["cases_total"] = int(P.cases.sum()); N["py"] = float(P.offset.sum()); assert N["cases_total"] == 220648
    y = P.groupby("year")[["cases", "offset"]].sum(); N["cases_2011"], N["cases_2024"] = int(y.cases[2011]), int(y.cases[2024])
    N["crude_2011"], N["crude_2024"] = 1e5 * y.cases[2011] / y.offset[2011], 1e5 * y.cases[2024] / y.offset[2024]
    A = pd.read_csv(os.path.join(PAN, "NIHD_national_agerates_mort.csv"))
    _d = {yr: y.cases[yr] - A[A.year == yr].deaths.sum() for yr in y.index}; N["age_unknown"] = sum(_d.values()); assert all(0 <= v <= 5 for v in _d.values()), _d
    w = A[A.year == 2015].set_index("age").denom_nat; w = w / w.sum(); asr = {}
    for yr, g in A.groupby("year"): asr[yr] = 1e5 * float((g.set_index("age").rate * w).sum())
    N["asr"] = asr; N["asr_2011"], N["asr_2024"] = asr[2011], asr[2024]; N["asr_ratio"] = asr[2024] / asr[2011]
    N["asr_max_year"] = max(asr, key=asr.get)
    g24 = A[A.year == 2024].set_index("age"); g11 = A[A.year == 2011].set_index("age")
    N["share85_2024"] = float(g24.deaths["85+"] / g24.deaths.sum()); N["share85_2011"] = float(g11.deaths["85+"] / g11.deaths.sum())
    # 순환계 사망 중 비허혈 심장 비중(NIHD_mort_extra: 사망원인 103항목 = SQLite 원자료)
    X = pd.read_csv(os.path.join(PAN, "NIHD_mort_extra_261112.csv")); xs = X.groupby("year")[["OTHHEART_deaths", "CIRC_deaths", "IHD_deaths", "불명확_deaths"]].sum()
    assert int(xs.OTHHEART_deaths.sum()) == N["cases_total"]
    N["circ_share"] = (100 * xs.OTHHEART_deaths / xs.CIRC_deaths).to_dict(); N["ihd_share"] = (100 * xs.IHD_deaths / xs.CIRC_deaths).to_dict()
    N["ill_deaths"] = xs["불명확_deaths"].to_dict()
    T1 = {}
    for wn, a, b in WIN + [("2011-2024", 2011, 2024)]:
        q = P[(P.year >= a) & (P.year <= b)]; sir = q.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False)
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), py=float(q.offset.sum()), crude=1e5 * q.cases.sum() / q.offset.sum(),
                      asr=np.mean([asr[t] for t in range(a, b + 1)]), sir_p10=sir.quantile(.1), sir_p90=sir.quantile(.9), sir_med=sir.median(),
                      circ=float(100 * xs.OTHHEART_deaths.loc[a:b].sum() / xs.CIRC_deaths.loc[a:b].sum()),
                      cov={v: (q[f"{v}_raw"].mean(), q[f"{v}_raw"].std()) for v in T1COV})
    N["T1"] = T1
    # 공간
    s6m = rd("S6_moran_year.csv"); N["moran_year_min"], N["moran_year_max"] = s6m.moran_I.min(), s6m.moran_I.max()
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"] = r8.loc["pearson_residual_area_mean", "moran_I"]; N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "p_perm"]
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv"); N["rr_min"], N["rr_max"] = s6.RR.min(), s6.RR.max(); N["s6"] = s6
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    N["hot_strict"] = {t: (int((s6.P_gt1 > t).sum()), int((s6.P_gt1 < 1 - t).sum())) for t in (0.975, 0.99)}
    sido = s6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["top_hot"] = s6.sort_values("RR", ascending=False).head(6)[["fbd_region", "RR", "lo", "hi"]].values.tolist()
    wm = rd("S4b_window_spatialRR.csv"); N["win_hot"] = wm[wm["class"] == "hotspot"].groupby("window").size().to_dict()
    hs = {w: set(wm[(wm.window == w) & (wm["class"] == "hotspot")].fbd_region) for w in wm.window.unique()}; N["hot_all_windows"] = len(set.intersection(*hs.values()))
    nc3 = {w: set(wm[(wm.window == w) & (wm["class"] == "coldspot")].fbd_region) for w in wm.window.unique()}; N["cold_all_windows"] = len(set.intersection(*nc3.values()))
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall_W"] = pe.loc["2011-2024", "kendall_W"]
    # 다른 호와의 겹침(IHD, HTND 같은 std3 체인의 잔차 공간 RR)
    N["overlap"] = {}
    for t in ("IHD", "HTND"):
        o = pd.read_csv(os.path.join(os.path.dirname(B), t, "results_std3", "S6_spatial_RR.csv")); m = s6.merge(o[["fbd_region", "RR", "class"]], on="fbd_region", suffixes=("", "_o"))
        assert len(m) == 229
        N["overlap"][t] = (float(m.RR.corr(m.RR_o, method="spearman")), int(((m["class"] == "hotspot") & (m.class_o == "hotspot")).sum()), int((m.class_o == "hotspot").sum()))
    # 주모형·다중우주
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role", "label_en", "P_gt1"]].to_dict("index")
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); N["n_cred_hyp"] = int(((m3.role == "hypothesis") & m3.cred).sum())
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust"]].to_dict("index")
    N["n_robust"] = int(s7.robust.sum()); assert set(s7.index[s7.robust]) == set(ROB), s7.index[s7.robust].tolist()
    hb = open(os.path.join(B, "HM_best_NIHD_std3.txt")).read(); N["waic_forced"] = float(hb.split("ref_forced_only_WAIC=")[1].split()[0])
    N["waic_main"] = float(hb.split("S1_narrative_full(")[1].split(",")[0])
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = nc[["IRR", "lo", "hi", "cred"]].to_dict("index")
    wi = rd("S4_window_IRR.csv"); N["win_irr"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in wi.itertuples()}
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict()
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    ALT = sorted({a for a in S41.analysis.unique() if not a.startswith(("F1_", "F2_", "G2_", "H1_", "bw_"))}); N["alt"] = ALT
    N["ret"] = {}
    for v in ROB + ["public_sports_facilities_per_100k"]:
        sg = N["main"][v]["IRR"] > 1; rr = [N["s41"][(a, v)] for a in ALT if (a, v) in N["s41"]]
        N["ret"][v] = (sum(1 for t in rr if t[3] and (t[0] > 1) == sg), len(rr))
    N["bw"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index"); N["oos"] = rd("S41_oos2024.csv").iloc[0].to_dict()
    N["ppc"] = rd("S42_ppc.csv").iloc[0].to_dict()
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41[S41.analysis.str.startswith("H1_nco_")].itertuples()}
    lo = rd("S41_leaveout_ranges.csv"); N["leaveout"] = {(r.set, r.cov): (r.n, r.n_cred_same_sign) for r in lo.itertuples() if not str(r.cov).startswith("__")}
    cv = rd("S5_covid.csv"); N["covid_main"] = tuple(cv[cv.term == "post_main"][["IRR", "lo", "hi", "cred"]].iloc[0])
    N["covid_int"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in cv[cv.term == "var_x_post"].itertuples()}
    N["sens_main"] = {}
    for v in ["s577", "s2", "s8"]:
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens_main"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
    # 88k review(있을 때만)
    if os.path.exists(os.path.join(RS, "S50_region_slopes.csv")):
        rs = rd("S50_region_slopes.csv"); N["s50_region"] = {(r.covariate, r.region): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in rs.itertuples()}
        N["s50_region_dwaic"] = rs.groupby("covariate").dWAIC_vs_common.first().to_dict()
    # 사망진단 사후 검정(88z, S45_coding_*)
    N["q"] = {}; N["q_waic"] = {}
    for f in glob.glob(os.path.join(RS, "S45_coding_Q*.csv")):
        d = pd.read_csv(f); an = d.analysis.iloc[0] if "analysis" in d else os.path.basename(f)[11:-4]
        N["q"].update({(an, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in d.itertuples()})
        if "WAIC" in d: N["q_waic"][an] = float(d.WAIC.iloc[0])
    qa = pd.read_csv(os.path.join(RS, "S45_coding_area.csv"))
    N["q_rho_noill"] = float(qa.RR_main.corr(qa.RR_noill, method="spearman")); N["q_rho_broad"] = float(qa.RR_main.corr(qa.RR_broad, method="spearman"))
    # 연도별 EB 평활 SMR 격차
    from scipy.stats import kendalltau
    eb = rd("S12c_yearly_EB_SIR.csv"); g = eb.groupby("year").ebSIR
    gap = pd.DataFrame({"p10": g.quantile(.1), "p90": g.quantile(.9)}); gap["ratio"] = gap.p90 / gap.p10
    N["gap"] = gap.to_dict("index"); kt = kendalltau(gap.index, gap.ratio); N["gap_tau"] = (float(kt.statistic), float(kt.pvalue))
    _hs = pd.read_csv(os.path.join(B, "results_screen", "forced_std_hyper.csv")).set_index("hyperpar").loc["Phi for area"]; N["phi_screen"] = (float(_hs["mean"]), float(_hs["X0.025quant"]), float(_hs["X0.975quant"]))
    N["crude_y"] = (1e5 * y.cases / y.offset).to_dict()
    return N

if __name__ == "__main__":
    N = load()
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in N.items() if not isinstance(v, (dict, list, pd.DataFrame))})
    print("circ_share", {k: round(v, 2) for k, v in N["circ_share"].items()}); print("asr", {k: round(v, 2) for k, v in N["asr"].items()})
    print("hot_by_sido", N["hot_by_sido"]); print("top_hot", N["top_hot"]); print("overlap", N["overlap"]); print("win_hot", N["win_hot"])
    print("ret", N["ret"], "alt", len(N["alt"])); print("bw", {k: v for k, v in N["bw"].items() if any(r in k for r in ROB + ["public_sports"])})
    print("evalue", {k: N["evalue"][k] for k in ROB if k in N["evalue"]}); print("oos", N["oos"]); print("ppc", N["ppc"])
    print("nco", {k: v for k, v in N["nco"].items() if k[1] in ROB}); print("leaveout", {k: v for k, v in N["leaveout"].items() if k[1] in ROB})
    print("KH WAIC", {k: v for k, v in N["s43_waic"].items()}); print("q keys", sorted({a for a, _ in N["q"]}))
