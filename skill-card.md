## Description:

算命老师傅 provides Chinese-language fortune-telling consultations for natal readings and event divination, using birth details or question context to produce conversational judgments, timing guidance, and practical next steps.

This skill is ready for commercial/non-commercial use.

## Publisher:

[william22820785-cmyk](https://clawhub.ai/user/william22820785-cmyk)

### License/Terms of Use:

MIT-0

## Use Case:

External users use this skill for Chinese-language fortune-telling conversations about long-term life patterns, relationships, career, wealth, timing, and specific event outcomes. Agents use it to gather necessary context, run bundled charting or divination workflows, and return concise conversational guidance rather than a technical report.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Local scripts can write generated files that contain birth date, birth time, gender, location, timezone, and personal question data.

Mitigation: Review before installing, keep generated chart and fusion files private, and delete those files when they are no longer needed.

Risk: The security review reports executable local script behavior and unclear scoping for imported local skill code.

Mitigation: Review and scan the skill before deployment, and verify that any referenced local skill directories are trusted before using event-divination workflows.

Risk: Fortune-telling responses may be misleading if treated as professional medical, legal, financial, or safety guidance.

Mitigation: Present outputs as entertainment or cultural reflection and route high-stakes decisions to qualified professionals.

## Reference(s):

- [ClawHub skill page](https://clawhub.ai/william22820785-cmyk/skills/skill)
- [Consultation method](references/consultation-method.md)
- [Interpretation method](references/interpretation-method.md)
- [Liuyao method](references/liuyao-method.md)
- [Qimen event engine](scripts/qimen.cjs)
- [Voice and dialogue](references/voice-and-dialogue.md)
- [Consultation plan schema](references/consultation-plan-schema.md)
- [Liuyao plan schema](references/liuyao-plan-schema.md)
- [Third-party component notice](NOTICE)
- [APA Dictionary: Barnum effect](https://dictionary.apa.org/barnum-effect)
- [NIDA OARS communication techniques](https://nida.nih.gov/sites/default/files/oarsessentialcommunicationtechniques.pdf)
- [SPIKES protocol](https://academic.oup.com/oncolo/article/5/4/302/6386019)

## Skill Output:

**Output Type(s):** [text, markdown, shell commands, configuration, guidance]

**Output Format:** [Conversational Markdown text with generated JSON artifacts and command snippets used by the agent.]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Outputs should be treated as entertainment or cultural reflection, not medical, legal, financial, or safety advice.]

## Skill Version(s):

4.0.1 (local portability and 立春 boundary bugfix)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
