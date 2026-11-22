
from typing import Literal

from pydantic import BaseModel, Field


class AIEntity(BaseModel):
    """Information about one AI startup or AI product."""

    entity_type: Literal["startup", "ai_product"] = Field(
        description="Whether the entity is an AI startup or AI product."
    )

    name: str | None = Field(
        default=None,
        description="Official name of the startup or product."
    )

    website_url: str | None = Field(
        default=None,
        description="Official website URL, if explicitly available."
    )

    description: str | None = Field(
        default=None,
        description="Short description based on the supplied text."
    )

    category: str | None = Field(
        default=None,
        description="AI industry or product category."
    )

    developer: str | None = Field(
        default=None,
        description="Company or developer behind the product."
    )

    pricing_model: str | None = Field(
        default=None,
        description="Pricing information, if explicitly mentioned."
    )

    launch_date: str | None = Field(
        default=None,
        description="Launch date in YYYY-MM-DD format, if available."
    )


class ExtractionResult(BaseModel):
    """Collection of extracted AI entities."""

    entities: list[AIEntity] = Field(
        description="AI startups and AI products identified in the supplied text."
    )
