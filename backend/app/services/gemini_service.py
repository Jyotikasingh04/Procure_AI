"""
Gemini AI Service.

Generates a procurement summary for buyers after an auction ends.
This service ONLY produces descriptive analysis — participation,
price spread, competition level, bid trends, and observations. It
must NEVER select a winner or recommend a vendor; that decision
belongs to the buyer alone, per the platform's core auction rules.
"""

import os
import statistics
from decimal import Decimal

import google.generativeai as genai
from fastapi import HTTPException, status

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

MANDATORY_CLOSING_LINE = (
    "Final supplier selection should consider delivery capability, "
    "quality, compliance and commercial terms. AI provides analysis only."
)


def _configure_gemini() -> None:
    """
    Configure the Gemini client from the API key in the environment.
    Raises a clear error rather than silently failing if the key is
    missing, since a misconfigured key should never surface as a
    generic 500 to the buyer.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured on the server.",
        )
    genai.configure(api_key=GEMINI_API_KEY)


def _compute_bid_statistics(bid_amounts: list[Decimal]) -> dict:
    """
    Compute the numeric inputs the prompt needs. Done in Python, not
    left to the model, so the summary's numbers are always accurate
    even if the model paraphrases them.
    """
    if not bid_amounts:
        return {
            "lowest_bid": None,
            "highest_bid": None,
            "average_bid": None,
            "num_vendors": 0,
        }

    floats = [float(b) for b in bid_amounts]

    return {
        "lowest_bid": min(floats),
        "highest_bid": max(floats),
        "average_bid": round(statistics.mean(floats), 2),
        "num_vendors": len(floats),
    }


def _build_prompt(
    auction_title: str,
    material_name: str,
    quantity: int,
    unit: str,
    base_price: Decimal,
    duration_display: str,
    num_bids: int,
    stats: dict,
) -> str:
    """
    Build the prompt sent to Gemini. Explicitly instructs the model
    not to name or imply a preferred vendor, and not to declare a
    winner, since vendor identities are intentionally not included
    in the input data at all.
    """
    if stats["num_vendors"] == 0:
        bid_summary_block = "No bids were placed on this auction."
    else:
        bid_summary_block = (
            f"Number of vendors who bid: {stats['num_vendors']}\n"
            f"Total bids submitted: {num_bids}\n"
            f"Lowest bid: {stats['lowest_bid']}\n"
            f"Highest bid: {stats['highest_bid']}\n"
            f"Average bid: {stats['average_bid']}\n"
            f"Base price set by buyer: {base_price}"
        )

    return f"""You are writing a short, professional procurement summary for a
buyer company reviewing a completed reverse-auction event.

Auction: {auction_title}
Material: {material_name}
Quantity: {quantity} {unit}
Auction Duration: {duration_display}

{bid_summary_block}

Write a concise summary covering, where the data supports it:
- Participation level (how many vendors engaged)
- Price spread between lowest and highest bid
- Overall competition level (was it competitive or thin?)
- Any notable bid trends
- General observations about the outcome

Strict rules you must follow:
- Do NOT name, identify, or refer to any specific vendor.
- Do NOT declare, suggest, or imply a winner.
- Do NOT recommend which vendor the buyer should choose.
- Do NOT use phrases like "the best option" or "the recommended vendor."
- Stick to factual, descriptive analysis of the numbers and process only.
- Keep it to 3-5 short paragraphs, plain professional language, no headers or bullet lists.
- Do not include any closing disclaimer yourself — one will be appended separately.
"""


def generate_auction_summary(
    auction_title: str,
    material_name: str,
    quantity: int,
    unit: str,
    base_price: Decimal,
    duration_display: str,
    bid_amounts: list[Decimal],
) -> str:
    """
    Generate a procurement summary for a single ended/awarded auction.

    bid_amounts should be the full list of bid amounts for the
    auction (vendor identities are deliberately not passed in, so the
    model has no way to reference a specific vendor even in error).

    Returns the AI-generated summary with the mandatory closing line
    appended. Raises HTTPException on any Gemini API failure so the
    router can surface a clean error rather than a stack trace.
    """
    _configure_gemini()

    stats = _compute_bid_statistics(bid_amounts)
    num_bids = len(bid_amounts)

    prompt = _build_prompt(
        auction_title=auction_title,
        material_name=material_name,
        quantity=quantity,
        unit=unit,
        base_price=base_price,
        duration_display=duration_display,
        num_bids=num_bids,
        stats=stats,
    )

    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        summary_text = (response.text or "").strip()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini request failed: {exc}",
        ) from exc

    if not summary_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an empty response.",
        )

    return f"{summary_text}\n\n{MANDATORY_CLOSING_LINE}"