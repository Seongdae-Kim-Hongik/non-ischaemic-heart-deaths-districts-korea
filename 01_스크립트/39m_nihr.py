#!/usr/bin/env python3
# 39m_nihr — NIHD 역방향(불명확 사인 비율) 사후 검정용 넓은 결과(비허혈 심장 I26-I51 + 불명확 사인 R00-R99)의 세분 간접표준화 E (2026-11-12, 39m_circb 복제).
#  39m_build_Estd_mort.py 원본은 건드리지 않고, 사인 필터만 두 사인 합으로 바꿔 실행한다.
#  입력: 04_분석/NIHD/panel_NIHD_std3.csv + 02_패널/NIHD_mort_extra_261112.csv(OTHHEART_deaths+불명확_deaths) → 04_분석/NIHR/panel_NIHR.csv
#  산출: 02_패널/NIHR_Estd2.csv
import os, sys, unicodedata
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
NFC = lambda s: unicodedata.normalize("NFC", str(s))
P = pd.read_csv(os.path.join(ROOT, "04_분석", "NIHD", "panel_NIHD_std3.csv"), encoding="utf-8-sig"); P["fbd_region"] = P.fbd_region.map(NFC)
X = pd.read_csv(os.path.join(ROOT, "02_패널", "NIHD_mort_extra_261112.csv"), encoding="utf-8-sig"); X["fbd_region"] = X.fbd_region.map(NFC)
X["NIHR_deaths"] = X.OTHHEART_deaths + X["불명확_deaths"]
P = P.merge(X[["year", "fbd_region", "OTHHEART_deaths", "NIHR_deaths"]], on=["year", "fbd_region"], validate="one_to_one")
assert len(P) == 3206 and (P.cases == P.OTHHEART_deaths).all()
P = P.drop(columns=["cases", "OTHHEART_deaths"]).rename(columns={"NIHR_deaths": "cases"})
os.makedirs(os.path.join(ROOT, "04_분석", "NIHR"), exist_ok=True)
P.to_csv(os.path.join(ROOT, "04_분석", "NIHR", "panel_NIHR.csv"), index=False, encoding="utf-8-sig")
print(f"[39m-nihr] panel_NIHR: 14년 I26-I51 + R00-R99 {int(P.cases.sum()):,}")
src = open(os.path.join(HERE, "39m_build_Estd_mort.py"), encoding="utf-8").read()
rep = [('TAG = sys.argv[1]; assert TAG in CAUSES, TAG; NC = CAUSES[TAG]', 'TAG = "NIHR"; NC = ["기타 심장 질환 (I26-I51)", "달리 분류되지 않은 증상 징후 (R00-R99)"]'),
       ('& (N.cause == NC)]', '& N.cause.isin(NC)]'),
       ('tot = N[N.age == "계"].set_index("year").value; unk = N[N.age == "연령미상"].set_index("year").value.reindex(tot.index).fillna(0)',
        'tot = N[N.age == "계"].groupby("year").value.sum(); unk = N[N.age == "연령미상"].groupby("year").value.sum().reindex(tot.index).fillna(0)')]
for a, b in rep:
    assert src.count(a) == 1, a; src = src.replace(a, b)
i = src.index('old = pd.read_csv(os.path.join(ROOT, "02_패널", f"{TAG}_Estd.csv")'); k = src.index("Gs = OUT.groupby")
src = src[:i] + src[k:]
sys.argv = ["39m_build_Estd_mort.py", "NIHR"]
exec(compile(src, os.path.join(HERE, "39m_build_Estd_mort.py"), "exec"), {"__file__": os.path.join(HERE, "39m_build_Estd_mort.py"), "__name__": "__main__"})
