"""
Customer Insights Platform – KPI Cards & UI Atoms v5.0 — Cosmic Aurora
kpi_card()      → DM Mono metric card with teal glow & icon badge
insight_card()  → AI recommendation card with aurora priority system
section_title() → teal/violet gradient left-accent section header
"""
from __future__ import annotations

_KPI_ICONS = {
    "revenue":   ("💰", "green"),
    "orders":    ("📦", "blue"),
    "customers": ("👥", "violet"),
    "basket":    ("🛒", "amber"),
    "profit":    ("📈", "green"),
    "inventory": ("🏭", "cyan"),
    "default":   ("✦",  "blue"),
}


def kpi_card(label: str, value: str, delta: str, positive: bool, kpi_type: str = "default") -> str:
    icon_emoji, icon_color = _KPI_ICONS.get(kpi_type, _KPI_ICONS["default"])
    delta_class = "up" if positive else "down"
    delta_arrow = "▲" if positive else "▼"
    delta_str   = str(delta) if delta and delta != "–" else "–"

    show_delta = delta_str != "–"
    delta_html = f"""
      <span class="ip-kpi-delta {delta_class}">
        {delta_arrow} {delta_str}
      </span>
      <span class="ip-kpi-delta-label">vs prev month</span>
    """ if show_delta else '<span class="ip-kpi-delta-label">No prior data</span>'

    return f"""
    <div class="ip-kpi-card">
      <div class="ip-kpi-header">
        <span class="ip-kpi-label">{label}</span>
        <div class="ip-kpi-icon {icon_color}">{icon_emoji}</div>
      </div>
      <div class="ip-kpi-value">{value}</div>
      <div class="ip-kpi-footer">{delta_html}</div>
    </div>
    """


def insight_card(title: str, description: str, action: str, impact: str,
                 priority: str = "medium", confidence: float = 0.75) -> str:
    prio     = priority.lower() if priority else "medium"
    conf_val = float(confidence)
    # Support both 0-1 scale (e.g. 0.90) and 0-100 scale (e.g. 90.0)
    conf_pct = int(conf_val) if conf_val > 1.0 else int(conf_val * 100)
    conf_pct = max(0, min(100, conf_pct))  # clamp to [0, 100]
    prio_map = {
        "high":   ("●", "HIGH"),
        "medium": ("●", "MED"),
        "low":    ("●", "LOW"),
    }
    p_dot, p_label = prio_map.get(prio, ("●", "MED"))

    return f"""
    <div class="ip-insight-card {prio}">
      <div class="ip-insight-meta">
        <span class="ip-badge-priority {prio}">{p_dot} {p_label}</span>
        <span class="ip-badge-confidence">✦ {conf_pct}% confidence</span>
      </div>
      <div class="ip-insight-title">{title}</div>
      <div class="ip-insight-desc">{description}</div>
      <div class="ip-insight-action">
        <span style="color:var(--nx-teal, #00D4A8);font-weight:700;font-size:0.7rem;
                     text-transform:uppercase;letter-spacing:0.08em;
                     font-family:'Space Grotesk',sans-serif;">
          ✦ Recommended Action
        </span><br>
        <span style="font-size:0.8rem;color:var(--nx-text-2, #9898BB);margin-top:4px;display:block;">
          {action}
        </span>
        <span style="
          display:inline-flex;align-items:center;gap:4px;
          margin-top:7px;font-size:0.7rem;color:var(--nx-success, #86EFAC);font-weight:600;
          font-family:'DM Mono',monospace;">
          ↑ Impact: {impact}
        </span>
      </div>
    </div>
    """


def section_title(title: str, icon: str = "") -> str:
    prefix = f"{icon}  " if icon else ""
    return f'<div class="ip-section-title">{prefix}{title}</div>'
