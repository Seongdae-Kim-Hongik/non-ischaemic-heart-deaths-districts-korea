#!/usr/bin/env python3
# 99c — 비허혈 심장질환 사망(NIHD, I26-I51) 분자·가설 풀 추가 열(2026-11-12). 99c_htnd를 복제(결합 규칙: 코드표, 이름 결합 금지, 군위군 37310 별칭 그대로). 공유 원본 무수정.
#  ① 정본 통합자료: im_specialists_per100k(내과 전문의 ÷ 정본 인구 × 10만, 정의) — 심부전 진단·지침 약물·심방세동 항응고 진료 역량
#     basic_livelihood_rate(국민기초생활보장 수급자 비율 %) — 수급률 양쪽 규칙(2021-23 값이 2020·2024 평균의 20% 미만 또는 5배 초과 → 결측 → 시군구 내 선형 보간, 33칸 assert)
#  ② 분자: 기준 SQLite region_year mort__심장질환_deaths − mort__허혈성심장질환_deaths(읽기 전용) = 사망원인 long 기타 심장 I26-I51(코드 94)와 3,206칸 일치 assert
#  ③ 사망원인 추가 사인(성=계): 순환계 I00-I99, IHD I20-I25, 기타 심장 I26-I51, 고혈압성 I10-I13, 뇌혈관 I60-I69, R00-R99, 전체
#       → ill_defined_share = R00-R99 ÷ 전체 사망 × 100 (사망진단 품질 대리; NIHD에서는 가설 변수)
#  산출: 02_패널/EXT_canonical_pool_NIHD_261112.csv(nihd_deaths 포함), 02_패널/NIHD_mort_extra_261112.csv
import os, sys, unicodedata, importlib.util
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
ZD = os.environ.get("ST_CANON", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030"))
PAN = os.path.join(ROOT, "02_패널")

# ① 정본
C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); assert K.sigungu_cd.is_unique and len(K) == 229
K.loc[K.sigungu_cd == "37310", "region"] = "대구시군위군"
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
out = pd.DataFrame({"year": C.year, "fbd_region": C.region.map(NFC),
                    "im_specialists_per100k": C.internal_medicine_specialists.astype(float) / C["pop"].astype(float) * 1e5,
                    "basic_livelihood_rate": C.basic_livelihood_recipient_rate.astype(float)})
out = out[(out.year >= 2011) & (out.year <= 2024)].copy()
out = out.sort_values(["fbd_region", "year"])
ref = out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean()
bad = out.year.isin([2021, 2022, 2023]) & ((out.basic_livelihood_rate < 0.2 * out.fbd_region.map(ref)) | (out.basic_livelihood_rate > 5 * out.fbd_region.map(ref)))
print("[99c-nihd] 수급률 결함 칸", int(bad.sum()), sorted(out.loc[bad, "fbd_region"].unique()))
assert bad.sum() == 33 and (out.loc[bad, "fbd_region"] == NFC("경상남도창원시")).sum() == 3
out.loc[bad, "basic_livelihood_rate"] = np.nan
out["basic_livelihood_rate"] = out.groupby("fbd_region").basic_livelihood_rate.transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
assert out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229 and not out.duplicated(["year", "fbd_region"]).any()
print("[99c-nihd] 보간값(앞 9칸)", out.loc[bad, "basic_livelihood_rate"].round(2).tolist()[:9])

# ② 분자(기준 SQLite, 읽기 전용) + 패널 지역
import sqlite3
DB = os.path.expandvars("$ST_GPT_DATASET") + "/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
SQ = pd.read_sql('select year, fbd_region, "mort__심장질환_deaths" as hrt, "mort__허혈성심장질환_deaths" as ihd, "mort__전체사망_deaths" as allm from region_year where year between 2011 and 2024', con); con.close()
SQ["fbd_region"] = SQ.fbd_region.map(NFC); SQ["nihd_sqlite"] = SQ.hrt - SQ.ihd
P = pd.read_csv(os.path.join(ROOT, "04_분석", "NIHD", "panel_NIHD.csv"), encoding="utf-8-sig", usecols=["year", "fbd_region", "population", "cases"]); P["fbd_region"] = P.fbd_region.map(NFC)
X = P.merge(SQ, on=["year", "fbd_region"], how="left", validate="one_to_one"); assert len(X) == 3206 and X.nihd_sqlite.notna().all()
assert (X.cases == X.nihd_sqlite).all(), "선별 패널 cases ≠ SQLite 심장−허혈"
MA = X[["year", "fbd_region", "allm"]].rename(columns={"allm": "mort__전체사망_deaths"})

# ③ 사망원인 추가 사인 → 50.load_source 집계
spec = importlib.util.spec_from_file_location("m50", os.path.join(HERE, "50_build_master_panel.py")); m50 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m50)
L = pd.read_parquet(os.path.join(PAN, "사망원인_시군구_연도_사인_성_long.parquet"), columns=["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note", "cause_code", "sex", "deaths"],
                    filters=[("sex", "==", "계"), ("year", ">=", 2011), ("year", "<=", 2024), ("cause_code", "in", ["0", "91", "9", "93", "94", "95", "I"])])
L = L[(L.sex == "계") & L.year.between(2011, 2024) & L.cause_code.isin(["0", "91", "9", "93", "94", "95", "I"])]
L["v"] = L.cause_code.map({"0": "전체_deaths", "91": "HTND_deaths", "9": "CIRC_deaths", "93": "IHD_deaths", "94": "OTHHEART_deaths", "95": "STRK_deaths", "I": "불명확_deaths"})
IDX = ["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note"]
for c in IDX[1:]: L[c] = L[c].fillna("").astype(str)
W = L.pivot_table(index=IDX, columns="v", values="deaths", aggfunc="sum").reset_index().replace({"": np.nan})
W = W[W.level.notna()]
tmpf = "_tmp_NIHD_mort_extra_wide.csv"; W.to_csv(os.path.join(PAN, tmpf), index=False, encoding="utf-8-sig")
mk = pd.read_csv(os.path.join(PAN, "시군구_마스터키.csv"), dtype=str); mk = mk[mk.fbd_sido.notna()].drop_duplicates("key")
log = dict(missing_files=[], level_filter={}, unmatched=[], special=[], overlap=[], sources={})
src = dict(name="mortx", prefix="", files=[tmpf], sido="sido", sgg="sigungu", merge_counts=True, level="시군구", ratio=lambda c: False, label="사망원인통계")
agg, meta = m50.load_source(src, set(mk.key), log)
os.remove(os.path.join(PAN, tmpf))
agg = agg.merge(mk[["key", "fbd_region"]], on="key", how="left"); agg["fbd_region"] = agg.fbd_region.map(NFC); agg["year"] = agg.year.astype(int)
M = P[["year", "fbd_region", "cases"]].merge(agg[["year", "fbd_region", "전체_deaths", "HTND_deaths", "CIRC_deaths", "IHD_deaths", "OTHHEART_deaths", "STRK_deaths", "불명확_deaths"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
assert M[["전체_deaths", "HTND_deaths", "CIRC_deaths", "OTHHEART_deaths"]].notna().all().all(), M[M.OTHHEART_deaths.isna()].head()
mm = (M.OTHHEART_deaths != M.cases).sum(); print(f"[99c-nihd] I26-I51 검산: 사망원인 long(94) vs SQLite 심장−허혈 불일치 {mm}칸 / {len(M)}"); assert mm == 0
tot_chk = M.merge(MA, on=["year", "fbd_region"]); assert (tot_chk["전체_deaths"] == tot_chk["mort__전체사망_deaths"]).all()
for c in ["불명확_deaths", "IHD_deaths", "STRK_deaths"]: print(f"[99c-nihd] {c} 결측 {int(M[c].isna().sum())}, 14년 합 {int(M[c].sum()):,}"); M[c] = M[c].fillna(0)
M["ill_defined_share"] = M["불명확_deaths"] / M["전체_deaths"] * 100
assert (M.CIRC_deaths >= M.OTHHEART_deaths).all()
M["nihd_share_of_circ"] = M.OTHHEART_deaths / M.CIRC_deaths.where(M.CIRC_deaths > 0) * 100
print("[99c-nihd] 순환계 사망 중 비허혈 심장 비율(%) 연도별 전국", (M.groupby("year").OTHHEART_deaths.sum() / M.groupby("year").CIRC_deaths.sum() * 100).round(2).to_dict())
print("[99c-nihd] 불명확 사인 비율(%) 연도 중앙값", M.groupby("year").ill_defined_share.median().round(2).to_dict())
out = out.merge(M[["year", "fbd_region", "ill_defined_share", "OTHHEART_deaths"]].rename(columns={"OTHHEART_deaths": "nihd_deaths"}), on=["year", "fbd_region"], how="left", validate="one_to_one")
assert out.notna().all().all(), out.isna().sum()
fp = os.path.join(PAN, "EXT_canonical_pool_NIHD_261112.csv"); out.to_csv(fp, index=False, encoding="utf-8-sig")
M.to_csv(os.path.join(PAN, "NIHD_mort_extra_261112.csv"), index=False, encoding="utf-8-sig")
print(f"[99c-nihd] 저장 {fp} {out.shape}; 02_패널/NIHD_mort_extra_261112.csv {M.shape}")
