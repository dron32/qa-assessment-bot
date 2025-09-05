PROMPT_TEMPLATE = (
    "Ты — помогаешь сотруднику формулировать краткие, конкретные ответы по компетенциям QA. "
    "Тон: профессиональный, доброжелательный, без жаргона. Ограничение — до 120 слов. "
    "Верни JSON по схеме: {outline:str, example:str, bullet_points:list[str](3..5, <=120)}."
)

PROMPT_REFINE = (
    "Перепиши текст короче и яснее, сохрани факты, убери воду, предложи улучшения. "
    "Верни JSON: {refined:str, improvement_hints:list[str](2..6)}."
)

PROMPT_CONFLICTS = (
    "Получаешь списки пунктов self и peer. Найди дубликаты (похожие по смыслу) и противоречия (взаимоисключающие). "
    "Верни JSON: {duplicates:list[list[int]], contradictions:list[{self_idx:int, peer_idx:int, reason:str}]}."
)

PROMPT_SUMMARY = (
    "Сделай короткий, практичный summary сотрудника: 3 сильные стороны, 3 зоны роста, 3 конкретных шага (SMART, ≤ 90 дней). Без PII. "
    "Верни JSON: {strengths:list[str](3), areas_for_growth:list[str](3), next_steps:list[str](3)}."
)


