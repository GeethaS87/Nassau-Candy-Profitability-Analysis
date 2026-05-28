# Nassau Candy Distributor — Profitability Analysis

> Exploratory data analysis and interactive Streamlit dashboard for product line profitability and margin performance at Nassau Candy Distributor.

> 📄 **Published Research:** [Product Line Profitability and Margin Performance Analysis for Nassau Candy Distributor: A Data-Driven Approach Using Exploratory Data Analysis and Interactive Dashboard](https://www.aijfr.com/papers/2026/3/5984.pdf) — *Advanced International Journal for Research (AIJFR), Volume 7, Issue 3, May–June 2026*

> 📊 **Project Presentation:** [Nassau Candy Profitability Analysis — Methodology & Findings](./Nassau_Candy_Profitability_Analysis_Methodology.pptx)

> 🚀 **Live Dashboard:** [ncd-profitability-dashboard.streamlit.app](https://ncd-profitability-dashboard.streamlit.app/)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Research Publication](#research-publication)
- [Problem Statement](#problem-statement)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Analytical Methodology](#analytical-methodology)
- [Dashboard Modules](#dashboard-modules)
- [Key Metrics & KPIs](#key-metrics--kpis)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Key Findings](#key-findings)
- [Live Demo](#live-demo)
- [Presentation](#presentation)
- [Author](#author)

---

## Project Overview

Nassau Candy Distributor operates as a national confectionery distributor, supplying products across the United States and Canada through three product divisions — Chocolate, Sugar, and Other. Despite strong sales volume, the organisation lacked visibility into which product lines were truly profitable versus those merely generating revenue.

This project transforms raw order and transaction data into product-level and division-level profitability intelligence through a full EDA pipeline and a five-module interactive Streamlit dashboard.

---

## Research Publication

This project has been peer-reviewed and published in the **Advanced International Journal for Research (AIJFR)**.

| Field | Details |
|---|---|
| **Title** | Product Line Profitability and Margin Performance Analysis for Nassau Candy Distributor: A Data-Driven Approach Using Exploratory Data Analysis and Interactive Dashboard |
| **Author** | Geetha S |
| **Journal** | Advanced International Journal for Research (AIJFR) |
| **E-ISSN** | 3048-7641 |
| **Volume / Issue** | Volume 7, Issue 3 (May–June 2026) |
| **Paper ID** | AIJFR26035984 |
| **Full Paper** | [https://www.aijfr.com/papers/2026/3/5984.pdf](https://www.aijfr.com/papers/2026/3/5984.pdf) |

**Abstract:** This paper presents a comprehensive data-driven profitability and margin performance analysis conducted on transactional sales data from Nassau Candy Distributor. Using Python-based EDA and an interactive Streamlit dashboard, the study identifies key profitability drivers, margin risks, cost structure inefficiencies, and product portfolio concentration vulnerabilities. Key findings reveal that the Chocolate division dominates revenue at 92.88% share with a 67.45% average gross margin, while Pareto analysis confirms that 5 of 15 products generate 80% of total revenue — representing a significant concentration risk.

---

## Problem Statement

The organisation currently lacks visibility into:

- Which product lines actually generate profit versus those that merely generate revenue
- Which products carry high cost ratios that quietly erode overall portfolio margins
- How profitability varies across the Chocolate, Sugar, and Other divisions
- Which products are candidates for repricing, renegotiation, or discontinuation

Without this intelligence, pricing and portfolio decisions are made without a reliable signal of what is actually working.

---

## Dataset

| Field | Description |
|---|---|
| Row ID | Unique row identifier |
| Order ID | Unique order identifier |
| Order Date | Date of order placement |
| Ship Date | Date of shipment |
| Ship Mode | Shipping method (Standard Class, First Class, Second Class, Same Day) |
| Customer ID | Unique customer identifier |
| Country / Region | Country or region of customer |
| City | Customer city |
| State / Province | Customer state or province |
| Postal Code | Customer postal code |
| Division | Product division (Chocolate, Sugar, Other) |
| Region | Sales region (Interior, Atlantic, Gulf, Pacific) |
| Product ID | Unique product identifier |
| Product Name | Full product name |
| Sales | Total sales value of the order |
| Units | Total units ordered |
| Gross Profit | Gross profit (Sales − Cost) |
| Cost | Cost to manufacture |

**Dataset summary:**

- **Total orders:** 10,194
- **Total revenue:** $141,783.63
- **Total gross profit:** $93,442.80
- **Unique products:** 15
- **Product divisions:** 3 (Chocolate, Sugar, Other)
- **Sales regions:** 4 (Interior, Atlantic, Gulf, Pacific)
- **Order date range:** January 2024 – December 2025
- **Market coverage:** United States and Canada

---

## Project Structure

```
Nassau-Candy-Profitability-Analysis/
│
├── Nassau_Candy_Distributor.csv     # Source dataset
├── nassau_candy_eda.ipynb           # Full exploratory data analysis notebook
├── app.py                           # Streamlit app entry point
│
├── pages_code/
│   ├── utils.py                     # Data loading, filtering, KPI card components
│   ├── p1_overview.py               # Page 1 — Executive Overview
│   ├── p2_product.py                # Page 2 — Product Profitability
│   ├── p3_division.py               # Page 3 — Division Performance
│   ├── p4_pareto.py                 # Page 4 — Profit Concentration (Pareto)
│   └── p5_diagnostics.py            # Page 5 — Cost vs Margin Diagnostics
│
└── requirements.txt                 # Python dependencies
```

---

## Analytical Methodology

### 1. Data Cleaning & Validation
Raw transaction data was cleaned by removing rows where sales, cost, or profit were null or zero. Missing unit counts were imputed to one to prevent division errors. Product labels, divisions, regions, and shipping modes were standardised to title case for consistent grouping.

### 2. Profitability Metric Design
Four core metrics were engineered from the cleaned data:
- **Gross Margin %** — primary health indicator per product and division
- **Profit Per Unit** — surfaces thin-margin, high-volume products
- **Cost Ratio** — flags products where sourcing consumes more than 80% of sales
- **Revenue & Profit Share %** — reveals each product's weight within the broader portfolio

### 3. Product-Level Analysis
Every product was ranked by average gross margin and total profit contribution, then assigned one of six action flags — Maintain, Promote, Monitor, Reprice, Renegotiate Cost, or Discontinue — based on its position in a margin-by-volume matrix. Products were also classified into four strategic quadrants using sales, margin, and portfolio median thresholds.

### 4. Division & Pareto Analysis
Performance was aggregated across divisions using eight KPIs. A grouped bar chart with a margin overlay exposes divisions generating strong revenue without proportional profit. Pareto curves identify how many products drive 80% of total revenue and profit, and a concentration flag is raised when any single product exceeds 20% of divisional or portfolio profit.

### 5. Cost Diagnostics
A cost-vs-sales scatter plot with colour-coded margin zones maps every product into one of three cost actions: Renegotiate Cost, Review Pricing, or Maintain. Margin volatility trends and a strategic assessment complete the diagnostic layer.

---

## Dashboard Modules

The Streamlit dashboard consists of five interactive pages, all sharing a unified sidebar filter system (Division, Date Range, Gross Margin %, Product Search).

| Page | Module | Description |
|---|---|---|
| p1 | Executive Overview | Six KPI cards — Gross Margin %, Profit Per Unit, Revenue Contribution, Profit Contribution, Margin Volatility, and Critical Zone alerts. Supporting charts cover Sales Distribution (Mean vs Median), Division Performance (3 selectable views), Revenue & Profit Pareto by product, KDE Gross Margin % distribution by division, and a Product Margin Summary Table with action flags and colour gradient. |
| p2 | Product Profitability | Gross Margin % leaderboard (all products ranked); Profit Per Unit bar chart; Total Profit Contribution bar chart; Product Quadrant Analysis — Sales vs Margin scatter (4-quadrant: High/Low Sales × High/Low Margin); Product Margin Leaderboard table; Product Portfolio Assessment cards. |
| p3 | Division Performance | Revenue vs Gross Profit by Division (grouped bars); Gross Margin % Distribution by division; Revenue Share vs Profit Share comparison; Average Gross Margin % by Division bar chart; Division Summary Table; Financial Efficiency & Structural Margin Assessment cards. |
| p4 | Profit Concentration | Revenue & Profit Pareto by Product, Region, and State; Order Concentration by State and Canadian Province; Top 20 States chart; State Over-Dependency Risk Table; cumulative 80/20 Pareto curves by division. |
| p5 | Cost vs Margin Diagnostics | Cost vs Sales scatter with colour-coded margin zones; Cost vs Gross Profit chart; Cost Ratio by Product bar chart; Margin Volatility Over Time by Division; Action Recommendations breakdown; Strategic Assessment cards with intervention flags. |

### Dashboard Sidebar Filters
All five modules respond to four unified filters:
- **Division** — All / Chocolate / Sugar / Other
- **Date Range** — Order date picker (January 2024 – December 2025)
- **Gross Margin %** — Slider to filter by margin threshold
- **Product Search** — Multi-select product filter with reset button

---

## Key Metrics & KPIs

| KPI | Formula | Purpose |
|---|---|---|
| Gross Margin % | Gross Profit ÷ Sales × 100 | Primary health indicator per product and division |
| Profit Per Unit | Gross Profit ÷ Units | Surfaces thin-margin, high-volume products |
| Cost Ratio | Cost ÷ Sales × 100 | Flags products where sourcing cost erodes margin (threshold > 80%) |
| Revenue Share % | Product Sales ÷ Total Sales × 100 | Measures each product's weight in total revenue |
| Profit Share % | Product Profit ÷ Total Profit × 100 | Reveals revenue-profit divergence at product level |
| Margin Volatility | Std Dev of Gross Margin over time | Stability signal — high variance signals repricing risk |

**Margin zone thresholds** are calculated dynamically from the full portfolio distribution:

| Zone | Threshold |
|---|---|
| Healthy | ≥ Mean gross margin |
| Watch | ≥ Mean − 1 Std Dev |
| Risk | ≥ Mean − 2 Std Dev |
| Critical | < Mean − 2 Std Dev |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Core Language | Python 3.x |
| Data Wrangling | Pandas, NumPy |
| Visualisation | Plotly, Matplotlib |
| Statistical Analysis | SciPy |
| Dashboard Framework | Streamlit |
| Exploratory Analysis | Jupyter Notebook |

---

## Getting Started

### Prerequisites

Python 3.8 or higher is required.

### Installation

```bash
# Clone the repository
git clone https://github.com/GeehaS87/Nassau-Candy-Profitability-Analysis.git
cd Nassau-Candy-Profitability-Analysis

# Install dependencies
pip install -r requirements.txt
```

### Running the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### Running the EDA Notebook

```bash
jupyter notebook nassau_candy_eda.ipynb
```

### Requirements

```
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.18.0
scipy>=1.11.0
matplotlib>=3.8.0
```

---

## Key Findings

1. **High sales volume does not equal high profitability** — a subset of top-selling products operate near break-even, distorting overall portfolio performance metrics.
2. **Without product-level margin data, pricing and promotional decisions lack a reliable profitability signal** — gross margin visibility is essential for evidence-based decision-making.
3. **Profitability varies sharply across Chocolate, Sugar, and Other divisions** — no structured view previously existed to surface this imbalance.
4. **Some products carry cost ratios above 80%**, meaning sourcing costs consume the majority of sales revenue and quietly erode overall portfolio margins.
5. **A small number of products drive the majority of profit** — the 80/20 Pareto analysis reveals high concentration risk in the portfolio.
6. **Kazookles requires cost renegotiation, not discontinuation** — at a 92.31% cost ratio and 7.69% gross margin, the issue is manufacturing cost, not market demand (96 orders, $1,205.75 revenue).
7. **The Sugar division is underutilised, not unprofitable** — with a 66.61% average gross margin nearly matching Chocolate, Sugar's near-zero revenue ($427.48) signals a distribution and promotion gap, not a product quality problem.

---

## Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ncd-profitability-dashboard.streamlit.app/)

> Click the badge above or visit: [https://ncd-profitability-dashboard.streamlit.app/](https://ncd-profitability-dashboard.streamlit.app/)

---

## Presentation

📊 The project methodology, analytical approach, and key findings are documented in the accompanying PowerPoint presentation:

**[Nassau Candy Profitability Analysis — Methodology & Findings](./Nassau_Candy_Profitability_Analysis_Methodology.pptx)**

The presentation covers:
- Project background and problem statement
- Analytical methodology and KPI design
- Dashboard module walkthrough
- Key findings and business recommendations

---

## Author

**Geetha S**
- GitHub: [@GeehaS87](https://github.com/GeehaS87)
- Published: [AIJFR Volume 7, Issue 3 (May–June 2026)](https://www.aijfr.com/papers/2026/3/5984.pdf)

---

*This project was developed as part of a data analytics capstone focused on product line profitability intelligence for a national confectionery distributor. The findings and methodology have been peer-reviewed and published in the Advanced International Journal for Research (AIJFR), E-ISSN: 3048-7641.*
