# Language and cross-cultural operation

Read this reference for any non-Chinese conversation, overseas birthplace, or question about language. It supplements the existing chart, dual-review and privacy requirements.

## Cultural entry and plain language

First read [Cultural narrative and noun-based terminology limit](CULTURAL-NARRATIVE.md). Lead first visits with a welcoming doorway into the spirit of Chinese culture, using familiar situations and one cultural idea at a time. The shipped welcome supports --welcome --lang zh/en/es/pt. Specialist noun occurrences must be below 14% of all noun occurrences; language review and a source-bound noun audit are required. Preserve the direct answer when a user already has a concrete question.

## Historical depth, legend and invitation

A first introduction of any method must include its long historical background and inherited legendary colour; read [History and legend](HISTORY-AND-LEGEND.md). In conversation, add a concise cultural aside when it illuminates the user’s question or curiosity. The public invitation should carry cultural confidence and a sense of participation, using William’s supplied campaign frame directly. Do not add a separate trend-investigation step to this writing task.

## Conversation and consent

Use the user's language from the first response, including the storage notice and uncertainty. Ask for a language only when it is unclear. Use a calm, experienced, plain-spoken voice; do not invent an elderly practitioner's biography, years of practice, client history or supernatural authority.

A request to inspect this skill, translate it, see an example or get ordinary advice does not authorize personal divination. For a personal reading, require the same explicit request and storage consent in the user's language. Translate the actual session notice accurately; preserve its real absolute path, expiry, cleanup facts and notice hash. Expiry is not automatic deletion. Host-model processing and chat history are outside the local session's cleanup.

## Preview routing

Shipped fixed preview languages are zh, en, es and pt. Regional tags such as en-US, es-MX and pt-BR resolve to their base language. Run:

```text
python <skill-root>/scripts/preview_examples.py --example contract --lang en
python <skill-root>/scripts/preview_examples.py --example birth --lang pt-BR
```

Show the verified output and its synthetic-example notice. Do not create a personal session, ask for birth data or call a paid service for a preview. On a checksum or missing-file error, stop and report the preview failure. For another requested language, first obtain a verified English preview, then label your output as an agent translation of that fixed synthetic example. Retain all lines, conditions and uncertainty; do not present it as a shipped or independently verified translation. The CLI itself rejects unsupported language tags.

## Cultural interpretation

Introduce each method briefly when relevant: BaZi = Four Pillars birth chart; Zi Wei Dou Shu = a traditional Chinese star-chart system; Liu Yao = six-line I Ching divination; Qi Men Dun Jia = a traditional time-based symbolic chart. Do not map them to a Western zodiac sign, tarot card or religious belief as though they were equivalent.

Explain a term by its role in this question, with Chinese or pinyin beside it only if useful for checking. For example, the traditional “Officer/Ghost” role does not establish a literal ghost, crime or danger; “Wealth” is a chart role, not a promise of money; “Spouse Palace” does not establish someone's sexuality, marital status or future partner. Avoid fear, curses, fatalism and rituals sold as remedies. Never infer family structure, gender identity, religion or beliefs from a name or birthplace.

Lead with the actual interpretation, its conditions and what remains unresolved. Separate symbolic interpretation from verified facts. Keep disagreements between the two methods, confidence limits and missing information when translating. A traditional role is not a diagnosis or an established event. A user may treat the material as cultural exploration without accepting its cosmology.

## Dates and birthplaces

Use YYYY-MM-DD and an explicit local clock time. Ask whether the date is Gregorian or a named lunar calendar; an unspecified “lunar date” outside China is not automatically a Chinese lunar date. An unknown birth hour stays unknown. The engine's male/female input is a traditional calculation parameter: explain it only if needed and let the user choose a supported convention; do not infer it from a name.

For overseas birth charts use the existing private session run entrypoint with these birth parameters, plus the user's confirmed date and time:

```text
--market=international --birthPlace=<city,country> --trueSolarTime=true
```

Quote paths and place names for the active shell. The offline city aliases are limited. If a place cannot be resolved, get a verified IANA identifier and longitude and pass both --birthTimezone and --longitude. Never guess a longitude or silently substitute a nearby city. Historical offsets come from the birthplace's zone on that date, including DST, not the machine's zone or the user's current residence. Missing IANA data requires requirements-international.txt in the active Python environment. DST gaps and repeated hours must be resolved before a chart is generated; the current birth route does not choose a fold for the user. Retain the calculated civil and solar time in the audit record; disclose boundary and convention limits in ordinary language.

For event readings, confirm the question's location, local date/time and UTC offset at that instant. Use --timeBasis=local and --timeZone with that offset, including quarter-hour offsets such as 5.5 and 5.75. Do not use the birth city's zone for an unrelated present-day event.

## Preserve calculation and delivery integrity

Do not translate JSON keys, IDs, enum values, hashes, source pointers or underlying chart facts. Reader claims and final prose can use the user's language; both readers and the reconciled response must use the same frozen chart. Existing validators still run. Do not switch to a Chinese answer just to conceal a failed check, drop source links, alter certainty or bypass the private-session gate.

Some required diagram text and time-basis disclosures retain Chinese source labels. Explain them alongside a translation, keeping the exact source text where the validator requires it. Tell a reviewer honestly that calculation/audit labels are not fully localized. Structured validation checks consistency and provenance; it does not prove predictive accuracy or certify translation quality.

## Free edition

This GitHub edition has no payment prerequisite or upsell step. Explain the host's possible model costs separately. Future international paid-service checkout is undecided. Do not route overseas users to domestic payment flows or imply that payment improves predictive accuracy.
