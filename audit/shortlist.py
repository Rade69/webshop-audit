import pandas as pd

from config import SHORTLIST_TOP_N, BEST_SAMPLE_TOP_N


def select_manual_review_candidates(
    df: pd.DataFrame, top_n: int = SHORTLIST_TOP_N
) -> pd.DataFrame:
    """
    Returns a subset of products that need manual review.

    Priority logic:
    0. Products likely rendered by JavaScript (Tier 0 — highest priority)
    1. Products with indexability flags
    2. Products missing schema
    3. Products missing price
    4. Products with low content
    5. Lowest overall_score among the rest

    The result is deduplicated and capped at top_n.
    """
    if df.empty:
        return df

    # Only consider pages that look like actual product pages
    if "is_likely_product_page" in df.columns:
        product_df = df[df["is_likely_product_page"].astype(bool)]
        if product_df.empty:
            product_df = df  # fallback: use all if nothing qualifies
    else:
        product_df = df

    df = product_df
    collected_indices = set()

    def add_subset(mask: pd.Series, limit: int = None):
        sub = df[mask].index.tolist()
        if limit:
            sub = sub[:limit]
        collected_indices.update(sub)

    # Tier 0: Likely JS-rendered (data unreliable)
    if "is_likely_js_rendered" in df.columns:
        add_subset(df["is_likely_js_rendered"] == True)  # noqa: E712

    # Tier 1: indexability issues
    add_subset(df["indexability_flags"].str.len() > 0)

    # Tier 2: no schema at all
    add_subset(df["suspicious_schema_missing"] == True)  # noqa: E712

    # Tier 3: no price found anywhere
    add_subset(df["suspicious_price_missing"] == True)  # noqa: E712

    # Tier 4: very low content
    add_subset(df["suspicious_low_content"] == True)  # noqa: E712

    # Tier 5: worst overall scores (fill up to top_n)
    remaining_needed = top_n - len(collected_indices)
    if remaining_needed > 0:
        worst = (
            df[~df.index.isin(collected_indices)]
            .sort_values("overall_score", ascending=True)
            .head(remaining_needed)
        )
        collected_indices.update(worst.index.tolist())

    result = df.loc[list(collected_indices)].sort_values("overall_score", ascending=True)
    return result.head(top_n)


def select_best_products_sample(
    df: pd.DataFrame, top_n: int = BEST_SAMPLE_TOP_N
) -> pd.DataFrame:
    """
    Returns a sample of highest-scoring products for comparison.
    
    Prioritizes agent_ready products first (products that are ready for
    AI recommendation), then fills with the best-scoring non-indexability-
    flagged products.
    """
    if df.empty:
        return df

    # Start with agent-ready products (no JS, has price, has schema, score >= 65)
    if "agent_ready" in df.columns:
        agent_ready = df[df["agent_ready"]].copy()
        if len(agent_ready) >= top_n:
            return agent_ready.sort_values("overall_score", ascending=False).head(top_n)
    
    # Combine: agent-ready + non-flagged products
    no_flags = df[df["indexability_flags"].str.len() == 0]
    
    if "agent_ready" in df.columns:
        # Prefer agent-ready products, then others with no flags
        best = pd.concat([
            agent_ready if len(agent_ready) < top_n else agent_ready.head(top_n),
            no_flags[~no_flags.index.isin(agent_ready.index)] if len(agent_ready) < top_n else pd.DataFrame()
        ]).sort_values("overall_score", ascending=False)
    else:
        best = no_flags.sort_values("overall_score", ascending=False)
    
    return best.head(top_n)
