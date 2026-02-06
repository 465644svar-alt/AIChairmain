# AIChairmain

Проект содержит две реализации арбитража LLM:

- `backend/` + `frontend/` — существующий web-стек.
- `app/` — новый desktop-клиент на **Python + PySide6** с ветвящимся чатом и 3-этапным Council pipeline.

## Desktop app (PySide6)

### Возможности

1. Stage 1: параллельный сбор ответов от GPT / DeepSeek / Claude / Mistral / Groq.
2. Stage 2: анонимный peer-review и парсинг строгого блока `FINAL RANKING`.
3. Aggregation: average-rank агрегатор.
4. Stage 3: chairman synthesis + fallback на лучший Stage1 ответ.
5. Branching chat tree: выбор ветки, возврат к узлу, продолжение от узла.
6. Export чата в `.md` (active branch) и `.json` (full tree).
7. History storage (`data/conversations/*.json`) и вкладка логов.

### Запуск

```bash
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

### Конфигурация

API ключи хранятся только в `.env` (не в git). Поддерживаются переменные:

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `ANTHROPIC_API_KEY`
- `MISTRAL_API_KEY`
- `GROQ_API_KEY`

При необходимости можно переопределить `*_BASE_URL`.

## Тесты

```bash
pytest app/tests -q
```

## License

MIT
