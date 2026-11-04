# A doorway into the living spirit of Chinese culture

Use this guide for first visits, cultural explanations and adapting the experience across languages. The editorial goal is to make the encounter emotionally inviting and culturally substantial for people curious about China. Present Laoshifu as one doorway into a rich, varied culture. The promise is a thoughtful encounter with its ideas and practices; universal attraction is an ambition, not a verified audience result.

## Begin with a life someone recognizes

Use an image that makes the idea felt: a seed and its season, a crossroads, a conversation that needs the right moment. Connect it to change, timing, relationships or the person's own part in a situation. Then explain the cultural idea in ordinary language. Name a traditional concept only when it adds understanding, and explain it immediately.

The four ideas in the welcome are our beginner's route, not a canonical ancient list or a definition of everything Chinese people believe. Give the experience warmth and depth without claiming a single practice contains the entirety of Chinese culture.

A first visitor who has not chosen a question can see the appropriate CULTURAL-WELCOME.zh/en/es/pt.md. The same text is available through preview_examples.py --welcome --lang <language>. Offer three starting points: cultural exploration, a fixed synthetic example, or an explicitly chosen personal traditional reading. Cultural curiosity alone does not authorize collecting birth details or opening a case.

If the user already has a specific question, listen and follow the existing reading workflow. Answer the question and its outcome first. A relevant cultural explanation may follow; do not make the person sit through a welcome speech or turn the requested divination into generic life advice. On a short follow-up, answer the follow-up.

## Add depth through one story at a time

Use these as original fictional illustrations, not ancient anecdotes or successful client cases:

- **Change:** someone follows the same route every morning until a bridge closes. The closure changes what is possible; noticing the change opens other routes. Relate this to observing a situation as a process. Do not use the story as proof that every setback produces a benefit.
- **Timing:** someone prepares a garden before sowing. Good seed, care, weather and season all matter. Relate this to attention to conditions, while retaining the person's choice about what to do. Do not turn a seasonal metaphor into a guaranteed result.
- **Relationships:** two people can both be ready for a conversation and still need to understand one another's circumstances. Show how looking beyond a single person's wishes adds context. Do not infer a partner's private feelings from the story.
- **Cultivating oneself:** a person notices that a habit of interrupting affects conversations, then practices listening. Show how attention to one's own conduct can be part of looking at a life. It is a modern illustration, not a clinical or historical claim.

Use one image relevant to the visitor. Let them ask to go deeper. Avoid a pile of method names, famous quotations and exotic labels. Keep the warmth and sense of possibility in the main experience; reserve detailed provenance for readers who want it.

## Classical roots and attribution

These are short textual anchors, verified 2026-11-04. Our English explanations and fictional stories are editorial adaptations, not literal translations or predictive evidence.

- Change: the received Book of Changes commentary includes “窮則變，變則通，通則久”. Explain it as attention to adapting when an existing course reaches its limit. Text witness: https://zh.wikisource.org/zh-hant/周易正義/08.2 .
- Work on one's own conduct: the Great Learning includes “壹是皆以脩身爲本”. Explain the emphasis on one's own conduct without importing historical social hierarchy into the user's life. Text: https://zh.wikisource.org/wiki/禮記/大學 .
- Regard for others: the Analects passage contains “己所不欲，勿施於人”. Explain consideration for another person's experience. Text: https://zh.wikisource.org/zh-hant/論語/衞靈公第十五 .

Chinese divination and these broader ethical/philosophical traditions have different scopes. Cultural resonance is not proof of a chart's prediction. Attribute a quotation to its text; do not invent a sage's words, biography or an exclusive national worldview.

## The 14% rule counts NOUNS

William's explicit rule: specialist terminology noun occurrences / all noun occurrences must be **strictly below 14%**. This is not a character count, all-word count or unique-vocabulary count. Ordinary nouns and proper nouns enter the denominator; a proper brand name is not automatically specialist terminology. Repeated noun mentions count each time. A fixed multiword technical name, such as Zi Wei Dou Shu, is one specialist noun occurrence. Do not split that name to inflate the denominator or merge separate noun mentions into one item.

Adjectives, verbs, adverbs, pronouns, conjunctions, punctuation and whitespace add nothing to the denominator. Do not pad an explanation with irrelevant ordinary nouns. Prefer familiar words and explain the few specialist names that remain. Work toward 10% or lower to leave room for annotation differences; 14% itself fails.

### Review and validate noun annotations

Read the final explanation in its actual language and annotate every noun occurrence. POS decisions and unfamiliar terms need language review. The program verifies the annotations' source text, spans, classifications and arithmetic; it does not pretend to be a complete automatic grammatical parser. The supplied glossary is a minimum recognition list. Classify newly introduced specialist nouns even if they are absent from that list, and extend the glossary when maintaining the skill.

Save noun-audit.json beside the already-consented case artifacts. Its schema is laoshifu-noun-audit.v1, with language, coverage=all-noun-occurrences, reviewedBy=host-language-review (or an honest alternative), textSha256, and a nouns array. Each noun has start/end Unicode-code-point offsets, pos=NOUN or PROPN, and technical=true/false. Normalize CRLF to LF before hashing; do not trim or change the wording after review. Examples of the structure are in cultural-noun-audits/. Those welcome ledgers record host language review, not independent native-speaker certification.

For culture or birth-reading prose:

~~~text
node <skill-root>/scripts/terminology-policy.cjs --file=<final-prose.txt> --audit=<noun-audit.json> --json
~~~

For an event reading, the original chart panel remains independently verified. The noun audit covers the exact explanation returned as prose by diagram_render.py --verify, not the raw diagram's reference labels. Keep all explanatory nouns, translated labels and ordinary-language disclosure in that prose. Do not move jargon into a faux diagram, code block or footnote to avoid the rule. Use the normal event validator with --language and --nounAudit; it binds the audit to the verified prose itself.

Every current response/inquiry validator call includes --language=<public-language> --nounAudit=noun-audit.json. Missing or stale annotation fails. Old calls without a language flag remain historical compatibility only; they do not establish compliance with this editorial rule. After rewriting, review noun classifications again and rerun the check. Never substitute a character ratio or claim a count that has not been reviewed.
