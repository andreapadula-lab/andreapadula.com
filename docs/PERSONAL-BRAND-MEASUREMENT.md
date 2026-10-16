# Personal Brand Measurement

This document defines how andreapadula.com is measured. It deliberately separates search visibility, authority, engagement, and real opportunities so that a single vanity metric cannot hide a weak signal.

Private Search Console, analytics, and opportunity data must not be committed to this public repository. Weekly snapshots live in Andrea's local private monitor.

## Reporting cadence

- Weekly operational check: every Monday at 09:00 Europe/Rome.
- Comparison window: latest 28 complete days versus the preceding 28 days.
- Strategic review: quarterly, after at least 28 days of comparable data.
- Every number must carry one of these labels: `measured`, `estimated`, `claimed`, or `not verified`.
- Missing data is reported as `N/D`; it is never converted to zero.

## Five measurement pillars

| Pillar | Weight | Primary sources | Core signals |
| --- | ---: | --- | --- |
| Search visibility | 30% | Google Search Console | indexed priority pages, impressions, clicks, CTR, non-branded queries |
| Authority | 20% | Search Console, backlink source, public SERP review | referring domains, relevant editorial mentions, branded-result ownership |
| Engagement | 20% | Privacy-safe web analytics | article readers, engaged visits, scroll depth, return visits, CTA clicks |
| Opportunities | 20% | Private opportunity log | qualified speaking, board, partnership, podcast, and meeting enquiries |
| Editorial coherence | 10% | Site/content audit | identity consistency, topic focus, cadence, and source quality |

The overall Personal Brand Index is:

```text
PBI = 0.30 × Visibility
    + 0.20 × Authority
    + 0.20 × Engagement
    + 0.20 × Opportunities
    + 0.10 × Editorial Coherence
```

Each pillar is normalized from its quarterly baseline to its quarterly target:

```text
normalized score = clamp((actual - baseline) / (target - baseline) × 100, 0, 100)
```

Targets are set only after the first clean 28-day baseline. An overall PBI must not be reported when weighted data coverage is below 70%; show the available component scores and coverage instead.

## Search and indexation

```text
Indexation rate = indexed sitemap URLs / total sitemap URLs
Priority coverage = indexed strategic URLs / 7
Branded share = impressions from name/domain queries / total impressions
Non-branded reach = impressions and unique queries without name/domain terms
```

The seven strategic URLs are Home, About, Writing, Speaking, Vision, the AI in Financial Services collection, and one current flagship essay.

The `site:` search operator is a smoke test only. It is incomplete and is never used as the indexation source of record; Search Console is authoritative.

## Engagement and conversion

When a privacy-safe analytics property is connected, track these events:

- `contact_email_click`
- `linkedin_click`
- `medium_click`
- `speaking_interest`
- `article_read_75`
- `vision_manifesto_open`

```text
CTA conversion = unique visitors with a CTA event / unique visitors
Article completion proxy = readers with article_read_75 / article readers
```

Analytics must use its own property for andreapadula.com. A Streetbeat property must never be reused.

## Qualified opportunities

Count an opportunity only when it identifies a real person or organization, a relevant context, and a plausible next step. Record source attribution when known.

Suggested categories:

- board position or investor conversation;
- keynote, workshop, roundtable, or podcast;
- strategic partnership or institutional introduction;
- editorial collaboration or media request;
- relevant professional meeting attributable to an article or search result.

## Weekly output

Every report should state:

1. what changed versus the preceding 28 days;
2. which strategic pages changed index state;
3. the top branded and non-branded queries;
4. new referring domains or relevant mentions;
5. engagement and CTA movement, when available;
6. qualified opportunities, when supplied privately;
7. one to three next actions, with no repeated indexing requests or speculative fixes;
8. data coverage and all `N/D` fields.

## Guardrails

- Do not request indexing repeatedly. Re-request only after a material page change or a documented indexing issue.
- Do not publish private Search Console, analytics, email, or opportunity records.
- Do not buy backlinks, fabricate social proof, or optimize content for a keyword that weakens Andrea's actual positioning.
- Preserve existing canonical URLs; use permanent redirects for any future URL change.
- Treat technical health, indexation, visibility, and reputation as separate states.
