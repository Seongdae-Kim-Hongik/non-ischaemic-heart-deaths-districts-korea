# -*- coding: utf-8 -*-
#  Fig 1 (A) 전 기간 잔차 공간 RR 지도(회색조) (B) 조율·연령표준화율 추이 · Fig 2 강건 4개 변수의 모형별 RR · 보충 그림 S1(EHSA·세 창) S2(시군구 유형)
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from numbers_nihd import load, ROB, SHP
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out_ms", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 166 * MM; DPI = 600; LW = 0.3
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "legend.fontsize": 7.5, "legend.title_fontsize": 8, "axes.linewidth": 0.5, "pdf.fonttype": 42})
NFC = lambda s: unicodedata.normalize("NFC", str(s)).strip()
N = load()
G = gpd.read_file(SHP); G["cd"] = G.sigungu_cd.astype(str); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido")   # 결합은 시군구 코드(cd)로만, 이름 결합 금지
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
rd = lambda f: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", dtype={"sigungu_cd": str})
PANEL_LABEL_PT = 48
def letter(ax, ch, x=None, y=None):   # 패널 문자: 축 왼쪽 위 모서리(그림 좌표), 지도는 왼쪽 위 빈 바다 자리
    fig = ax.figure; b = ax.get_position()
    fig.text(b.x0 if x is None else x, b.y1 if y is None else y, ch, fontsize=PANEL_LABEL_PT, fontweight="bold", va="top", ha="left")
def mapax(ax):   # 06 §6-C: 북침 = 슬림 채움 삼각형 Polygon + "N"(annotate 화살표 금지), 축척 = 0-50-100 km 흑백 2단
    from matplotlib.patches import Polygon, Rectangle
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=0.45); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0   # 좌표 단위 m
    bx, by, bh = x0 + 0.60 * W_, y0 + 0.04 * H_, 0.010 * H_
    ax.add_patch(Rectangle((bx, by), 50000, bh, facecolor="black", edgecolor="black", lw=0.5)); ax.add_patch(Rectangle((bx + 50000, by), 50000, bh, facecolor="white", edgecolor="black", lw=0.5))
    for k, t, ha in ((0, "0", "center"), (50000, "50", "center"), (100000, "100", "center")): ax.text(bx + k, by + bh + 0.008 * H_, t, ha=ha, va="bottom", fontsize=6.5)
    ax.text(bx + 100000 + 0.012 * W_, by + bh / 2, "km", ha="left", va="center", fontsize=6.5)
    nx, ny, nw, nh = x0 + 0.93 * W_, y0 + 0.40 * H_, 0.054 * W_, 0.21 * H_
    ax.add_patch(Polygon([[nx - nw / 2, ny], [nx, ny + nh], [nx + nw / 2, ny], [nx, ny + 0.25 * nh]], closed=True, facecolor="black", edgecolor="black", lw=0.4))
    ax.text(nx, ny + nh + 0.012 * H_, "N", ha="center", va="bottom", fontsize=24, fontweight="bold")
def save(fig, k, dpi=DPI):
    p = os.path.join(FIG, f"Fig{k}.png"); fig.savefig(p, dpi=dpi, facecolor="white"); plt.close(fig)   # 폭 166 mm 고정(bbox tight 쓰지 않음)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(dpi, dpi))
    if not str(k).startswith("S"): im.save(os.path.join(OUTF, f"Figure_{k}.tif"), dpi=(dpi, dpi), compression="tiff_lzw")   # 보충 그림은 보충 PDF에만
    return im.size

# Fig 1 — 회색조(흑백 인쇄)
S6 = rd("S6_spatial_RR.csv"); assert len(S6) == 229
BR = [0, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 99]; LB = ["<0.80", "0.80-0.89", "0.90-0.99", "1.00-1.09", "1.10-1.24", "1.25-1.49", "≥1.50"]
PAL = ["#2166AC", "#67A9CF", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
assert S6.RR.min() >= BR[0] and S6.RR.max() < BR[-1]
fig = plt.figure(figsize=(W, 5.0)); a0 = fig.add_axes([0.02, 0.19, 0.52, 0.79]); a1 = fig.add_axes([0.72, 0.62, 0.26, 0.30]); a2 = fig.add_axes([0.72, 0.22, 0.26, 0.30])
d = S6.set_index("sigungu_cd"); gg = G.copy(); gg["v"] = gg.cd.map(d.RR); gg["c"] = gg.cd.map(d["class"]); assert gg.v.notna().all()
gg.plot(ax=a0, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#b0b0b0", linewidth=LW); mapax(a0)
gg[gg.c == "coldspot"].boundary.plot(ax=a0, color="#08306B", linewidth=0.9); gg[gg.c == "hotspot"].boundary.plot(ax=a0, color="black", linewidth=0.9); letter(a0, "A", x=0.01, y=0.995)
h = [Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)] + [Patch(facecolor="none", edgecolor="black", linewidth=1.0, label="Hot spot"), Patch(facecolor="none", edgecolor="#08306B", linewidth=1.0, label="Cold spot")]
a0.legend(handles=h, title="Residual spatial rate ratio", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3)
yrs = sorted(N["asr"]); P = pd.read_csv(os.path.join(B, "panel_NIHD_std3.csv")); y = P.groupby("year")[["cases", "offset"]].sum(); cr = 1e5 * y.cases / y.offset
assert abs(cr[2011] - N["crude_2011"]) < 1e-6 and abs(cr[2024] - N["crude_2024"]) < 1e-6
a1.plot(yrs, [cr[t] for t in yrs], color="#7F7F7F", marker="o", ms=2.6, lw=0.9, mfc="white", label="Crude")
a1.plot(yrs, [N["asr"][t] for t in yrs], color="#B2182B", marker="s", ms=2.6, lw=0.9, label="Age-standardised")
YM = max(max(cr), max(N["asr"].values())); a1.set_ylim(0, YM * 1.15)
a1.set_xticks([2011, 2014, 2017, 2020, 2024]); a1.set_xticklabels([]); a1.set_ylabel("Deaths per 100,000"); a1.spines[["top", "right"]].set_visible(False); a1.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=6.5); letter(a1, "B", x=0.56, y=0.93)
a2.plot(yrs, [N["circ_share"][t] for t in yrs], color="#B2182B", marker="s", ms=2.6, lw=0.9, label="Non-ischaemic heart disease")
a2.plot(yrs, [N["ihd_share"][t] for t in yrs], color="#2166AC", marker="o", ms=2.6, lw=0.9, label="Ischaemic heart disease")
a2.set_ylim(0, 40); a2.set_xticks([2011, 2014, 2017, 2020, 2024]); a2.set_ylabel("% of circulatory deaths"); a2.set_xlabel("Year"); a2.spines[["top", "right"]].set_visible(False); a2.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=1, fontsize=6.5); letter(a2, "C", x=0.56, y=0.53)
assert max(max(N["circ_share"].values()), max(N["ihd_share"].values())) < 40
s1 = save(fig, 1)

# SDC 그림
EH = rd("S11_ehsa.csv")
CATS = [f"{a} {b}" for b in ("hot", "cold") for a in ("New", "Consecutive", "Intensifying", "Persistent", "Diminishing", "Sporadic", "Oscillating", "Historical")] + ["No pattern"]
EPAL = {"New hot": "#fdd0a2", "Consecutive hot": "#fdae6b", "Intensifying hot": "#a50f15", "Persistent hot": "#de2d26", "Diminishing hot": "#fc9272", "Sporadic hot": "#fee0d2", "Oscillating hot": "#d6a5c9", "Historical hot": "#bcbddc",
        "New cold": "#c6dbef", "Consecutive cold": "#9ecae1", "Intensifying cold": "#08519c", "Persistent cold": "#3182bd", "Diminishing cold": "#6baed6", "Sporadic cold": "#deebf7", "Oscillating cold": "#a1d99b", "Historical cold": "#c7e9c0", "No pattern": "#f7f7f7"}
WM = rd("S4b_window_spatialRR.csv")
nh = WM[WM["class"] == "hotspot"].groupby("sigungu_cd").size(); nc = WM[WM["class"] == "coldspot"].groupby("sigungu_cd").size()
assert int((nh == 3).sum()) == N["hot_all_windows"] and int((nc == 3).sum()) == N["cold_all_windows"]
fig, (a0, a1) = plt.subplots(1, 2, figsize=(W, 4.4)); fig.subplots_adjust(left=0.01, right=0.99, top=0.84, bottom=0.31, wspace=0.04)
gg = G.copy(); gg["c"] = gg.cd.map(EH.set_index("sigungu_cd").EHSA); assert gg.c.notna().all()
gg.plot(ax=a0, color=[EPAL[c] for c in gg.c], edgecolor="#a0a0a0", linewidth=LW); mapax(a0); letter(a0, "A", y=0.995)
cnt = EH.EHSA.value_counts(); pres = [c for c in CATS if c in cnt.index]
a0.legend(handles=[Patch(facecolor=EPAL[c], edgecolor="#777777", linewidth=LW, label=f"{c} ({cnt[c]})") for c in pres], title="Category (districts)", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
hh = gg.cd.map(nh).fillna(0).astype(int); cc = gg.cd.map(nc).fillna(0).astype(int)
gg["k"] = np.where((hh > 0) & (cc > 0), 9, hh - cc)
KP = {-3: "#2166AC", -2: "#67A9CF", -1: "#D1E5F0", 0: "#f7f7f7", 1: "#FDDBC7", 2: "#EF8A62", 3: "#B2182B", 9: "#c2a5cf"}
KL = {-3: "Cold spot in 3 windows", -2: "Cold spot in 2", -1: "Cold spot in 1", 0: "Neither", 1: "Hot spot in 1", 2: "Hot spot in 2", 3: "Hot spot in 3 windows", 9: "Hot or cold by window"}
gg.plot(ax=a1, color=[KP[k] for k in gg.k], edgecolor="#a0a0a0", linewidth=LW); mapax(a1); letter(a1, "B", y=0.995)
kc = gg.k.value_counts()
a1.legend(handles=[Patch(facecolor=KP[k], edgecolor="#777777", linewidth=LW, label=f"{KL[k]} ({kc.get(k, 0)})") for k in (3, 2, 1, 0, -1, -2, -3, 9) if kc.get(k, 0)], title="Windows 2011-2015, 2016-2019, 2020-2024", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
s2 = save(fig, "S1")

# Fig 2 — 강건 3개 + 공공체육시설의 모형별 RR(주모형, KH II·IV, 세 창, 사후 넓은 결과)
LAB = {"screening_suspected_diabetes_share": "Suspected diabetes\nat screening", "current_smoking_rate": "Current smoking", "ill_defined_death_share": "Ill-defined causes\nof death", "public_sports_facilities_per_100k": "Public sports\nfacilities"}
ORD = ["screening_suspected_diabetes_share", "current_smoking_rate", "ill_defined_death_share", "public_sports_facilities_per_100k"]; assert set(ORD[:3]) == set(ROB)
W3 = (("W1_2011-15", "2011-2015 window", "#FDB863"), ("W2_2016-19", "2016-2019 window", "#E08214"), ("W3_2020-24", "2020-2024 window", "#B35806"))
MOD = [("Principal model", lambda v: (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"]), "o", "#000000"),
       ("Knorr-Held type II", lambda v: N["s43"][("KH_typeII", v)][:3], "D", "#D6604D"),
       ("Knorr-Held type IV", lambda v: N["s43"][("KH_typeIV", v)][:3], "D", "#B2182B")] + \
      [(lab, (lambda w: (lambda v: N["win_irr"][(v, w)][:3]))(w), "s", c) for w, lab, c in W3] + \
      [("Broad outcome, post hoc", lambda v: None if v == "ill_defined_death_share" else N["q"][("Q4_broad_outcome", v)][:3], "^", "#542788")]
VALS = [f(v) for v in ORD for _, f, _, _ in MOD if f(v) is not None]; lo_all = min(t[1] for t in VALS); hi_all = max(t[2] for t in VALS)
fig, ax = plt.subplots(figsize=(W, 4.6)); fig.subplots_adjust(left=0.20, right=0.98, top=0.98, bottom=0.25)
off = np.linspace(-0.36, 0.36, len(MOD))
for i, v in enumerate(ORD):
    for (lab, f, mk, fc), o in zip(MOD, off):
        t = f(v)
        if t is None: continue
        e, lo, hi = t; ax.plot([lo, hi], [i + o] * 2, color=fc, lw=0.8); ax.plot(e, i + o, marker=mk, mfc=fc, mec=fc, mew=0.6, ms=3.6, ls="none")
ax.axvline(1, color="#808080", lw=0.5); ax.set_yticks(range(len(ORD))); ax.set_yticklabels([LAB[v] for v in ORD]); ax.invert_yaxis()
ax.set_xscale("log"); xt = [0.90, 0.95, 1.0, 1.05, 1.10]; assert xt[0] <= lo_all and hi_all <= xt[-1], (lo_all, hi_all)
ax.set_xlim(xt[0], xt[-1]); ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Rate ratio per 1 standard deviation (95% credible interval, log scale)"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(handles=[Line2D([0], [0], color=fc, marker=m, mfc=fc, mec=fc, mew=0.6, lw=0.8, ms=3.6, label=l) for l, _, m, fc in MOD], loc="upper center", bbox_to_anchor=(0.40, -0.14), ncol=4, frameon=False)
s3 = save(fig, 2, dpi=1200)   # 
for k, s, dp in zip((1, "S1", 2), (s1, s2, s3), (DPI, DPI, 1200)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/dp*25.4:.0f} x {s[1]/dp*25.4:.0f} mm")
