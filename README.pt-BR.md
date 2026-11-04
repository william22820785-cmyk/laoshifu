# Laoshifu · Tradição chinesa no seu agente de IA

[English](README.md) · [中文](README.zh-CN.md) · [Español](README.es.md)

Skill local e gratuito para explorar mapas natais chineses (BaZi + Zi Wei Dou Shu) ou uma pergunta específica com Liu Yao + Qi Men Dun Jia. Interpretações tradicionais não são previsões cientificamente comprovadas.

## Experimente sem compartilhar dados pessoais

Baixe ou clone o repositório completo. Na pasta dele, execute:

```sh
python scripts/preview_examples.py --example contract --lang pt-BR
python scripts/preview_examples.py --example birth --lang pt-BR
```

São exemplos fixos com dados simulados, não depoimentos nem leituras sobre você. A prévia verifica a integridade da fonte e da tradução, não coleta dados, não cria uma sessão pessoal nem inicia pagamentos. Ela só precisa de Python.

## Com o seu agente

Leituras pessoais exigem um agente compatível com SKILL.md que execute Python e Node.js. Recomendamos Python 3.11+ e Node.js 20+. Mantenha todas as pastas do repositório e informe ao agente o caminho absoluto de SKILL.md. A instalação depende do aplicativo usado.

> Use o Laoshifu a partir do SKILL.md desta pasta. Responda em português e mostre primeiro o exemplo fixo de contrato com --lang pt-BR. Não peça meus dados de nascimento nem crie uma sessão pessoal para esta prévia.

Para começar depois uma leitura pessoal, peça explicitamente uma consulta tradicional. Antes de coletar dados ou salvar um caso, o agente deve informar o caminho local, a validade e a limpeza e obter seu consentimento. A sessão vale 24 horas por padrão: ao vencer, seu uso é bloqueado, mas **os arquivos não são apagados automaticamente**. A limpeza exige prévia e confirmação. O histórico e os dados do seu provedor de IA são tratados separadamente.

## Local, horário e idioma

Informe cidade e país de nascimento, data local em YYYY-MM-DD e horário do relógio local. A rota internacional usa o fuso IANA histórico e a convenção de hora solar verdadeira do pacote. Não presume UTC+8 nem o deslocamento atual. Locais fora do catálogo precisam de fuso IANA e longitude verificados. Horários ambíguos em transições de horário de verão exigem esclarecimento.

No Windows e em outros sistemas sem a base IANA, instale no ambiente Python do seu agente:

```sh
python -m pip install -r requirements-international.txt
```

Os exemplos estão traduzidos para português. A explicação pessoal acompanha o idioma escolhido conforme a capacidade do modelo; algumas etiquetas de cálculo e auditoria mantêm o chinês para conferência. Nem todo local ou aplicativo foi testado.

## Preço e avaliações

A edição do GitHub é **gratuita**, sem conta paga nem compra. Seu provedor de IA pode cobrar pelos próprios serviços. Os pagamentos de um possível serviço internacional futuro ainda não foram definidos.

Avaliações independentes, inclusive críticas, são bem-vindas. Veja o [guia de avaliação](references/REVIEWER-GUIDE.md) e não publique dados pessoais nas issues. Versão do skill 4.4.2; motor 4.2.0. [Detalhes em inglês](README.md) · [Licença](LICENSE.txt).
