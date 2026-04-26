# EBAY — Changelog

*Append-only. Most recent entry first. Format defined in CLAUDE.md.*

---

## [2026-04-26] — v2.6+v2.7+v2.8 Retrofit (Primary-source synthesis depth + page-output discipline)

**Trigger**: Schema retrofit pass applying CLAUDE.md v2.6 (Rules #19–#20: shareholder-letter + 10-K MD&A primary-source synthesis), v2.7 (5-year 10-K + letter baselines, quarterly-letter Pattern B substitution), and v2.8 (Rules #21–#26: synthesis over transcription, output discipline, moat consolidation, competitive-landscape integration, risk-factor materiality filter, R/R discipline). EBAY was on v2.5 and was missing the multi-year primary-source baselines.

**Sources reviewed (newly fetched / referenced)**:
- 10-K FY2025 (filed 2026-02-19) — `raw/EBAY/filings/EBAY-10K-FY2025.url`
- 10-K FY2024, FY2023, FY2022, FY2021 — SEC EDGAR HTML (URL pointer files in `raw/EBAY/filings/`)
- Q4 2025 / FY2025 earnings PR (PRNewswire)
- Yahoo Finance live price endpoint (2026-04-26)
- MarketBeat / Benzinga / TipRanks — analyst consensus April 2026
- Stocktitan FY2025 10-K analysis (used as supplementary primary-source reference for Item 1A summary; 10-K cited as underlying source)
- Sacra (Whatnot scale), Statista (C2C TAM) — competitive-landscape inputs

**Letter pattern**: Pattern C (per Core Rule #19) — eBay does not publish a standalone annual or quarterly shareholder letter. Iannone's commentary lives in quarterly earnings PRs, transcripts, and DEF 14A intro letters. Pattern C gap documented in `raw/EBAY/shareholder-letters/PATTERN_C_NOTE.md`. Section 6 RMC drew from FY2021–FY2025 quarterly earnings PR commentary archive + 10-K FY2025 verbatim quotes.

### What Changed (sections refreshed)

- **Header**: Schema v2.5 → v2.8; Last Updated 2026-04-25 → 2026-04-26.
- **Summary**: Refreshed to v2.8 format — 10 emoji-tagged bullets, moat verdict line per Rule #23, R/R figure per Rule #26.
- **Business Overview**: Tightened; removed standalone "Moat Assessment" block per Rule #23 (moat detail now lives only in Section 5).
- **Pivotal Investment Question**: Re-framed around the genuinely new agentic-commerce risk vector vs. the legacy "Amazon erosion" framing.
- **Section 1**: Refreshed framing in light of agentic-commerce question.
- **Section 2**: Added `### Primary Source: 10-K Segment Detail (FY2021 → FY2025)` subsection per Rule #20 — multi-year MD&A synthesis on take-rate expansion (+200bps in 5 yrs), active-buyer base inflection (132M → 134M → 135M), Focus Categories ~30% of GMV in FY25 vs. "investing" framing in FY22.
- **Section 4**: Added explicit advertising-revenue transparency-gap callout.
- **Section 5**: Per Rule #23 + #24 — added mandatory `### Competitive Landscape` subsection with full peer table (AMZN, MELI, ETSY, Vinted, Whatnot, StockX, Poshmark, Mercari, Depop, Facebook Marketplace, Fanatics) including market share / scale and threat-vector reads. Added agentic-commerce as new vulnerability.
- **Section 6**: Added `### Recent Management Commentary — Primary Source Synthesis` subsection per Rule #19 with verbatim quotes mapped to investment relevance + 5-Year Strategic Framework Arc (FY21–FY25) traced through three coherent stages.
- **Section 8**: Per Rule #25 — applied materiality filter, dropped boilerplate (generic cyber, FX, payments regulation), elevated **agentic-commerce / LLM disintermediation** (NEW in FY25 10-K, NOT priced in) and **de minimis exemption removal** (NEW in FY25 10-K, partially priced) as headline risks. Per Rule #21 — replaced 5-Year Risk Factor Evolution table with 2–4-sentence synthesis paragraph naming the genuine multi-year worldview shift.
- **Section 9**: Added agentic-commerce + de minimis macro overlay.
- **Section 10**: Refreshed multiples; trough-vs-normalized framing rewrite.
- **Section 11**: Refreshed price/sentiment/upcoming catalysts as of 2026-04-26 (rolled date forward by 1 day; added EU de minimis July 2026 watch, DEF 14A spring proxy filing).
- **Section 12 (BAIT)**: Refreshed Analytical edge to incorporate active-buyer inflection + transparency-gap modeling edge; added agentic-commerce as new analytical wildcard.
- **Section 13**: Adjusted Bear case to $60 from $70 to incorporate agentic-commerce + de minimis downside; PW EV recalculated.
- **Section 14**: PW EV ~$115 → ~$113 (recomputed). R/R figure framed per Rule #26 — headline ~1.2 : 1 Bull-vs-Bear, secondary 2.4 : 1 Bull-vs-Base.
- **Section 15**: Updated thesis sentence to incorporate agentic-commerce framing; added new thesis-break triggers for AI-search referral decline (>15%), cross-border GMV decline (>10%), Whatnot/Fanatics breakout.

### Thesis Status

- **Overall**: 🟡 **Unchanged** (Hold / Watch). The headline price, recommendation verbs, and zone framework are preserved; primary-source enrichment sharpens the *risk* picture (agentic-commerce + de minimis are genuinely new and not yet priced in) but does not alter the central recommendation.
- **BAIT delta**: A bumped slightly on active-buyer inflection + transparency-gap edge; B/I unchanged (Weak); T unchanged (Moderate). Verdict still Low-Moderate Conviction.
- **Price target delta**: Bull $145 (unchanged) | Base $115 (unchanged) | Bear $70 → **$60** (incorporates agentic-commerce + de minimis tail). PW EV $115 → ~$113.
- **Catalyst & Sentiment delta**: No price action since prior entry (one trading day); analyst consensus and short interest unchanged. New macro watch: EU de minimis July 2026 effective date.

### Recommendation

- **For a non-holder**: 🟡 Watch / selective Initiate — wait for $80 weakness or sustained reacceleration print + early agentic-commerce read.
- **For a current holder**: 🟡 Hold — capital return + reacceleration support; trim toward $115+.

**Next review trigger**: Q1 2026 earnings, early May 2026 (first read on de minimis cross-border GMV impact + any agentic-commerce / AI shopping-agent pilot metrics).

---

## [2026-04-24] — v2.2 Initial Ingest (Workflow A)

**Trigger**: User added EBAY to wiki on 2026-04-24 as part of a 25-ticker expansion batch.

**Sources reviewed**:
- eBay Q4 2025 / FY2025 earnings release (2026-02-18, IR + Motley Fool earnings call transcript)
- eBay Q1 2026 guidance (Seeking Alpha summary, IR press release)
- Yahoo Finance live price endpoint (2026-04-24)
- MarketBeat, Benzinga, TipRanks — analyst consensus April 2026
- Cantor Fitzgerald PT update (2026-04-21)
- Morgan Stanley PT (2026-04-10)
- eBay IR dividend history
- gurufocus / Quiver Quantitative buyback + dividend coverage

### What Changed
- Initial compilation; no prior wiki content
- Live price verified at $97.94 (Yahoo Finance, April 24, 2026)
- Established EBAY as Capital-light platform / two-sided marketplace asset type
- Recorded –8.8% from 52-wk high, +50.7% above 52-wk low (major recovery)
- Documented Q4 2025: revenue +15% (+13% FXN), GMV +10% (+8% FXN), Q4 EPS $1.41 NGAAP
- Documented FY26 framework: GMV ~similar to FY25, op income +8 to +10%
- $2B incremental buyback authorization + 7% dividend raise to $0.31/quarter

### Thesis Status
- **Overall**: Initiated — Neutral to mildly constructive
- **BAIT signal**: Low-Moderate — A + T both Moderate; no asymmetric mispricing
- **PW EV**: ~$115 (3-yr) vs. $97.94 spot = +17% / +5.5% annualized; plus ~1.3% dividend + buyback = ~6.5–7%/yr base case

### Recommendation
- **For a non-holder**: Watch / selective Initiate — Roughly at consensus target; combined ~6% yield makes patient hold reasonable. Better entry below $90.
- **For a current holder**: Hold — Capital return + reacceleration support position. Trim only on rally toward $115+.

**Next review trigger**: Q1 2026 earnings (early May 2026, est.).

---

## [2026-04-24] — Original Overlay Analysis (pre-ingest)

**Trigger**: First full wiki entry — compiled from live web research (Q4 2025 earnings,
eBay IR press releases, MacroTrends, stockanalysis.com, seekingalpha.com).

*Note: This entry predates the v2.2 schema ingest above. Price discrepancy ($103.40 here vs. $97.94 in v2.2) reflects different intraday timing / data source.*

**Data points reviewed**:
- Q4 2025: GMV $21.2B (+8% FX-neutral), Revenue $2.96B (+13%), Non-GAAP EPS $1.41 (+13%)
- FY2025: GMV ~$79B (+6%), Revenue $11.1B (+8%), FCF $1.5B, returned $3.0B to shareholders
- Q1 2026 guidance: GMV $21.5–21.9B (+10–12%), Revenue $3.0–3.05B (+13–15%), Non-GAAP EPS $1.53–1.59
- Depop acquisition: $1.2B from Etsy; $1B GMV, 7M buyers (90% under 34), closing H1 2026
- Buyback: ~$2.8B authorized; $2.5B executed in FY2025
- Stock price ~$103.40; market cap ~$47B; forward P/E ~18x
- Layoffs: ~800 roles (~6%) announced Feb/Mar 2026 to fund AI and Depop investments

### What Changed
- First-time compilation — no prior thesis to compare against
- Key findings:
  - GMV is finally inflecting (+8% Q4, guided +10–12% Q1 2026) after years of stagnation
  - The strategy is coherent: recommerce + focus categories + AI + Depop Gen Z pipeline
  - But the stock has already re-rated: +33% in 12 months; no longer cheap
  - BAIT: Single Overlap — no strong informational or behavioral edge at current price
  - Best entry: $85–$95 on a pullback; current $103 is not a compelling entry

### Thesis Status
- **Overall**: Established — **Medium Conviction**
- **BAIT delta**: B-MODERATE + A-MODERATE + I-WEAK + T-MODERATE = Single Overlap
- **Price targets**:
  - Bull: $130–$150 (25%) | Base: $100–$115 (55%) | Bear: $65–$80 (20%)
  - Probability-weighted EV: ~$108 (~+5% from $103)

### Action
- [ ] Buy more — not at current price; wait for pullback to $85–$95
- [ ] Trim — N/A (no position)
- [ ] Hold — N/A
- [x] Watch — Monitor Q1 2026 earnings (expected ~May 2026); Depop closing; GMV growth trajectory

**Data gaps resolved in v2.2 ingest**:
- ⚠️ Full-year non-GAAP EPS history (FY2021–FY2024)
- ⚠️ Balance sheet detail: cash, debt, net debt
- ⚠️ Geographic revenue breakdown from 10-K
- ⚠️ Active buyer count trend (FY2021–FY2025)
