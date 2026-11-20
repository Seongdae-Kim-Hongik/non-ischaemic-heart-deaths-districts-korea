#!/bin/bash
# run_all_nihd.sh — NIHD manuscript build. Network access only in build_refs_nihd.py. MS_PHONE must be set for the title page.
set -e; cd "$(dirname "$0")"
python3 build_refs_nihd.py
python3 figs_nihd.py 2>&1 | grep -v Warning
python3 build_manuscript_nihd.py
python3 esm_nihd.py
python3 sanitize_docx.py ../out_ms/Manuscript.docx ../out_ms/Supplementary_Material.docx ../out_ms/Tables.docx
