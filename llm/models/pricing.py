"""
Stores pricing information for different LLM models.

These values should be updated periodically as providers adjust their pricing.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field

class ModelPricing(BaseModel):
    model_name: str
    input_cost_per_million: Optional[float] = Field(default=None) # USD per 1M tokens
    output_cost_per_million: Optional[float] = Field(default=None) # USD per 1M tokens
    cached_input_cost_per_million: Optional[float] = Field(default=None) # USD per 1M tokens
    currency: str = Field(default="USD")
    last_updated: str = Field(default="2026-06-15")

MODEL_PRICING_REGISTRY: Dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing(
        model_name="gpt-4o-mini",
        input_cost_per_million=0.15,
        output_cost_per_million=0.60,
        cached_input_cost_per_million=0.075
    ),
    "gpt-4o": ModelPricing(
        model_name="gpt-4o",
        input_cost_per_million=5.00,
        output_cost_per_million=15.00,
        cached_input_cost_per_million=2.50
    ),
    "gemini-1.5-flash": ModelPricing(
        model_name="gemini-1.5-flash",
        input_cost_per_million=0.075,
        output_cost_per_million=0.30,
        cached_input_cost_per_million=0.0375
    ),
    "gemini-1.5-pro": ModelPricing(
        model_name="gemini-1.5-pro",
        input_cost_per_million=1.25,
        output_cost_per_million=5.00,
        cached_input_cost_per_million=0.625
    ),
    "gemini-2.5-flash": ModelPricing(
        model_name="gemini-2.5-flash",
        input_cost_per_million=0.075,
        output_cost_per_million=0.30,
        cached_input_cost_per_million=0.0375
    ),
    "gemini-2.5-pro": ModelPricing(
        model_name="gemini-2.5-pro",
        input_cost_per_million=1.25,
        output_cost_per_million=5.00,
        cached_input_cost_per_million=0.625
    ),
    "gemini-2.0-flash": ModelPricing(
        model_name="gemini-2.0-flash",
        input_cost_per_million=0.075,
        output_cost_per_million=0.30,
        cached_input_cost_per_million=0.0375
    ),
    "gemini-flash-latest": ModelPricing(
        model_name="gemini-flash-latest",
        input_cost_per_million=0.075,
        output_cost_per_million=0.30,
        cached_input_cost_per_million=0.0375
    ),
    "claude-3-5-sonnet-latest": ModelPricing(
        model_name="claude-3-5-sonnet-latest",
        input_cost_per_million=3.00,
        output_cost_per_million=15.00,
        cached_input_cost_per_million=1.50
    )
}

def get_model_pricing(model_name: str) -> Optional[ModelPricing]:
    """Retrieve pricing info for a model, returning None if unknown."""
    if model_name in MODEL_PRICING_REGISTRY:
        return MODEL_PRICING_REGISTRY[model_name]
    
    for key, pricing in MODEL_PRICING_REGISTRY.items():
        if key in model_name:
            return pricing
            
    return None

def estimate_cost(model_name: str, input_tokens: int, output_tokens: int, cached_tokens: int = 0) -> Optional[float]:
    """Estimate cost of an interaction in USD. Returns None if pricing is unknown."""
    pricing = get_model_pricing(model_name)
    if not pricing:
        return None
        
    if pricing.input_cost_per_million is None or pricing.output_cost_per_million is None:
        return None
        
    cache_cost = (cached_tokens / 1_000_000.0) * (pricing.cached_input_cost_per_million or pricing.input_cost_per_million)
    normal_input_cost = ((input_tokens - cached_tokens) / 1_000_000.0) * pricing.input_cost_per_million
    output_cost = (output_tokens / 1_000_000.0) * pricing.output_cost_per_million
    
    return max(0.0, cache_cost + normal_input_cost + output_cost)
