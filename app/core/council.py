from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import asdict

from .models.providers import AsyncProviderClient
from .prompts import STAGE2_REVIEW_PROMPT_RU, STAGE3_CHAIRMAN_PROMPT_RU
from .types import AggregateRanking, LLMResult, Stage1Result, Stage2Result, Stage2Review, Stage3Result

logger = logging.getLogger("aichairman")

RANK_PATTERN = re.compile(r"^\s*\d+\.\s*Response\s+([A-Z])", flags=re.MULTILINE)
FALLBACK_PATTERN = re.compile(r"Response\s+([A-Z])")


class CouncilOrchestrator:
    def __init__(self, clients: dict[str, AsyncProviderClient], timeout: float = 60.0):
        self.clients = clients
        self.timeout = timeout

    async def run(self, question: str, models: dict[str, str], chairman_provider: str, chairman_model: str) -> dict:
        stage1 = await self.stage1_collect(question, models)
        stage2 = await self.stage2_peer_review(question, stage1)
        stage3 = await self.stage3_chairman(question, stage1, stage2, chairman_provider, chairman_model)
        return {"stage1": asdict(stage1), "stage2": asdict(stage2), "stage3": asdict(stage3)}

    async def stage1_collect(self, question: str, models: dict[str, str]) -> Stage1Result:
        messages = [{"role": "user", "content": question}]
        tasks = [self._chat_with_preflight(p, m, messages) for p, m in models.items() if p in self.clients]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return Stage1Result(question=question, responses=results)

    async def _chat_with_preflight(self, provider: str, model: str, messages: list[dict]) -> LLMResult:
        client = self.clients[provider]
        ok, error, latency, raw = await client.check_connectivity(self.timeout)
        if not ok:
            normalized_error = error or "connectivity check failed"
            if normalized_error != "api key is not configured":
                normalized_error = f"connectivity check failed: {normalized_error}"
            return LLMResult(provider, model, None, normalized_error, latency, raw)
        return await client.chat(model, messages, self.timeout)

    async def stage2_peer_review(self, question: str, stage1: Stage1Result) -> Stage2Result:
        valid = [r for r in stage1.responses if r.content]
        labels = {chr(ord("A") + i): r for i, r in enumerate(valid)}
        answers_block = "\n\n".join([f"Response {label}:\n{res.content}" for label, res in labels.items()])

        reviews: list[Stage2Review] = []
        if not labels:
            empty = AggregateRanking(label_to_model={}, average_ranks={}, aggregate_order=[])
            return Stage2Result(reviews=reviews, aggregate=empty)

        prompt = STAGE2_REVIEW_PROMPT_RU.format(question=question, answers_block=answers_block)
        for reviewer in valid:
            client = self.clients.get(reviewer.provider)
            if not client:
                continue
            review_result = await client.chat(reviewer.model, [{"role": "user", "content": prompt}], self.timeout)
            if review_result.error:
                reviews.append(Stage2Review(reviewer.provider, reviewer.model, None, [], review_result.error))
            else:
                ranking = parse_ranking(review_result.content or "")
                reviews.append(Stage2Review(reviewer.provider, reviewer.model, review_result.content, ranking, None))

        aggregate = aggregate_rankings(reviews, labels)
        return Stage2Result(reviews=reviews, aggregate=aggregate)

    async def stage3_chairman(
        self,
        question: str,
        stage1: Stage1Result,
        stage2: Stage2Result,
        chairman_provider: str,
        chairman_model: str,
    ) -> Stage3Result:
        stage1_block = "\n\n".join([f"{r.provider}/{r.model}: {r.content or r.error}" for r in stage1.responses])
        stage2_block = "\n\n".join([f"{r.reviewer_provider}/{r.reviewer_model}: {r.review_text or r.error}" for r in stage2.reviews])
        aggregate_summary = ", ".join([f"{m}:{v:.2f}" for m, v in stage2.aggregate.average_ranks.items()])

        prompt = STAGE3_CHAIRMAN_PROMPT_RU.format(
            question=question,
            stage1_block=stage1_block,
            stage2_block=stage2_block or "нет данных",
            aggregate_summary=aggregate_summary or "нет данных",
        )

        client = self.clients.get(chairman_provider)
        if not client:
            return Stage3Result(content=None, error=f"chairman provider not configured: {chairman_provider}")

        result = await client.chat(chairman_model, [{"role": "user", "content": prompt}], self.timeout)
        if result.error:
            fallback = pick_best_stage1(stage1, stage2)
            return Stage3Result(content=fallback, error=result.error, used_fallback=True)
        return Stage3Result(content=result.content, error=None)


def parse_ranking(text: str) -> list[str]:
    if "FINAL RANKING" in text:
        section = text.split("FINAL RANKING", 1)[1]
    else:
        section = text
    ranked = RANK_PATTERN.findall(section)
    if not ranked:
        ranked = FALLBACK_PATTERN.findall(section)
    dedup: list[str] = []
    for r in ranked:
        label = r.upper()
        if label not in dedup:
            dedup.append(label)
    return dedup


def aggregate_rankings(reviews: list[Stage2Review], labels: dict[str, LLMResult]) -> AggregateRanking:
    sums = {label: 0.0 for label in labels}
    counts = {label: 0 for label in labels}
    for review in reviews:
        for idx, label in enumerate(review.ranking, start=1):
            if label in sums:
                sums[label] += idx
                counts[label] += 1
    averages = {}
    for label in labels:
        if counts[label] == 0:
            averages[label] = float("inf")
        else:
            averages[label] = sums[label] / counts[label]
    ordered_labels = sorted(averages.keys(), key=lambda x: averages[x])
    model_scores = {f"{labels[l].provider}/{labels[l].model}": averages[l] for l in ordered_labels}
    label_to_model = {l: f"{labels[l].provider}/{labels[l].model}" for l in labels}
    return AggregateRanking(label_to_model=label_to_model, average_ranks=model_scores, aggregate_order=ordered_labels)


def pick_best_stage1(stage1: Stage1Result, stage2: Stage2Result) -> str:
    if stage2.aggregate.aggregate_order:
        best_label = stage2.aggregate.aggregate_order[0]
        model = stage2.aggregate.label_to_model.get(best_label)
        if model:
            for resp in stage1.responses:
                if f"{resp.provider}/{resp.model}" == model and resp.content:
                    return resp.content
    for resp in stage1.responses:
        if resp.content:
            return resp.content
    return "Не удалось получить финальный ответ: все модели завершились с ошибкой."
