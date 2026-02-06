STAGE2_REVIEW_PROMPT_RU = """
Ты арбитр. Оцени анонимные ответы на вопрос пользователя и выдай ранжирование.

Вопрос:
{question}

Ответы:
{answers_block}

Сделай краткий сравнительный анализ качества, точности и практичности.
После анализа ОБЯЗАТЕЛЬНО заверши строго блоком:
FINAL RANKING:
1. Response X
2. Response Y
3. Response Z

Требования:
- В разделе FINAL RANKING не добавляй лишний текст.
- Используй только метки Response A/B/C... .
""".strip()


STAGE3_CHAIRMAN_PROMPT_RU = """
Ты председатель LLM-совета. На основе материалов подготовь итоговый ответ.

Вопрос пользователя:
{question}

Stage 1 (оригинальные ответы):
{stage1_block}

Stage 2 (peer review + rankings):
{stage2_block}

Aggregate ranking summary:
{aggregate_summary}

Сформируй лучший финальный ответ на русском языке.
Если есть неопределённость, явно обозначь риски и предложи безопасные шаги.
""".strip()
