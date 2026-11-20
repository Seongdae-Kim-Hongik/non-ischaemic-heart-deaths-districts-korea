# Non-ischaemic heart disease mortality across districts of South Korea, 2011-2024

Analysis code for the manuscript

> Kim S. *A south-eastern excess of non-ischaemic heart disease deaths in South Korea and its inverse link with ill-defined death certification.*

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24397807 (v1.0.0).

This code is released under the MIT licence.

## Contents

This repository contains code only. The processed district-year data (master table, analytic panel, expected deaths, result tables, adjacency graph and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/NIHD/sets_NIHD_std3.json`, `sets_NIHD_s577.json`, `sets_NIHD_s2.json`, `sets_NIHD_s8.json`, `config_NIHD_std3.json`, `run_std3_chain.sh` | Covariates with expected directions and literature sources, forced controls, negative controls and model settings (principal model `std3`; sensitivity versions with the queen contiguity graph, without the share aged 80 or older, and with ten-group expected deaths) |
| `04_분석/NIHD/MS/` | Scripts that read the result tables and write every number, table and figure in the manuscript and supplementary material, including `content_nihd.py`, which generates the Methods and Results text (the draft source of the Introduction and Discussion is not included) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Deaths by underlying cause (non-ischaemic heart disease, ICD-10 I26-I51 = heart disease I20-I51 minus ischaemic heart disease I20-I25; ill-defined causes R00-R99; all causes) by district of residence: Statistics Korea, cause-of-death statistics (KOSIS DT_1B34E13), 2011-2024. Comparison outcomes are infectious disease and stomach cancer deaths.
- National deaths by cause and 5-year age group (to 85 years or older): Statistics Korea (KOSIS DT_1B34E01), fetched by `34_fetch_national_cause_age_deaths.py` (requires a personal KOSIS API key in `~/.kosis_key`; the key is not included).
- Population by 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block and was corrected (`population_override` in the sets files).
- District covariates: the national public sports facility register (public and village sports facilities), the Community Health Survey (walking, moderate-or-higher physical activity, current smoking, high-risk drinking), national general health screening statistics (suspected hypertension, suspected diabetes, abdominal obesity), Korean Statistical Information Service local indicators (older-adult single-person households, negative controls) and a harmonised public district panel (basic livelihood security recipients with 33 corrected cells, internal medicine specialists, population and area).

## Pipeline

Run from the repository root (set `ST_DATA_ROOT`, `ST_FBDZIP_CORRECTED` and `ST_GPT_DATASET` to the local copies of the public source files and the read-only district database).

| Step | Script | Output |
|---|---|---|
| 0 | `34_fetch_national_cause_age_deaths.py`, `99m3_screen_mortality_prep.py`, `98_fit_forced.R`, `99m3_screen_mortality.py` | National cause-by-age deaths, screening panels and spatial screening of causes of death |
| 1 | `99b_extra_canonical_pool.py`, `99c_extra_canonical_pool_nihd.py` | Outcome counts, ill-defined share, internal medicine specialists and corrected assistance indicators joined by district code |
| 2 | `39m_nihd.py`, `39m_nihr.py` | Expected deaths by indirect standardisation in eighteen 5-year age groups (and ten groups for sensitivity); broad outcome adding ill-defined deaths |
| 3 | `80_build_disease_panel_v.py NIHD` (`ST_VER=std3`) | Analytic panel |
| 4 | `81_fit_inla.R NIHD` (`ST_VER=std3`, `ST_GRAPH=04_분석/NIHD/graph_593.graph`, `ST_THREADS=1`; see `04_분석/NIHD/run_std3_chain.sh`, which wraps R jobs in `rslot.sh`) | Principal model, set comparison, 200-subset multiverse, window models |
| 5 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `86b_ehsa_modified_mk.py`, `87_window_grid.py` | Maps, yearly smoothed ratios and emerging hot spot analysis |
| 6 | `88g_sens_prep.py NIHD std3 INFECT,GCA`, `88g_sens_suite.R` (`GROUP=1..6`), `88h_ppc_varpart.R`, `88k_struct_kh.R` (nb, struct, kh, review) with `kh_constraints.R`, `89g_sens_combine.py` | Sensitivity analyses, comparison outcomes, Knorr-Held models, review outputs |
| 6b | `88z_nihd_posthoc.R` | Post hoc analyses of death certification (Online Table 3) |
| 7 | `04_분석/NIHD/MS/build/` (`build_refs_nihd.py`, `figs_nihd.py`, `build_manuscript_nihd.py`, `esm_nihd.py`; `run_all_nihd.sh`) | Manuscript, supplementary material, figures and checks |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep and sf; Python 3.9 with pandas, geopandas, numpy, scipy, matplotlib and python-docx.

## Licence

MIT (see `LICENSE`).
