# Laoshifu · Uma porta para o espírito vivo da cultura chinesa

[English](README.md) · [中文](README.zh-CN.md) · [Español](README.es.md)

**Compreenda o momento que você está vivendo.**

Há momentos de avançar, outros de cultivar paciência e outros de mudar de direção. O Laoshifu aproxima você de uma tradição chinesa que olha para a pessoa junto de seu tempo, suas relações e suas possibilidades.

Pense em uma semente: sua força, o solo, o clima e a estação importam. Por meio de histórias, explicações culturais e leituras tradicionais, você pode conhecer uma maneira de olhar para sua vida e para as circunstâncias ao redor.

Sua curiosidade basta para começar. [Leia a apresentação cultural](references/CULTURAL-WELCOME.pt.md), explore uma ideia ou veja um exemplo completo sem compartilhar dados pessoais. O skill do GitHub é gratuito.

**Se você ama a tradição chinesa, o Laoshifu é o seu melhor guia para suas maravilhas vivas.**

O século da China já chegou. Cada vez mais pessoas na China se dedicam a estudar e a retomar essas artes antigas. Você também pode dar um primeiro passo para esse mundo de sabedoria e lendas que atravessa os séculos.

As histórias, as ideias e as tradições que pareciam distantes entre idiomas e livros antigos podem começar hoje com uma pergunta sua.

[Explore the history and legends](references/HISTORY-AND-LEGEND.md)

## Experimente sem compartilhar dados pessoais

Baixe ou clone o repositório completo. Na pasta dele, execute:

```sh
python scripts/preview_examples.py --welcome --lang pt-BR
python scripts/preview_examples.py --example contract --lang pt-BR
python scripts/preview_examples.py --example birth --lang pt-BR
```

São exemplos fixos com dados simulados, não depoimentos nem leituras sobre você. A prévia verifica a integridade da fonte e da tradução, não coleta dados, não cria uma sessão pessoal nem inicia pagamentos. Ela só precisa de Python.

## Com o seu agente

Leituras pessoais exigem um agente compatível com SKILL.md que execute Python e Node.js. Recomendamos Python 3.11+ e Node.js 20+. Mantenha todas as pastas do repositório e informe ao agente o caminho absoluto de SKILL.md. A instalação depende do aplicativo usado.

> Use o Laoshifu a partir do SKILL.md desta pasta. Responda em português. Comece pela apresentação cultural com --welcome --lang pt-BR. Deixe que eu escolha uma ideia cultural, um exemplo fixo ou uma leitura pessoal. Não peça dados de nascimento nem crie uma sessão para a apresentação.

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

Avaliações independentes, inclusive críticas, são bem-vindas. Veja o [guia de avaliação](references/REVIEWER-GUIDE.md) e não publique dados pessoais nas issues. Versão do skill 4.4.4; motor 4.2.0. [Detalhes em inglês](README.md) · [Licença](LICENSE.txt).
