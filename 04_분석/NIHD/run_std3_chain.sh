#!/bin/bash
# NIHD (non-ischaemic heart disease deaths, I26-I51) principal chain
#  comparison outcomes: infectious disease (INFECT) and stomach cancer (GCA) deaths. E는 사망판 39m(5세 18구간·85+).
set -x
S="${ST_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"; cd "$S"
RC="${ST_FBDZIP_CORRECTED:?set ST_FBDZIP_CORRECTED}"
GR="$S/04_분석/NIHD/graph_593.graph"; T=NIHD; D=261112; NW=4; NMV=200
ST_FBDZIP="$RC" python3 01_스크립트/39m_nihd.py || exit 1   # 선별용 panel_CLRD.csv(99m)가 이미 창원 교정 인구
ST_VER=std3 python3 01_스크립트/80_build_disease_panel_v.py $T || exit 1
ST_FBDZIP="$RC" ST_E2_PANEL_SUF=_std3 python3 01_스크립트/39m_nihd.py || exit 1
ST_VER=std3 python3 01_스크립트/80_build_disease_panel_v.py $T || exit 1
python3 ../논문_마스터자료/00_분석전_데이터게이트/data_gate.py 04_분석/$T/panel_${T}_std3.csv --region fbd_region > 04_분석/$T/data_gate_${T}_std3_$D.txt 2>&1
echo "GATE rc=$?"
[ "$STAGE" = A ] || ( for V in s577 s2 s8; do ST_VER=$V python3 01_스크립트/80_build_disease_panel_v.py $T && (cd 01_스크립트 && ST_VER=$V ST_THREADS=1 ST_MV_N=2 ST_GRAPH=$([ $V = s577 ] || echo "$GR") $S/01_스크립트/rslot.sh Rscript 81_fit_inla.R $T); done > 04_분석/$T/run_sens3.log 2>&1 ) &
# 81: S1~S6 + S7 사양표까지(ST_MV_STOP) → 사양 구간 병렬 → 본 실행(합치기·요약·S9 이후) → 82·83
export ST_VER=std3 ST_THREADS=1 ST_GRAPH="$GR"
(cd 01_스크립트 && ST_MV_STOP=1 $S/01_스크립트/rslot.sh Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81a.log 2>&1 || exit 1
echo STAGE_A_done; [ "$STAGE" = A ] && exit 0
STEP=$(( NMV / NW ))
for k in $(seq 0 $((NW-1))); do a=$(( k*STEP+1 )); b=$(( (k+1)*STEP )); (cd 01_스크립트 && ST_MV_RANGE=$a-$b $S/01_스크립트/rslot.sh Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81_mv_$a.log 2>&1 & sleep 20; done
wait
(cd 01_스크립트 && $S/01_스크립트/rslot.sh Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81b.log 2>&1 || exit 1
python3 01_스크립트/82_core_report.py $T $D > 04_분석/$T/run_std3_82.log 2>&1
python3 01_스크립트/83_check_report.py $T $D >> 04_분석/$T/run_std3_82.log 2>&1
echo "CHAIN done"
python3 01_스크립트/87_window_grid.py $T std3; (cd 01_스크립트 && TAG=$T ST_VER=std3 $S/01_스크립트/rslot.sh Rscript 85_window_maps.R $T std3); python3 01_스크립트/86_yearly_maps_ehsa.py $T std3
python3 01_스크립트/88g_sens_prep.py $T std3 INFECT,GCA || exit 1
cd 01_스크립트; export TAG=$T NCO=INFECT,GCA
L=../04_분석/$T
for G in 1 2 3 4 5 6; do GROUP=$G $S/01_스크립트/rslot.sh Rscript 88g_sens_suite.R > $L/run_std3_88g_$G.log 2>&1 & done
$S/01_스크립트/rslot.sh Rscript 88h_ppc_varpart.R > $L/run_std3_88h.log 2>&1 &
for G in nb struct kh review; do $S/01_스크립트/rslot.sh Rscript 88k_struct_kh.R $G > $L/run_std3_88k_$G.log 2>&1 & done
wait
if grep -q 'KH_typeII FAILED' $L/run_std3_88k_kh.log; then mv $L/results_std3/S43_part_KH_typeII.csv $L/results_std3/S43_part_KH_typeII_failed_init.csv.bak; KH_INIT=0 $S/01_스크립트/rslot.sh Rscript 88k_struct_kh.R kh > $L/run_std3_88k_kh_init0.log 2>&1; fi
cd ..; TAG=$T ST_VER=std3 python3 01_스크립트/89g_sens_combine.py $T std3 > 04_분석/$T/run_std3_89g.log 2>&1
echo "ALL rc=$?"; grep -l "FAILED" 04_분석/$T/run_std3_88*.log; true
