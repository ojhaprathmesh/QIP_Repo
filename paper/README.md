# Research Paper: Quantum Image Processing (QIP) on NISQ Hardware

This directory contains the complete, publication-ready research paper conforming to the formatting specifications and guidance provided for the course project.

## Directory Contents
- **`main.tex`**: Master LaTeX source document using the required single-column IEEEtran template (`\documentclass[12pt,onecolumn,draftclsnofoot]{IEEEtran}`), including:
  - 1-inch margins, Times 12 pt, justified text with continuous sections (no `\raggedright`, no artificial page breaks).
  - All 8 required sections structured strictly according to the word count guidance (~4,987 total prose words).
  - Mathematical proof of the **NEQR Bit-Significance Variance Theorem**.
  - Embedded vector diagrams using TikZ:
    - **Fig. 1**: End-to-end System Architecture.
    - **Fig. 2**: Algorithmic Execution Workflow.
    - **Fig. 3**: Reconstruction PSNR scaling curves showing the empirical critical threshold $p_{\text{crit}} \approx 0.008$.
  - Structured tables:
    - **Table I**: Comprehensive literature comparison table.
    - **Table II**: Notation and symbol table.
    - **Table III**: Experimental parameters and IBM quantum hardware noise profiles.
    - **Table IV**: Restoration performance (PSNR and SSIM) across quantum and classical pipelines with mean $\pm$ std over 5 runs.
  - **Algorithm 1**: Full pseudocode in `algorithm2e`.
  - AI-use declaration, author contributions, and GitHub repository link.
- **`references.bib`**: Exactly 20 real, verified IEEE and leading journal publications (100% cited in text).

---

## Overleaf Setup Instructions

1. **Create an Overleaf Project:**
   - Log into [Overleaf](https://www.overleaf.com).
   - Click **New Project** $\to$ **Upload Project** (upload a ZIP of this `paper/` folder, or create a blank project and upload `main.tex` and `references.bib`).
   - Rename the Overleaf project with your assigned group identifier (e.g., `Group05`).

2. **Add Faculty / Editor:**
   - Click the **Share** button in the top-right corner of Overleaf.
   - Add `kiran.khatter@bmu.edu.in` as an **Editor**.

3. **Compile:**
   - Ensure the compiler is set to **pdfLaTeX** (default in Overleaf).
   - TeX Live Version: 2023 or later.
   - Click **Recompile**. All vector diagrams are generated in native TikZ and will render cleanly at 300+ DPI with zero external image path dependencies.

4. **Verify Final Checklist:**
   - [x] Single column, A4, 1-inch margins, Times 12 pt.
   - [x] Text fully justified, no `\raggedright`, no `\newpage` before `\section`.
   - [x] Length: ~4,987 words (Target: 4,500–5,500 words).
   - [x] Figures and tables: Fig captions below, Table captions above, numbered as Fig. 1 and Table I.
   - [x] References: 20 verified IEEE entries in `references.bib`, all cited.
   - [x] Code link included: `https://github.com/ojhaprathmesh/QIP_Repo`.
   - [x] AI-Use Declaration and Individual Contribution Statement included.
   - [x] Due Date: 18 November 2026, 11:59 pm.
