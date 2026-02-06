"""
Core council logic — the three-stage LLM deliberation process.

Stage 1: Each council member independently answers the user's query.
Stage 2: Each member reviews all other responses (anonymized) and ranks them.
Stage 3: The Chairman synthesizes everything into a final answer.
"""

import asyncio
import uuid
import logging

from backend.config import COUNCIL_MEMBERS, CHAIRMAN_MODEL
from backend.models import (
    CouncilSession,
    MemberResponse,
    PeerReview,
    SynthesisResponse,
)
from backend.providers import get_provider
from backend.storage import save_session

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_RESPOND = (
    "You are a knowledgeable AI assistant participating in a council of experts. "
    "Provide a thorough, well-reasoned answer to the user's question. "
    "Be concise but comprehensive."
)

SYSTEM_PROMPT_REVIEW = (
    "You are a critical reviewer in a council of AI experts. "
    "You will be shown several anonymized responses to a question. "
    "Evaluate each response for accuracy, completeness, clarity, and insight. "
    "Rank them from best to worst. For each, provide a brief reasoning. "
    "Respond in valid JSON format:\n"
    '[\n  {"response_label": "Response A", "rank": 1, "reasoning": "..."},\n'
    '  {"response_label": "Response B", "rank": 2, "reasoning": "..."}\n]\n'
    "Only output the JSON array, nothing else."
)

SYSTEM_PROMPT_SYNTHESIS = (
    "You are the Chairman of a council of AI experts. "
    "You have received multiple independent answers to a question, "
    "along with peer reviews from each council member. "
    "Your job is to synthesize all of this into a single, definitive, "
    "high-quality final answer. Take the best ideas from each response, "
    "resolve any disagreements, and produce a clear, comprehensive answer. "
    "Do not mention the council process — just provide the final answer."
)


async def _query_member(member: dict, query: str) -> MemberResponse:
    """Query a single council member."""
    try:
        provider = get_provider(member["provider"])
        text = await provider.generate(
            model=member["model"],
            system_prompt=SYSTEM_PROMPT_RESPOND,
            user_prompt=query,
        )
        return MemberResponse(
            member_id=member["id"],
            member_name=member["name"],
            provider=member["provider"],
            model=member["model"],
            response=text,
        )
    except Exception as e:
        logger.error(f"Error querying {member['name']}: {e}")
        return MemberResponse(
            member_id=member["id"],
            member_name=member["name"],
            provider=member["provider"],
            model=member["model"],
            response="",
            error=str(e),
        )


def _build_review_prompt(query: str, responses: list[MemberResponse], reviewer_id: str) -> str:
    """Build the peer review prompt with anonymized responses."""
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    parts = [f"Original question: {query}\n\nHere are the anonymized responses:\n"]
    idx = 0
    for resp in responses:
        if resp.member_id == reviewer_id:
            continue  # don't review your own response
        if resp.error:
            continue
        parts.append(f"--- Response {labels[idx]} ---\n{resp.response}\n")
        idx += 1
    parts.append("\nPlease rank these responses as instructed.")
    return "\n".join(parts)


async def _review_by_member(
    member: dict, query: str, responses: list[MemberResponse]
) -> PeerReview:
    """One member reviews all other responses."""
    import json as _json

    prompt = _build_review_prompt(query, responses, member["id"])
    try:
        provider = get_provider(member["provider"])
        text = await provider.generate(
            model=member["model"],
            system_prompt=SYSTEM_PROMPT_REVIEW,
            user_prompt=prompt,
        )
        # Parse JSON rankings
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        rankings = _json.loads(text)
        return PeerReview(
            reviewer_id=member["id"],
            reviewer_name=member["name"],
            rankings=rankings,
        )
    except Exception as e:
        logger.error(f"Error in review by {member['name']}: {e}")
        return PeerReview(
            reviewer_id=member["id"],
            reviewer_name=member["name"],
            rankings=[{"error": str(e)}],
        )


def _build_synthesis_prompt(
    query: str,
    responses: list[MemberResponse],
    reviews: list[PeerReview],
) -> str:
    """Build the chairman's synthesis prompt."""
    parts = [f"Original question: {query}\n"]

    parts.append("=== Individual Responses ===\n")
    for resp in responses:
        if resp.error:
            parts.append(f"[{resp.member_name}]: (error — no response)\n")
        else:
            parts.append(f"[{resp.member_name}]:\n{resp.response}\n")

    parts.append("\n=== Peer Reviews ===\n")
    for review in reviews:
        parts.append(f"Review by {review.reviewer_name}:")
        for r in review.rankings:
            parts.append(f"  {r}")
        parts.append("")

    parts.append(
        "\nBased on all responses and peer evaluations, "
        "provide the definitive synthesized answer."
    )
    return "\n".join(parts)


async def run_stage_responses(session: CouncilSession) -> CouncilSession:
    """Stage 1: Gather independent responses from all council members."""
    tasks = [_query_member(m, session.query) for m in COUNCIL_MEMBERS]
    session.responses = await asyncio.gather(*tasks)
    session.stage = "review"
    save_session(session)
    return session


async def run_stage_review(session: CouncilSession) -> CouncilSession:
    """Stage 2: Each member peer-reviews all other responses."""
    tasks = [
        _review_by_member(m, session.query, session.responses)
        for m in COUNCIL_MEMBERS
    ]
    session.reviews = await asyncio.gather(*tasks)
    session.stage = "synthesis"
    save_session(session)
    return session


async def run_stage_synthesis(session: CouncilSession) -> CouncilSession:
    """Stage 3: The Chairman synthesizes the final answer."""
    prompt = _build_synthesis_prompt(session.query, session.responses, session.reviews)
    try:
        provider = get_provider(CHAIRMAN_MODEL["provider"])
        text = await provider.generate(
            model=CHAIRMAN_MODEL["model"],
            system_prompt=SYSTEM_PROMPT_SYNTHESIS,
            user_prompt=prompt,
        )
        session.synthesis = SynthesisResponse(
            chairman_model=CHAIRMAN_MODEL["name"],
            synthesis=text,
        )
    except Exception as e:
        logger.error(f"Chairman synthesis error: {e}")
        session.synthesis = SynthesisResponse(
            chairman_model=CHAIRMAN_MODEL["name"],
            synthesis=f"Error during synthesis: {e}",
        )
    session.stage = "complete"
    save_session(session)
    return session


async def run_full_council(query: str) -> CouncilSession:
    """Run the complete 3-stage council process."""
    session = CouncilSession(
        session_id=str(uuid.uuid4()),
        query=query,
        stage="responses",
    )
    save_session(session)

    session = await run_stage_responses(session)
    session = await run_stage_review(session)
    session = await run_stage_synthesis(session)

    return session
