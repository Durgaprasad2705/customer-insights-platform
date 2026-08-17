"""Customer Profiles Page — individual customer intelligence with AI suggestions."""

from __future__ import annotations

import math
from datetime import datetime

import pandas as pd
import streamlit as st

from components.kpi_cards import section_title, insight_card
from utils.formatters import fmt_currency, fmt_number, fmt_percent


def _stars(rating: float) -> str:
    full = int(round(rating))
    return "★" * full + "☆" * (5 - full)


def _tier(spend: float) -> tuple[str, str, str]:
    if spend >= 5000: return "Platinum", "#E5C4FF", "💎"
    if spend >= 2000: return "Gold",     "#FFD04D", "🥇"
    if spend >= 500:  return "Silver",   "#B0C4DE", "🥈"
    return "Bronze", "#CD7F32", "🥉"


def _churn_risk(orders: int, rating: float, days_since_last: int) -> tuple[str, str, int]:
    score = 0
    if days_since_last > 180: score += 40
    elif days_since_last > 90: score += 20
    elif days_since_last > 45: score += 10
    if rating < 2.5:   score += 30
    elif rating < 3.5: score += 15
    if orders < 3:     score += 20
    elif orders < 7:   score += 10
    score = min(score, 100)
    if score >= 60: return "High",   "#FF6B8A", score
    if score >= 35: return "Medium", "#FFAD00", score
    return "Low", "#22C55E", score


def _days_since(dates_series: pd.Series) -> int:
    try:
        most_recent = pd.to_datetime(dates_series, errors="coerce").max()
        if pd.isna(most_recent):
            return 999
        return max(0, (datetime.now() - most_recent.to_pydatetime().replace(tzinfo=None)).days)
    except Exception:
        return 999


def _generate_suggestions(
    spend: float, orders: int, avg_order: float, rating: float,
    days_since_last: int, top_category: str, churn_label: str, tier_label: str
) -> list[dict]:
    suggestions: list[dict] = []

    if days_since_last > 120:
        suggestions.append({
            "icon": "🔔", "category": "Re-engagement",
            "title": f"Win back {tier_label} customer — {days_since_last} days inactive",
            "why": (
                f"This customer hasn't purchased in {days_since_last} days. "
                f"Their last average order was {fmt_currency(avg_order)}, making them worth re-activating."
            ),
            "action": (
                f"Send a personalised 'We Miss You' email with a 15% discount "
                f"on {top_category or 'their favourite category'}. "
                f"Follow up with a push notification if no response in 5 days."
            ),
            "impact": "Potential revenue recovery: " + fmt_currency(avg_order * 1.5),
            "priority": "high", "confidence": 0.82,
        })
    elif days_since_last > 60:
        suggestions.append({
            "icon": "📬", "category": "Re-engagement",
            "title": "Customer showing early inactivity signals",
            "why": (
                f"No purchase in the last {days_since_last} days — "
                f"engagement is cooling. Early intervention prevents churn."
            ),
            "action": (
                "Trigger a browse-abandonment or 'Back in stock' campaign. "
                "Include social proof (trending items in their region)."
            ),
            "impact": "Reduces churn probability by ~25%",
            "priority": "medium", "confidence": 0.74,
        })

    if avg_order > 0 and orders >= 3:
        upsell_target = avg_order * 1.35
        suggestions.append({
            "icon": "🚀", "category": "Upsell Opportunity",
            "title": f"Upsell potential — avg order could reach {fmt_currency(upsell_target)}",
            "why": (
                f"Customer has {orders} orders with a healthy avg of {fmt_currency(avg_order)}. "
                f"Repeat buyers are 60% more likely to accept premium product recommendations."
            ),
            "action": (
                f"Recommend premium / bundle versions in {top_category or 'top categories'} at checkout. "
                f"Show savings on multi-buy offers (e.g. Buy 2 Get 15% off)."
            ),
            "impact": f"Avg order lift: +{fmt_currency(upsell_target - avg_order)}",
            "priority": "medium", "confidence": 0.78,
        })

    tier_thresholds = {"Bronze": 500, "Silver": 2000, "Gold": 5000, "Platinum": None}
    next_tier_map   = {"Bronze": "Silver", "Silver": "Gold", "Gold": "Platinum"}
    if tier_label in next_tier_map:
        next_tier = next_tier_map[tier_label]
        target_spend = tier_thresholds[next_tier]
        if target_spend is not None:
            gap = target_spend - spend
            if 0 < gap < spend * 0.8:
                suggestions.append({
                    "icon": "⭐", "category": "Loyalty Growth",
                    "title": f"Only {fmt_currency(gap)} away from {next_tier} status!",
                    "why": (
                        f"Customer is at {fmt_currency(spend)} lifetime spend. "
                        f"{next_tier} unlocks exclusive perks and drives long-term retention."
                    ),
                    "action": (
                        f"Send a loyalty progress notification: "
                        f"'You're {fmt_currency(gap)} away from {next_tier}! "
                        f"Here's a curated selection to get you there.' "
                        f"Include a limited-time bonus points event."
                    ),
                    "impact": "LTV increase ~20% post tier upgrade",
                    "priority": "low", "confidence": 0.88,
                })

    if rating > 0 and rating < 3.0:
        suggestions.append({
            "icon": "🛠️", "category": "Satisfaction Recovery",
            "title": f"Low satisfaction alert — avg rating {rating:.1f} ★",
            "why": (
                f"Average rating of {rating:.1f}/5 indicates negative experiences. "
                f"Unhappy customers are 4× more likely to churn and share bad reviews."
            ),
            "action": (
                "Trigger a personal apology email from the support team. "
                "Offer a complimentary service credit or no-questions-asked return on their last order. "
                "Assign to VIP support queue."
            ),
            "impact": "Saves ~" + fmt_currency(spend * 0.4) + " in potential lost LTV",
            "priority": "high", "confidence": 0.91,
        })
    elif rating > 0 and rating < 4.0:
        suggestions.append({
            "icon": "💬", "category": "Experience Improvement",
            "title": "Moderate satisfaction — room for experience uplift",
            "why": (
                f"Rating of {rating:.1f}/5 suggests occasional friction. "
                f"A small improvement in satisfaction can meaningfully lift repeat purchases."
            ),
            "action": (
                "Send a short NPS survey (2 questions) to identify pain points. "
                "Offer a surprise reward (free shipping on next order) as a goodwill gesture."
            ),
            "impact": "Rating improvement → 15% higher repeat purchase rate",
            "priority": "medium", "confidence": 0.70,
        })

    if spend >= 2000 and rating >= 4.0:
        suggestions.append({
            "icon": "🎁", "category": "VIP Reward",
            "title": "High-value loyal customer — reward to deepen bond",
            "why": (
                f"With {fmt_currency(spend)} lifetime spend and a {rating:.1f}★ rating, "
                f"this customer is a brand ambassador. Rewarding them costs little "
                f"but yields outsized word-of-mouth value."
            ),
            "action": (
                "Invite to VIP early-access sale (24h before general public). "
                "Send a personalised gift (branded merchandise or exclusive discount). "
                "Feature in loyalty programme case study with consent."
            ),
            "impact": "Referral value: 3–5 new customers on avg",
            "priority": "low", "confidence": 0.85,
        })

    if orders == 1:
        suggestions.append({
            "icon": "🌱", "category": "New Customer Nurture",
            "title": "First-time buyer — convert to repeat customer now",
            "why": (
                "The highest drop-off happens between order 1 and 2. "
                "Nurturing within the first 30 days triples the chance of a second purchase."
            ),
            "action": (
                f"Launch a 7-day onboarding sequence: Day 1 — thank you + tips, "
                f"Day 4 — curated picks from {top_category or 'their category'}, "
                f"Day 7 — 10% next-order voucher expiring in 14 days."
            ),
            "impact": "2nd purchase probability: +65%",
            "priority": "high", "confidence": 0.87,
        })

    order_map = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: order_map.get(s["priority"], 2))
    return suggestions[:5]


def _suggestion_card_html(s: dict) -> str:
    prio = s["priority"]
    conf_pct = int(float(s["confidence"]) * 100)
    prio_colors = {
        "high":   ("rgba(255,77,106,0.12)",  "#FF6B8A", "rgba(255,77,106,0.35)"),
        "medium": ("rgba(255,173,0,0.10)",   "#FFAD00", "rgba(255,173,0,0.35)"),
        "low":    ("rgba(34,197,94,0.10)",   "#22C55E", "rgba(34,197,94,0.30)"),
    }
    prio_labels = {"high": "🔴 HIGH PRIORITY", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}
    bg, accent, border = prio_colors.get(prio, prio_colors["medium"])
    prio_label = prio_labels.get(prio, "MEDIUM")

    return f"""<div style="padding:18px 20px;background:{bg};border:1px solid {border};
border-left:3px solid {accent};border-radius:12px;margin-bottom:12px;">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:6px;">
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="font-size:1.3rem;">{s['icon']}</span>
    <span style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;color:{accent};text-transform:uppercase;
      background:rgba(255,255,255,0.06);padding:2px 8px;border-radius:99px;border:1px solid {border};">{s['category']}</span>
    <span style="font-size:0.6rem;font-weight:700;letter-spacing:0.08em;color:{accent};text-transform:uppercase;">{prio_label}</span>
  </div>
  <span style="font-size:0.65rem;font-weight:600;color:#00D4A8;background:rgba(0,212,168,0.08);
    border:1px solid rgba(0,212,168,0.25);padding:2px 8px;border-radius:99px;">✦ {conf_pct}% AI Confidence</span>
</div>
<div style="font-family:'Space Grotesk',sans-serif;font-size:0.95rem;font-weight:700;
  color:var(--nx-text-1, #EEEEFF);margin-bottom:7px;line-height:1.35;">{s['title']}</div>
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
  border-radius:8px;padding:10px 13px;margin-bottom:10px;">
  <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.1em;color:#4E4E7A;
    text-transform:uppercase;margin-bottom:4px;">💡 WHY THIS MATTERS</div>
  <div style="font-size:0.81rem;color:var(--nx-text-2, #9898BB);line-height:1.5;">{s['why']}</div>
</div>
<div style="background:rgba(0,212,168,0.04);border:1px solid rgba(0,212,168,0.15);
  border-radius:8px;padding:10px 13px;margin-bottom:10px;">
  <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.1em;color:#00D4A8;
    text-transform:uppercase;margin-bottom:4px;">✦ RECOMMENDED ACTION</div>
  <div style="font-size:0.82rem;color:var(--nx-text-1, #EEEEFF);line-height:1.55;">{s['action']}</div>
</div>
<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
  <span style="font-size:0.68rem;color:#4E4E7A;font-weight:500;">Expected Impact:</span>
  <span style="font-size:0.72rem;font-weight:700;color:#86EFAC;font-family:'DM Mono',monospace;
    background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);
    padding:2px 10px;border-radius:99px;">↑ {s['impact']}</span>
</div>
</div>"""


def _mini_bar_html(label: str, value: float, max_val: float, color: str = "#00D4A8") -> str:
    pct = min(100, (value / max_val * 100)) if max_val > 0 else 0
    return (
        f'<div style="margin-bottom:8px;">'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
        f'<span style="font-size:0.78rem;color:var(--nx-text-2, #9898BB);">{label}</span>'
        f'<span style="font-size:0.78rem;font-weight:600;color:var(--nx-text-1, #EEEEFF);font-family:\'DM Mono\',monospace;">{fmt_currency(value)}</span>'
        f'</div>'
        f'<div style="background:rgba(255,255,255,0.05);border-radius:99px;height:5px;">'
        f'<div style="width:{pct:.1f}%;background:{color};border-radius:99px;height:5px;transition:width 0.4s ease;"></div>'
        f'</div></div>'
    )


@st.cache_data(show_spinner=False)
def _get_customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    cust_col   = next((c for c in ["CustomerID"] if c in df.columns), None)
    name_col   = next((c for c in ["CustomerName", "Name"] if c in df.columns), None)
    age_col    = next((c for c in ["CustomerAge", "Age"] if c in df.columns), None)
    gender_col = next((c for c in ["Gender", "Sex"] if c in df.columns), None)
    region_col = next((c for c in ["Region", "Location", "State"] if c in df.columns), None)
    amt_col    = next((c for c in ["TotalAmount", "Revenue", "Amount"] if c in df.columns), None)
    rating_col = next((c for c in ["CustomerRating", "Rating"] if c in df.columns), None)

    if not cust_col:
        return pd.DataFrame()

    agg: dict = {}
    if name_col:   agg[name_col]   = pd.NamedAgg(column=name_col,   aggfunc="first")
    if age_col:    agg[age_col]    = pd.NamedAgg(column=age_col,    aggfunc="first")
    if gender_col: agg[gender_col] = pd.NamedAgg(column=gender_col, aggfunc="first")
    if region_col: agg[region_col] = pd.NamedAgg(column=region_col, aggfunc="first")
    if amt_col:
        agg[f"{amt_col}_sum"]   = pd.NamedAgg(column=amt_col, aggfunc="sum")
        agg[f"{amt_col}_count"] = pd.NamedAgg(column=amt_col, aggfunc="count")
        agg[f"{amt_col}_mean"]  = pd.NamedAgg(column=amt_col, aggfunc="mean")
    if rating_col:
        agg[f"{rating_col}_mean"] = pd.NamedAgg(column=rating_col, aggfunc="mean")

    return (
        df.groupby(cust_col).agg(**agg).reset_index()
        if agg else
        df.groupby(cust_col).size().reset_index(name="TransactionCount")
    )


def render(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No customer data available. Adjust filters or upload a dataset.")
        return

    cust_col   = next((c for c in ["CustomerID"] if c in df.columns), None)
    name_col   = next((c for c in ["CustomerName", "Name"] if c in df.columns), None)
    age_col    = next((c for c in ["CustomerAge", "Age"] if c in df.columns), None)
    gender_col = next((c for c in ["Gender", "Sex"] if c in df.columns), None)
    region_col = next((c for c in ["Region", "Location", "State"] if c in df.columns), None)
    amt_col    = next((c for c in ["TotalAmount", "Revenue", "Amount"] if c in df.columns), None)
    rating_col = next((c for c in ["CustomerRating", "Rating"] if c in df.columns), None)
    date_col   = next((c for c in ["PurchaseDate", "Date", "OrderDate"] if c in df.columns), None)
    cat_col    = "Category" if "Category" in df.columns else None
    prod_col   = next((c for c in ["ProductName", "Product"] if c in df.columns), None)

    if not cust_col:
        st.error("No CustomerID column found in the dataset.")
        return

    cust_summary = _get_customer_summary(df)
    if cust_summary.empty:
        st.error("Could not aggregate customer data.")
        return

    col_search, _ = st.columns([2, 3])
    with col_search:
        customer_ids  = cust_summary[cust_col].tolist()
        selected_cust = st.selectbox("🔍 Search Customer ID", customer_ids, key="cust_profile_select")

    row       = cust_summary[cust_summary[cust_col] == selected_cust].iloc[0]
    cust_txns = df[df[cust_col] == selected_cust].copy()

    name = str(row.get(name_col, selected_cust) if name_col else selected_cust)

    _raw_age = row.get(age_col, None) if age_col else None
    try:   age = int(float(_raw_age)) if pd.notna(_raw_age) else "–"
    except (ValueError, TypeError): age = "–"

    gender = str(row.get(gender_col, "–")) if gender_col else "–"
    region = str(row.get(region_col, "–")) if region_col else "–"

    try:   spend = float(row.get(f"{amt_col}_sum", 0)) if amt_col else 0.0
    except (ValueError, TypeError): spend = 0.0

    try:   orders = int(float(row.get(f"{amt_col}_count", 0))) if amt_col else 0
    except (ValueError, TypeError): orders = 0

    try:   avg_ord = float(row.get(f"{amt_col}_mean", 0)) if amt_col else 0.0
    except (ValueError, TypeError): avg_ord = 0.0

    try:   rating = float(row.get(f"{rating_col}_mean", 0)) if rating_col else 0.0
    except (ValueError, TypeError): rating = 0.0

    days_last                        = _days_since(cust_txns[date_col]) if date_col else 0
    tier_label, tier_color, tier_emoji = _tier(spend)
    churn_label, churn_color, churn_score = _churn_risk(orders, rating, days_last)

    top_category = ""
    if cat_col and amt_col and not cust_txns.empty:
        try:
            top_category = cust_txns.groupby(cat_col)[amt_col].sum().idxmax()
        except Exception:
            top_category = ""

    # Profile Header
    stats_html = "".join([
        f'<div style="flex:1;padding:12px 14px;border-right:1px solid rgba(255,255,255,0.05);">'
        f'<div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#4E4E7A;margin-bottom:4px;">{lbl}</div>'
        f'<div style="font-family:\'DM Mono\',monospace;font-size:1.05rem;font-weight:600;color:var(--nx-text-1, #EEEEFF);">{val}</div>'
        f'</div>'
        for lbl, val in [
            ("Lifetime Spend", fmt_currency(spend)),
            ("Total Orders",   fmt_number(orders)),
            ("Avg Order",      fmt_currency(avg_ord)),
            ("Avg Rating",     f"{_stars(rating)} {rating:.1f}" if rating > 0 else "—"),
            ("Days Since Buy", f"{days_last}d ago" if days_last < 999 else "—"),
            ("Top Category",   top_category or "—"),
        ]
    ])

    avatar_letter = str(name)[0].upper() if str(name) else "?"

    profile_html = (
        f'<div style="background:linear-gradient(135deg,rgba(9,9,26,0.9) 0%,rgba(13,13,32,0.95) 100%);'
        f'border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:24px 28px;'
        f'margin-bottom:20px;position:relative;overflow:hidden;">'
        f'<div style="position:absolute;top:-60px;right:-60px;width:200px;height:200px;'
        f'background:radial-gradient(circle,rgba(155,109,255,0.12) 0%,transparent 70%);pointer-events:none;"></div>'
        f'<div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;">'
        f'<div style="width:64px;height:64px;flex-shrink:0;background:linear-gradient(135deg,#6366F1,#A855F7);'
        f'border-radius:50%;display:flex;align-items:center;justify-content:center;'
        f'font-size:26px;font-weight:800;color:#fff;box-shadow:0 0 20px rgba(155,109,255,0.35);">{avatar_letter}</div>'
        f'<div style="flex:1;min-width:180px;">'
        f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.45rem;font-weight:800;color:var(--nx-text-1, #EEEEFF);'
        f'letter-spacing:-0.03em;line-height:1.2;">{name}</div>'
        f'<div style="color:var(--nx-text-2, #9898BB);font-size:0.82rem;margin-top:4px;">'
        f'{selected_cust} &nbsp;·&nbsp; {gender} &nbsp;·&nbsp; Age {age} &nbsp;·&nbsp; 📍 {region}'
        f'</div></div>'
        f'<div style="display:flex;flex-direction:column;gap:7px;align-items:flex-end;flex-shrink:0;">'
        f'<div style="display:inline-flex;align-items:center;gap:6px;padding:5px 14px;'
        f'background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.12);border-radius:99px;">'
        f'<span style="font-size:1rem;">{tier_emoji}</span>'
        f'<span style="font-size:0.78rem;font-weight:700;color:{tier_color};'
        f'font-family:\'Space Grotesk\',sans-serif;letter-spacing:0.05em;">{tier_label.upper()} MEMBER</span></div>'
        f'<div style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;'
        f'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:99px;">'
        f'<div style="width:7px;height:7px;border-radius:50%;background:{churn_color};box-shadow:0 0 6px {churn_color};"></div>'
        f'<span style="font-size:0.7rem;font-weight:600;color:{churn_color};letter-spacing:0.05em;">{churn_label} CHURN RISK</span>'
        f'</div></div></div>'
        f'<div style="display:flex;gap:0;margin-top:20px;background:rgba(255,255,255,0.03);'
        f'border:1px solid rgba(255,255,255,0.06);border-radius:10px;overflow:hidden;">'
        f'{stats_html}</div></div>'
    )
    st.markdown(profile_html, unsafe_allow_html=True)

    # AI Suggestions
    st.markdown(section_title("AI-Powered Customer Suggestions", "🤖"), unsafe_allow_html=True)

    suggestions = _generate_suggestions(
        spend=spend, orders=orders, avg_order=avg_ord, rating=rating,
        days_since_last=days_last, top_category=top_category,
        churn_label=churn_label, tier_label=tier_label,
    )

    if not suggestions:
        st.success("✅ This customer is in great health — no urgent actions needed right now.")
    else:
        high_count = sum(1 for s in suggestions if s["priority"] == "high")
        mid_count  = sum(1 for s in suggestions if s["priority"] == "medium")
        low_count  = sum(1 for s in suggestions if s["priority"] == "low")

        high_span = f"<span style='font-size:0.72rem;font-weight:700;color:#FF6B8A;background:rgba(255,77,106,0.1);border:1px solid rgba(255,77,106,0.25);padding:2px 9px;border-radius:99px;'>🔴 {high_count} High</span>" if high_count else ""
        mid_span  = f"<span style='font-size:0.72rem;font-weight:700;color:#FFAD00;background:rgba(255,173,0,0.1);border:1px solid rgba(255,173,0,0.25);padding:2px 9px;border-radius:99px;'>🟡 {mid_count} Medium</span>" if mid_count else ""
        low_span  = f"<span style='font-size:0.72rem;font-weight:700;color:#22C55E;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.25);padding:2px 9px;border-radius:99px;'>🟢 {low_count} Low</span>" if low_count else ""
        banner_html = (
            f'<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;align-items:center;">'
            f'<div style="font-size:0.8rem;color:var(--nx-text-2, #9898BB);"><strong style="color:var(--nx-text-1, #EEEEFF);">{len(suggestions)}</strong> personalised suggestions</div>'
            f'{high_span}{mid_span}{low_span}'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

        for s in suggestions:
            st.markdown(_suggestion_card_html(s), unsafe_allow_html=True)

    # Engagement Signals
    st.markdown(section_title("Engagement Signals", "📊"), unsafe_allow_html=True)
    sig_l, sig_r = st.columns(2)

    with sig_l:
        gauge_color = churn_color
        gauge_pct   = churn_score
        st.markdown(f"""<div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);
border-radius:12px;padding:18px 20px;height:100%;">
  <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#4E4E7A;margin-bottom:12px;">⚡ Churn Risk Score</div>
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="width:68px;height:68px;border-radius:50%;flex-shrink:0;
      background:conic-gradient({gauge_color} {gauge_pct * 3.6}deg,rgba(255,255,255,0.06) 0deg);
      display:flex;align-items:center;justify-content:center;position:relative;">
      <div style="width:52px;height:52px;border-radius:50%;background:#09091A;
        display:flex;align-items:center;justify-content:center;
        font-family:'DM Mono',monospace;font-size:0.95rem;font-weight:700;color:{gauge_color};">{gauge_pct}</div>
    </div>
    <div>
      <div style="font-size:1.1rem;font-weight:700;color:{gauge_color};font-family:'Space Grotesk',sans-serif;">{churn_label} Risk</div>
      <div style="font-size:0.77rem;color:var(--nx-text-2, #9898BB);margin-top:3px;">Score: {gauge_pct}/100 · {days_last}d since last purchase</div>
    </div>
  </div>
  <div style="margin-top:12px;">
    <div style="background:rgba(255,255,255,0.05);border-radius:99px;height:6px;">
      <div style="width:{gauge_pct}%;background:{gauge_color};border-radius:99px;height:6px;"></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    with sig_r:
        loyalty_score = min(100, int(
            (min(orders, 20) / 20 * 40) +
            (min(spend, 5000) / 5000 * 40) +
            (max(0, rating - 1) / 4 * 20)
        ))
        loyalty_color = "#00D4A8" if loyalty_score >= 60 else "#FFAD00" if loyalty_score >= 35 else "#FF6B8A"

        st.markdown(f"""<div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);
border-radius:12px;padding:18px 20px;height:100%;">
  <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#4E4E7A;margin-bottom:12px;">💎 Loyalty Score</div>
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="width:68px;height:68px;border-radius:50%;flex-shrink:0;
      background:conic-gradient({loyalty_color} {loyalty_score * 3.6}deg,rgba(255,255,255,0.06) 0deg);
      display:flex;align-items:center;justify-content:center;">
      <div style="width:52px;height:52px;border-radius:50%;background:#09091A;
        display:flex;align-items:center;justify-content:center;
        font-family:'DM Mono',monospace;font-size:0.95rem;font-weight:700;color:{loyalty_color};">{loyalty_score}</div>
    </div>
    <div>
      <div style="font-size:1.1rem;font-weight:700;color:{loyalty_color};font-family:'Space Grotesk',sans-serif;">{tier_label} Tier</div>
      <div style="font-size:0.77rem;color:var(--nx-text-2, #9898BB);margin-top:3px;">{orders} orders · {fmt_currency(spend)} lifetime</div>
    </div>
  </div>
  <div style="margin-top:12px;">
    <div style="background:rgba(255,255,255,0.05);border-radius:99px;height:6px;">
      <div style="width:{loyalty_score}%;background:{loyalty_color};border-radius:99px;height:6px;"></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Spend by Category
    if cat_col and amt_col and not cust_txns.empty:
        st.markdown(section_title("Spend by Category", "📦"), unsafe_allow_html=True)

        cat_breakdown = (
            cust_txns.groupby(cat_col)[amt_col].sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        cat_breakdown.columns = ["Category", "Total Spend"]
        max_val = float(cat_breakdown["Total Spend"].max()) if not cat_breakdown.empty else 1.0
        palette = ["#00D4A8", "#9B6DFF", "#FF6B8A", "#FFAD00", "#38BDF8", "#22C55E"]

        with st.container():
            st.markdown("""<div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);
border-radius:12px;padding:18px 22px;margin-bottom:16px;">""", unsafe_allow_html=True)
            for i, row_c in cat_breakdown.head(6).iterrows():
                st.markdown(
                    _mini_bar_html(str(row_c["Category"]), float(row_c["Total Spend"]), max_val, palette[i % len(palette)]),
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

    # Purchase History
    st.markdown(section_title("Purchase History Timeline", "🕐"), unsafe_allow_html=True)

    show_cols = [c for c in [
        "TransactionID", date_col, cat_col, prod_col,
        "Brand", amt_col, "PaymentMethod", rating_col
    ] if c and c in cust_txns.columns]

    if show_cols:
        display_df = cust_txns[show_cols].copy()
        if date_col and date_col in display_df.columns:
            display_df[date_col] = pd.to_datetime(display_df[date_col], errors="coerce")
            display_df = display_df.sort_values(date_col, ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(cust_txns, use_container_width=True, hide_index=True)
