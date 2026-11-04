# Laoshifu · Chinese divination for your AI agent

[中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md)

A free, local agent skill for exploring traditional Chinese birth charts and I Ching questions. Start with a complete synthetic example: this skill requires no birth details, account or payment for the preview.

Laoshifu combines **BaZi + Zi Wei Dou Shu** for birth readings, or **Liu Yao + Qi Men Dun Jia** for a specific question. The methods are read separately and reconciled, with disagreements and missing evidence kept visible. These are traditional interpretations, not scientifically established predictions.

## Try it before sharing anything personal

Download or clone the repository and run a fixed preview from its directory:

```sh
git clone https://github.com/william22820785-cmyk/laoshifu.git
cd laoshifu
python scripts/preview_examples.py --example contract --lang en
```

Use `--example birth` for the birth example, or `--list` to list both. Use `--lang es`, `--lang pt-BR` or `--lang zh` for the other shipped translations. A preview needs only Python; personal chart calculation also needs Node.js and a compatible agent. Use `python3` if that is your system's Python command.

The examples are **fixed synthetic cases**, not customer testimonials. The translated previews verify both their source chart/review bundle and their translation checksums. They do not collect input, create a personal session, call a network service or start a payment.

## Use it with an agent

Use a local agent that can load a `SKILL.md` skill and execute Python and Node.js. Python 3.11+ and Node.js 20+ are recommended. Point the agent at the absolute path to this repository's [SKILL.md](SKILL.md), or install the repository into the skill directory documented by your host. There is no universal install location across hosts. Do not import just `SKILL.md`: keep its scripts, engine, examples and references together.

Start with this explicit prompt:

> Use Laoshifu from this folder's SKILL.md. Reply in English. Show the fixed contract example with --lang en first. Do not ask for my birth details or start a personal session for this preview.

If you choose a personal reading later:

> I explicitly want a traditional Chinese divination reading about [one question and its deadline]. First explain what information you need and how the local session is saved.

The skill only begins personal divination after an explicit request. Before collecting personal details or writing case artifacts, the agent shows the actual local storage path, expiry and cleanup steps, then asks for consent. The default session lifetime is 24 hours. **Expiry stops further use; it does not automatically delete files.** Cleanup requires a preview and confirmation. Your chat provider's processing, chat history and backups are separate from this local tool.

## Languages and birthplaces

English, Spanish, Portuguese and Chinese have shipped onboarding and fixed previews. The AI can explain personal readings in your preferred language; that depends on the host model. Calculation labels and some audit output retain their Chinese source text. Translation coverage does not mean every host, language or location has been tested.

For overseas birth readings, provide the **birth city and country, local date and clock time**. Use ISO dates (YYYY-MM-DD) to avoid month/day ambiguity. The international route resolves the historical IANA time zone and applies the package's true-solar-time convention. It does not assume UTC+8 or today's UTC offset. Unknown locations need a verified IANA zone and longitude. Ambiguous or nonexistent times at daylight-saving transitions stop for clarification.

Windows and other systems without an IANA database need this small dependency, installed into the Python environment used by your agent:

```sh
python -m pip install -r requirements-international.txt
```

Event calculations accept UTC offsets in 15-minute steps, including +5.5 and +5.75. Check the offset at the question's location and date. Solar-term boundaries and other calendar conventions still need careful review; this release does not certify every historical birthplace.

## For reviewers

Try the birth and contract previews, compare two languages, then inspect the input and review files in [examples](examples). The [reviewer guide](references/REVIEWER-GUIDE.md) lists specific things to test and how to report a problem without posting personal data. Independent criticism is welcome. There is no request for a positive review, purchase or affiliate signup.

## Cost and version

**The GitHub edition is free.** It has no checkout, payment key or paid account requirement. Your AI host may charge its own model or subscription fees. Overseas payment options for a future paid service are undecided and do not affect access to this edition.

Skill release: **4.4.2**. Chart engine: **4.2.0**; this update improves localization and input handling, without claiming better predictive accuracy. See [changes](CHANGELOG.md), [Chinese usage details](references/TRY-IT.md), [cross-cultural rules](references/INTERNATIONAL.md), and [license](LICENSE.txt).
