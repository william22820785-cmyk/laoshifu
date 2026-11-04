# Independent reviewer guide

Laoshifu is a free local agent skill for traditional Chinese divination. We welcome critical reviews of how it works, how it explains itself, and where it falls short. No purchase, positive coverage, affiliate signup or private birth data is required.

## A short first test

1. Clone the complete repository. Start with --welcome in your language. Can a newcomer understand the cultural invitation and choose a story, a fixed example or a personal reading? Then run both fixed examples with --lang en, --lang es or --lang pt-BR. They are synthetic cases, not customer results.
2. Compare a second language. Does it preserve the same outcome, conditions, uncertainty and distinction between chart interpretation and real facts? Fixed previews show the complete plain-language explanation; inspect the source bundle for the original six-line chart.
3. Ask your agent to explain a term such as BaZi or the “Wealth” role. Is it understandable without importing assumptions from Western astrology or making a money promise?
4. If you explicitly choose a personal reading, check that the agent explains the actual local session path, expiry and cleanup before collecting details. Ordinary advice requests should not trigger a birth-data request.
5. For an overseas synthetic test, check historical time-zone metadata and birthplace handling. Try an ambiguous DST hour or an unknown city: the agent should stop for clarification. Keep personal details out of public bug reports.

## What a review can establish

Installation friction, reproducibility of a fixed input, quality of explanations, consistency across languages, honest handling of uncertainty, and whether privacy controls behave as described are all useful observations. A demonstration is not scientific validation of prediction, and two traditional methods agreeing does not establish truth.

The skill needs a compatible local agent plus Python and Node.js for personal calculations. The preview only needs Python. The host may have model fees and its own data handling. Calculation/audit labels retain some Chinese text; the English, Spanish and Portuguese translations have not had independent native-speaker review.

## Reporting

Open a GitHub issue with the skill version, operating system, Python/Node versions, host, language, a synthetic reproduction and expected versus actual behavior. Never attach personal session directories, real birth details, private conversations, credentials or full local paths containing identifying details. Use the supplied synthetic examples where possible.

If you cover the project, link to the GitHub repository and identify which version you tested. Please describe limitations in your own words. This invitation is for voluntary, unpaid independent testing; no sponsorship payment or benefit beyond the same free public software is promised.

## Noun-based clarity rule

Specialist noun occurrences must be below 14% of all noun occurrences. Repeated mentions count repeatedly; a fixed multiword technical name counts as one noun. Adjectives, verbs and other non-nouns do not enlarge the denominator. Review noun annotations in the actual language before checking the arithmetic; a matching hash does not prove that POS classification is linguistically correct. Welcome ledgers record host language review and still welcome independent native-speaker correction. Current delivery commands require both --language and --nounAudit.
