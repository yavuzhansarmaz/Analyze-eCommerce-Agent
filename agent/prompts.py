"""
Simple prompt templates for LLM-enhanced data analysis insights.
"""

import json

def enhance_insight_with_llm(llm_client, insight_content: str, analysis_type: str, context: dict = None) -> str:
    """Simple function to enhance insights with LLM."""

    # If no LLM client, return original
    if not llm_client:
        return insight_content

    context = context or {}

    prompt = f"""
You are a business analyst. Please enhance this insight with more context:

Insight: {insight_content}
Analysis Type: {analysis_type}

Additional Context: {json.dumps(context, indent=2)}

Please provide a clearer, more actionable version of this insight.
"""

    try:
        response = llm_client.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        # Log the error but return original insight
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"LLM enhancement failed: {e}")
        return insight_content

def generate_summary_prompt(analysis_type: str, insights: list, context: dict = None) -> str:
    """Generate a simple summary prompt."""

    insights_text = "\n".join([f"- {insight}" for insight in insights[:3]])

    return f"""
Summarize these {analysis_type} insights:

{insights_text}

Context: {json.dumps(context or {}, indent=2)}

Provide a brief business summary.
"""