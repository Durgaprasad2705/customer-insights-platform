"""
Customer Insights Platform – Global Navigation Toggle Component
Renders a sleek, responsive global navigation toggle button (☰ Menu / ✕ Close)
that controls Streamlit's native sidebar panel without triggering page reruns,
state loss, or data reloading.
"""
from __future__ import annotations
import streamlit.components.v1 as _components


def render_navigation_toggle() -> None:
    """Render the global navigation toggle button across all pages."""
    _components.html(
        """
        <script>
        (function() {
            var parentDoc = window.parent.document;
            if (!parentDoc) return;

            // 1. Inject Styles into Parent Document if not already present
            if (!parentDoc.getElementById('cip-nav-toggle-styles')) {
                var styleEl = parentDoc.createElement('style');
                styleEl.id = 'cip-nav-toggle-styles';
                styleEl.textContent = `
                    /* ── Global Navigation Toggle Button ── */
                    .cip-nav-toggle-btn {
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        gap: 7px;
                        padding: 5px 12px;
                        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 0.78rem;
                        font-weight: 600;
                        letter-spacing: 0.02em;
                        border-radius: 8px;
                        cursor: pointer;
                        outline: none;
                        user-select: none;
                        transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1);
                        flex-shrink: 0;
                        margin-right: 6px;
                        text-decoration: none;
                        line-height: 1.2;
                    }

                    /* Floating fallback if not inside topbar */
                    .cip-nav-toggle-btn.cip-floating {
                        position: fixed;
                        top: 14px;
                        left: 18px;
                        z-index: 999999;
                        backdrop-filter: blur(20px) saturate(180%);
                        -webkit-backdrop-filter: blur(20px) saturate(180%);
                    }

                    /* Collapsed State: ☰ Menu (Electric Teal) */
                    .cip-nav-toggle-btn.cip-sidebar-collapsed {
                        background: rgba(0, 212, 168, 0.08);
                        border: 1px solid rgba(0, 212, 168, 0.32);
                        color: #00D4A8;
                        box-shadow: 0 2px 10px rgba(0, 212, 168, 0.12);
                    }
                    .cip-nav-toggle-btn.cip-sidebar-collapsed:hover {
                        background: rgba(0, 212, 168, 0.18);
                        border-color: rgba(0, 212, 168, 0.6);
                        color: #4DFFD9;
                        box-shadow: 0 0 16px rgba(0, 212, 168, 0.28);
                        transform: translateY(-1px);
                    }
                    .cip-nav-toggle-btn.cip-sidebar-collapsed:active {
                        transform: scale(0.97);
                    }

                    /* Open State: ✕ Close (Coral/Obsidian) */
                    .cip-nav-toggle-btn.cip-sidebar-open {
                        background: rgba(255, 107, 138, 0.08);
                        border: 1px solid rgba(255, 107, 138, 0.3);
                        color: #FF6B8A;
                        box-shadow: 0 2px 10px rgba(255, 107, 138, 0.1);
                    }
                    .cip-nav-toggle-btn.cip-sidebar-open:hover {
                        background: rgba(255, 107, 138, 0.18);
                        border-color: rgba(255, 107, 138, 0.6);
                        color: #FF9DB3;
                        box-shadow: 0 0 16px rgba(255, 107, 138, 0.25);
                        transform: translateY(-1px);
                    }
                    .cip-nav-toggle-btn.cip-sidebar-open:active {
                        transform: scale(0.97);
                    }

                    .cip-nav-toggle-icon {
                        font-size: 13px;
                        line-height: 1;
                        display: inline-block;
                        transition: transform 0.2s ease;
                    }
                    .cip-nav-toggle-btn:hover .cip-nav-toggle-icon {
                        transform: scale(1.1);
                    }

                    .cip-nav-toggle-label {
                        font-size: 0.78rem;
                        font-weight: 600;
                    }

                    /* ── Light Mode Overrides ── */
                    html[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-collapsed,
                    body[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-collapsed,
                    [data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-collapsed {
                        background: rgba(0, 184, 148, 0.1) !important;
                        border-color: rgba(0, 184, 148, 0.35) !important;
                        color: #00B894 !important;
                        box-shadow: 0 2px 6px rgba(0, 184, 148, 0.1) !important;
                    }
                    html[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-collapsed:hover,
                    body[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-collapsed:hover,
                    [data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-collapsed:hover {
                        background: rgba(0, 184, 148, 0.2) !important;
                        border-color: rgba(0, 184, 148, 0.6) !important;
                        color: #00876C !important;
                        box-shadow: 0 0 12px rgba(0, 184, 148, 0.2) !important;
                    }

                    html[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-open,
                    body[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-open,
                    [data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-open {
                        background: rgba(220, 38, 38, 0.08) !important;
                        border-color: rgba(220, 38, 38, 0.28) !important;
                        color: #DC2626 !important;
                        box-shadow: 0 2px 6px rgba(220, 38, 38, 0.08) !important;
                    }
                    html[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-open:hover,
                    body[data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-open:hover,
                    [data-theme="light"] .cip-nav-toggle-btn.cip-sidebar-open:hover {
                        background: rgba(220, 38, 38, 0.16) !important;
                        border-color: rgba(220, 38, 38, 0.5) !important;
                        color: #B91C1C !important;
                        box-shadow: 0 0 12px rgba(220, 38, 38, 0.18) !important;
                    }
                `;
                parentDoc.head.appendChild(styleEl);
            }

            // 2. Helper to Check if Sidebar is Currently Open
            function isSidebarOpen() {
                try {
                    var sidebar = parentDoc.querySelector('section[data-testid="stSidebar"]') ||
                                  parentDoc.querySelector('[data-testid="stSidebar"]');
                    if (!sidebar) return false;

                    var ariaExpanded = sidebar.getAttribute('aria-expanded');
                    if (ariaExpanded !== null) {
                        return ariaExpanded === 'true';
                    }

                    var rect = sidebar.getBoundingClientRect();
                    var style = window.parent.getComputedStyle(sidebar);
                    if (style.display === 'none' || style.visibility === 'hidden') return false;
                    return rect.width > 50 && rect.right > 10;
                } catch (e) {
                    return false;
                }
            }

            // 3. Helper to Update Button UI Based on Sidebar State
            function updateButtonUI() {
                var btn = parentDoc.getElementById('cip-nav-toggle-btn');
                if (!btn) return;

                var open = isSidebarOpen();
                var iconSpan = btn.querySelector('.cip-nav-toggle-icon');
                var labelSpan = btn.querySelector('.cip-nav-toggle-label');

                if (open) {
                    btn.classList.add('cip-sidebar-open');
                    btn.classList.remove('cip-sidebar-collapsed');
                    btn.setAttribute('aria-expanded', 'true');
                    btn.setAttribute('title', 'Collapse sidebar');
                    if (iconSpan) iconSpan.textContent = '✕';
                    if (labelSpan) labelSpan.textContent = 'Close';
                } else {
                    btn.classList.add('cip-sidebar-collapsed');
                    btn.classList.remove('cip-sidebar-open');
                    btn.setAttribute('aria-expanded', 'false');
                    btn.setAttribute('title', 'Open sidebar');
                    if (iconSpan) iconSpan.textContent = '☰';
                    if (labelSpan) labelSpan.textContent = 'Menu';
                }
            }

            // 4. Helper to Programmatically Toggle Native Sidebar
            function handleToggle(e) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }

                var open = isSidebarOpen();

                if (open) {
                    // Find native collapse button in Streamlit
                    var collapseSelectors = [
                        '[data-testid="stSidebarCollapseButton"] button',
                        '[data-testid="stSidebarCollapseButton"]',
                        '[data-testid="stSidebarHeader"] button',
                        'section[data-testid="stSidebar"] button[aria-label*="Close" i]',
                        'section[data-testid="stSidebar"] button[aria-label*="Collapse" i]',
                        'button[data-testid="stSidebarCollapseButton"]',
                        'button[aria-label="Close sidebar"]',
                        'button[aria-label="Collapse sidebar"]',
                        'section[data-testid="stSidebar"] button'
                    ];
                    for (var i = 0; i < collapseSelectors.length; i++) {
                        var target = parentDoc.querySelector(collapseSelectors[i]);
                        if (target) {
                            target.click();
                            setTimeout(updateButtonUI, 120);
                            return;
                        }
                    }
                } else {
                    // Find native expand/open button in Streamlit
                    var expandSelectors = [
                        '[data-testid="stSidebarCollapsedControl"] button',
                        '[data-testid="stSidebarCollapsedControl"]',
                        'button[data-testid="stSidebarCollapsedControl"]',
                        '[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"] button',
                        '[data-testid="stSidebarHeader"] button',
                        'button[aria-label*="Open" i]',
                        'button[aria-label*="Expand" i]',
                        'button[aria-label="Open sidebar"]',
                        'button[aria-label="Expand sidebar"]',
                        '[data-testid="baseButton-header"]',
                        '[data-testid="stSidebarCollapseButton"] button',
                        '[data-testid="stSidebarCollapseButton"]'
                    ];
                    for (var j = 0; j < expandSelectors.length; j++) {
                        var expTarget = parentDoc.querySelector(expandSelectors[j]);
                        if (expTarget) {
                            expTarget.click();
                            setTimeout(updateButtonUI, 120);
                            return;
                        }
                    }
                }

                setTimeout(updateButtonUI, 200);
            }

            // 5. Mount or Relocate Button into Parent DOM
            function mountButton() {
                var btn = parentDoc.getElementById('cip-nav-toggle-btn');
                if (!btn) {
                    btn = parentDoc.createElement('button');
                    btn.id = 'cip-nav-toggle-btn';
                    btn.className = 'cip-nav-toggle-btn';
                    btn.type = 'button';
                    btn.setAttribute('aria-label', 'Toggle sidebar navigation');

                    var iconSpan = parentDoc.createElement('span');
                    iconSpan.className = 'cip-nav-toggle-icon';
                    iconSpan.textContent = '☰';

                    var labelSpan = parentDoc.createElement('span');
                    labelSpan.className = 'cip-nav-toggle-label';
                    labelSpan.textContent = 'Menu';

                    btn.appendChild(iconSpan);
                    btn.appendChild(labelSpan);

                    btn.addEventListener('click', handleToggle);
                }

                var topbarLeft = parentDoc.querySelector('.ip-topbar-left');
                if (topbarLeft) {
                    btn.classList.remove('cip-floating');
                    if (topbarLeft.firstChild !== btn) {
                        topbarLeft.insertBefore(btn, topbarLeft.firstChild);
                    }
                } else {
                    btn.classList.add('cip-floating');
                    if (!parentDoc.body.contains(btn)) {
                        parentDoc.body.appendChild(btn);
                    }
                }

                updateButtonUI();
            }

            // Initial mount
            mountButton();

            // 6. Set Up MutationObserver on Sidebar and Parent Body
            try {
                var sidebar = parentDoc.querySelector('section[data-testid="stSidebar"]') ||
                              parentDoc.querySelector('[data-testid="stSidebar"]');
                if (sidebar && !sidebar._cipObserved) {
                    sidebar._cipObserved = true;
                    var sidebarObserver = new MutationObserver(function() {
                        updateButtonUI();
                    });
                    sidebarObserver.observe(sidebar, {
                        attributes: true,
                        attributeFilter: ['aria-expanded', 'class', 'style']
                    });
                }

                // Periodic check for topbar mount during fast page transitions
                var attempts = 0;
                var mountInterval = setInterval(function() {
                    attempts++;
                    mountButton();
                    if (attempts > 10) clearInterval(mountInterval);
                }, 200);
            } catch (e) {
                console.warn('Sidebar observer error:', e);
            }

            // Listen to resize
            window.parent.addEventListener('resize', updateButtonUI);
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )
