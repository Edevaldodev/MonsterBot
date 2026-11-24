# Monster Bot — Assistente Groq

Aplicação web local de IA conversacional, criada em Python + Flask + Groq API.
O projeto reúne os conceitos dos seus PDFs: Prompt Engineering, Context Engineering,
memória de curto e longo prazo, Harness Engineering, Tool Calling e testes automatizados.

## Recursos incluídos

- Interface de chat responsiva, tema escuro, conversas recentes e Markdown.
- Respostas em streaming (o texto aparece enquanto é gerado).
- Integração com Groq Chat Completions e seleção de modelo na interface.
- Histórico persistente por conversa em SQLite.
- Memória de longo prazo: salvar, recuperar e excluir informações.
- Ferramentas com Function Calling: calculadora segura, data/hora de São Paulo,
  criar/listar/concluir tarefas e memória.
- Orquestrador com limite de ciclos de ferramentas e validação no servidor.
- Testes automatizados da calculadora.
- Chave de API mantida no servidor em `.env`; não é enviada ao navegador.

## Requisitos

- Windows 10/11
- Python 3.10 ou superior
- Uma chave da Groq API

## Instalação rápida (Windows)

1. Extraia o ZIP em uma pasta, por exemplo `C:\\Users\\Aluno\\Documents\\MonsterBot`.
2. Abra a pasta no VS Code.
3. Dê dois cliques em `run.bat` ou execute no terminal:

   ```powershell
   py -m venv .venv
   .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

4. Copie `.env.example` para `.env` (o `run.bat` faz isso na primeira execução).
5. Abra `.env` e substitua `sua_chave_groq_aqui` pela sua chave Groq.
6. Salve e execute:

   ```powershell
   python main.py
   ```

7. Acesse `http://127.0.0.1:5000`.

## Configurar o modelo

No `.env`, altere `GROQ_MODEL` se desejar. Também é possível selecionar um dos modelos
listados no menu superior. A disponibilidade e os limites dependem da conta e podem mudar.
Se um modelo retornar erro de indisponibilidade, escolha outro modelo disponível no menu
ou consulte a lista atual no painel da Groq.

Modelos sugeridos como ponto de partida:
- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `llama-3.3-70b-versatile`
- `llama-3.1-8b-instant`

## Testes

Com o ambiente virtual ativo:

```powershell
pytest -q
```

Os testes não precisam de chave Groq porque validam as funções locais isoladamente.

## Estrutura

```text
MonsterBot/
├── app/
│   ├── __init__.py
│   ├── agent.py
│   ├── calculator.py
│   ├── database.py
│   ├── routes.py
│   ├── tools.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── app.js
│       └── style.css
├── tests/
│   └── test_tools.py
├── instance/              # criado automaticamente; banco SQLite
├── .env                   # sua chave local; não compartilhar
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── run.bat
```

## Segurança e limites atuais

- Nunca publique seu `.env`, chave Groq ou banco com dados pessoais.
- O `.gitignore` exclui `.env` e arquivos de banco.
- O agente só pode chamar ferramentas explicitamente registradas no backend.
- A calculadora usa uma árvore de sintaxe restrita; não executa Python arbitrário.
- A aplicação é local e não possui autenticação multiusuário para exposição pública.
  Não publique o servidor na internet sem implementar autenticação, HTTPS, proteção CSRF,
  rate limiting e isolamento real de contas.
- A memória salva apenas quando o modelo chama a ferramenta de memória; confira o painel
  e exclua registros que não queira manter.
- O conteúdo das conversas é salvo no SQLite local.

## Próximas evoluções possíveis

Upload e leitura de PDFs, pesquisa web, autenticação, perfis, exportação de conversas,
voz (fala e transcrição) e implantação em servidor são módulos adicionais; não estão
implementados nesta primeira versão.
