"""
Streamlit UI for the Restaurant Social Media Generator.

Provides:
- Post generation from JSON templates
- A/B testing between templates
- Simple session-based analytics (no DB yet)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

import config
from src.ab_testing import ABTester
from src.openai_handler import OpenAIHandler
from src.quality_scorer import QualityScorer
from src.template_manager import TemplateManager


def main() -> None:
    """
    Run the Streamlit application.

    Initializes configuration, loads templates, and routes between pages.
    """
    st.set_page_config(
        page_title="Restaurant Social Media Generator",
        page_icon="🍽️",
        layout="wide",
    )

    _inject_minimal_css()

    # Setup logging and validate config (fail fast, show UI error).
    config.setup_logging()
    try:
        config.validate_config()
    except ValueError as e:
        st.error(str(e))
        st.info("Copy `.env.example` to `.env`, set `OPENAI_API_KEY`, then rerun.")
        st.stop()

    # Initialize components (cached for Streamlit reruns).
    template_manager = _get_template_manager()
    openai_handler = _get_openai_handler()
    quality_scorer = QualityScorer()
    ab_tester = ABTester(openai_handler=openai_handler, quality_scorer=quality_scorer)

    _init_session_state()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Navigate",
        ["Generate Post", "A/B Test Templates", "Analytics"],
        index=0,
    )

    if page == "Generate Post":
        render_generate_page(
            template_manager=template_manager,
            openai_handler=openai_handler,
            quality_scorer=quality_scorer,
        )
    elif page == "A/B Test Templates":
        render_ab_test_page(
            template_manager=template_manager,
            ab_tester=ab_tester,
        )
    else:
        render_analytics_page(template_manager=template_manager)


@st.cache_resource
def _get_template_manager() -> TemplateManager:
    """
    Create and cache the TemplateManager.

    Returns:
        TemplateManager instance pointing to the local templates directory.
    """
    templates_dir = Path(__file__).resolve().parent / "templates"
    return TemplateManager(templates_dir=templates_dir)


@st.cache_resource
def _get_openai_handler() -> OpenAIHandler:
    """
    Create and cache the OpenAIHandler.

    Returns:
        OpenAIHandler initialized from config.
    """
    return OpenAIHandler(api_key=config.OPENAI_API_KEY, model=config.MODEL_NAME)


def _init_session_state() -> None:
    """
    Initialize Streamlit session state keys for basic analytics.
    """
    if "total_cost" not in st.session_state:
        st.session_state["total_cost"] = 0.0
    if "total_posts" not in st.session_state:
        st.session_state["total_posts"] = 0
    if "generation_history" not in st.session_state:
        st.session_state["generation_history"] = []


def _inject_minimal_css() -> None:
    """
    Inject minimal CSS for small visual polish.
    """
    st.markdown(
        """
        <style>
          .smg-badge { display:inline-block; padding:2px 8px; border-radius:999px;
                      font-size:0.85rem; font-weight:600; }
          .smg-green { background:#E6F4EA; color:#137333; border:1px solid #A8DAB5; }
          .smg-yellow{ background:#FEF7E0; color:#8A6D00; border:1px solid #F3D48E; }
          .smg-red   { background:#FCE8E6; color:#A50E0E; border:1px solid #F4B4AE; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _quality_badge(score: float) -> str:
    """
    Return an HTML badge for a quality score.

    Args:
        score: Overall quality score (0-10).

    Returns:
        HTML string for Streamlit markdown.
    """
    if score > 7.5:
        klass = "smg-badge smg-green"
        label = f"High quality ({score:.1f}/10)"
    elif score >= 6.0:
        klass = "smg-badge smg-yellow"
        label = f"Medium quality ({score:.1f}/10)"
    else:
        klass = "smg-badge smg-red"
        label = f"Low quality ({score:.1f}/10)"
    return f"<span class='{klass}'>{label}</span>"


def _copy_to_clipboard_button(text: str, key: str) -> None:
    """
    Render a copy-to-clipboard button using a tiny HTML/JS snippet.

    Args:
        text: Text to copy.
        key: Unique key for Streamlit element uniqueness.
    """
    safe_text = json.dumps(text)  # safe JS string
    html = f"""
      <button id="btn-{key}" style="padding:0.25rem 0.6rem;border-radius:0.5rem;
              border:1px solid #ddd;background:#fff;cursor:pointer;">
        Copy to clipboard
      </button>
      <script>
        const btn = document.getElementById("btn-{key}");
        btn.addEventListener("click", async () => {{
          try {{
            await navigator.clipboard.writeText({safe_text});
            btn.innerText = "Copied!";
            setTimeout(() => btn.innerText = "Copy to clipboard", 1200);
          }} catch (e) {{
            btn.innerText = "Copy failed";
            setTimeout(() => btn.innerText = "Copy to clipboard", 1200);
          }}
        }});
      </script>
    """
    st.components.v1.html(html, height=42)


def _template_options(template_manager: TemplateManager) -> list[dict[str, Any]]:
    """
    Load template summaries for selectors.

    Returns:
        List of template summary dicts.
    """
    templates = template_manager.list_templates()
    # Stable ordering for UI
    return sorted(templates, key=lambda t: str(t.get("name", "")))


def _render_dynamic_variables_form(template: dict[str, Any], form_key: str) -> dict[str, Any]:
    """
    Render input controls for a template's variables list.

    Args:
        template: Full template dict including "variables".
        form_key: Unique key prefix for widget keys.

    Returns:
        Dict of collected variable values.
    """
    values: dict[str, Any] = {}
    specs = template.get("variables", [])

    for spec in specs:
        var_name = str(spec.get("name", "")).strip()
        if not var_name:
            continue

        var_type = str(spec.get("type", "string")).lower()
        required = bool(spec.get("required", False))
        desc = str(spec.get("description", ""))
        example = str(spec.get("example", ""))

        label = f"{var_name}{' *' if required else ''}"
        help_text = (desc + (f" (e.g. {example})" if example else "")).strip()

        # Keep the UI simple: strings and numbers map to text inputs by default.
        if var_type in ("int", "integer"):
            values[var_name] = st.number_input(
                label,
                value=0,
                step=1,
                key=f"{form_key}_{var_name}",
                help=help_text or None,
            )
        elif var_type in ("number", "float"):
            values[var_name] = st.number_input(
                label,
                value=0.0,
                step=0.1,
                key=f"{form_key}_{var_name}",
                help=help_text or None,
            )
        elif var_type == "bool":
            values[var_name] = st.checkbox(
                label,
                value=False,
                key=f"{form_key}_{var_name}",
                help=help_text or None,
            )
        else:
            values[var_name] = st.text_input(
                label,
                value="",
                key=f"{form_key}_{var_name}",
                help=help_text or None,
            )

    return values


def render_generate_page(
    template_manager: TemplateManager,
    openai_handler: OpenAIHandler,
    quality_scorer: QualityScorer,
) -> None:
    """
    Render the 'Generate Post' page.
    """
    st.title("🍽️ Generate Social Media Post")

    templates = _template_options(template_manager)
    if not templates:
        st.error("No templates found. Add JSON templates under `templates/`.")
        return

    template_label_to_id = {f'{t["name"]} ({t["template_id"]})': t["template_id"] for t in templates}
    selected_label = st.selectbox("Choose a template", list(template_label_to_id.keys()))
    selected_template_id = template_label_to_id[selected_label]

    template = template_manager.get_template(selected_template_id)

    st.subheader("Inputs")
    variables = _render_dynamic_variables_form(template=template, form_key=f"gen_{selected_template_id}")

    num_variations = st.slider("Number of variations", min_value=1, max_value=5, value=3)

    if st.button("Generate Posts", type="primary"):
        try:
            prompt = template_manager.fill_template(selected_template_id, variables)
        except ValueError as e:
            st.error(f"Variable validation failed: {e}")
            return

        with st.spinner("Generating posts..."):
            try:
                variations = openai_handler.generate_variations(
                    prompt=prompt,
                    num_variations=num_variations,
                    max_tokens=300,
                )
            except Exception as e:
                st.error(f"Generation failed: {e}")
                return

        st.subheader("Results")
        total_cost = 0.0

        for v in variations:
            content = str(v.get("content", "") or "")
            cost = float(v.get("cost", 0.0) or 0.0)
            total_cost += cost

            scoring = quality_scorer.score_post(content)
            overall = float(scoring.get("overall_score", 0.0) or 0.0)
            metrics = dict(scoring.get("metrics", {}) or {})
            feedback = list(scoring.get("feedback", []) or [])

            header_cols = st.columns([3, 1, 1])
            with header_cols[0]:
                st.markdown(
                    f"**Variation {int(v.get('variation', 0) or 0)}** "
                    f"{_quality_badge(overall)}",
                    unsafe_allow_html=True,
                )
            with header_cols[1]:
                st.metric("Score", f"{overall:.1f}/10")
            with header_cols[2]:
                st.metric("Cost", f"${cost:.6f}")

            with st.expander("View content + details", expanded=False):
                st.write(content)
                _copy_to_clipboard_button(content, key=f"copy_{selected_template_id}_{v.get('variation')}")

                st.markdown("### Metrics")
                st.json(metrics)

                st.markdown("### Feedback")
                if feedback:
                    for item in feedback:
                        st.write(f"- {item}")
                else:
                    st.write("No feedback — looks solid.")

            st.divider()

        # Session tracking
        st.session_state["total_cost"] += float(total_cost)
        st.session_state["total_posts"] += int(num_variations)
        st.session_state["generation_history"].append(
            {
                "template_id": selected_template_id,
                "template_name": template.get("name", selected_template_id),
                "num_variations": num_variations,
                "total_cost": round(total_cost, 6),
            }
        )

        st.markdown("### Total")
        st.metric("Total cost (this run)", f"${total_cost:.6f}")


def render_ab_test_page(template_manager: TemplateManager, ab_tester: ABTester) -> None:
    """
    Render the 'A/B Test Templates' page.
    """
    st.title("🔬 A/B Test Templates")

    templates = _template_options(template_manager)
    if len(templates) < 2:
        st.error("Need at least two templates to run an A/B test.")
        return

    label_to_id = {f'{t["name"]} ({t["template_id"]})': t["template_id"] for t in templates}
    labels = list(label_to_id.keys())

    col_a, col_b = st.columns(2)
    with col_a:
        a_label = st.selectbox("Template A", labels, index=0)
    with col_b:
        b_label = st.selectbox("Template B", labels, index=min(1, len(labels) - 1))

    template_a_id = label_to_id[a_label]
    template_b_id = label_to_id[b_label]

    template_a = template_manager.get_template(template_a_id)
    template_b = template_manager.get_template(template_b_id)

    # Union of both templates' variables (by name).
    vars_a = {v["name"]: v for v in template_a.get("variables", []) if v.get("name")}
    vars_b = {v["name"]: v for v in template_b.get("variables", []) if v.get("name")}
    union_specs = list({**vars_a, **vars_b}.values())
    union_template = {"variables": union_specs}

    st.subheader("Shared Inputs (Union of both templates)")
    variables = _render_dynamic_variables_form(union_template, form_key=f"ab_{template_a_id}_{template_b_id}")

    num_variations = st.slider(
        "Variations per template",
        min_value=1,
        max_value=10,
        value=5,
    )

    if st.button("Run A/B Test", type="primary"):
        with st.spinner("Running A/B test..."):
            try:
                report = ab_tester.run_ab_test(
                    template_a_id=template_a_id,
                    template_b_id=template_b_id,
                    variables=variables,
                    template_manager=template_manager,
                    num_variations=num_variations,
                )
            except ValueError as e:
                st.error(f"A/B test failed: {e}")
                return
            except Exception as e:
                st.error(f"A/B test failed: {e}")
                return

        results = report["results"]
        winner = report["winner"]
        summary = report["summary"]

        st.subheader("Summary")
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Templates tested", summary["total_templates_tested"])
        with s2:
            st.metric("Variations generated", summary["total_variations_generated"])
        with s3:
            st.metric("Total cost", f"${summary['total_cost']:.6f}")

        st.subheader("Winner")
        st.success(f"Winner: {winner['template_name']} ({winner['template_id']}) — {winner['reason']}")

        # Side-by-side comparison table
        comparison_df = pd.DataFrame(
            [
                {
                    "template_id": r["template_id"],
                    "template_name": r["template_name"],
                    "avg_quality_score": r["avg_quality_score"],
                    "avg_cost": r["avg_cost"],
                    "total_cost": r["total_cost"],
                }
                for r in results
            ]
        )
        st.subheader("Comparison")
        st.dataframe(comparison_df, use_container_width=True)

        # Bar chart for avg quality
        chart_df = comparison_df.set_index("template_name")[["avg_quality_score"]]
        st.subheader("Quality score comparison")
        st.bar_chart(chart_df)

        # Sample variations
        st.subheader("Sample variations")
        left, right = st.columns(2)
        for r, col in zip(results, [left, right], strict=False):
            with col:
                st.markdown(f"**{r['template_name']}**")
                sample = r["variations"][0]
                st.write(sample["content"])
                st.caption(f"Score: {sample['quality_score']:.1f}/10 | Cost: ${sample['cost']:.6f}")

        # Export CSV
        export_rows: list[dict[str, Any]] = []
        for r in results:
            for v in r["variations"]:
                export_rows.append(
                    {
                        "template_id": r["template_id"],
                        "template_name": r["template_name"],
                        "variation": v["variation"],
                        "quality_score": v["quality_score"],
                        "cost": v["cost"],
                        "content": v["content"],
                    }
                )
        export_df = pd.DataFrame(export_rows)
        st.download_button(
            label="Export results to CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="ab_test_results.csv",
            mime="text/csv",
        )


def render_analytics_page(template_manager: TemplateManager) -> None:
    """
    Render the 'Analytics' page (session-state only for now).
    """
    st.title("📊 Usage Analytics")

    results_db = (config.DATA_DIR / "results.db").resolve()
    has_db = results_db.exists()

    if not has_db:
        st.info("No data yet - generate some posts first!")

    history = list(st.session_state.get("generation_history", []) or [])
    total_cost = float(st.session_state.get("total_cost", 0.0) or 0.0)
    total_posts = int(st.session_state.get("total_posts", 0) or 0)

    avg_quality = None
    # We don't persist quality scores yet; placeholder derived from history.
    # This keeps the UI stable until DB integration is added.
    if history:
        avg_quality = "N/A (not persisted yet)"

    most_used_template = None
    if history:
        counts: dict[str, int] = {}
        for item in history:
            tid = str(item.get("template_id", "unknown"))
            counts[tid] = counts.get(tid, 0) + int(item.get("num_variations", 0) or 0)
        most_used_template = max(counts, key=counts.get)
        try:
            most_used_template_name = template_manager.get_template(most_used_template).get("name", most_used_template)
        except ValueError:
            most_used_template_name = most_used_template
    else:
        most_used_template_name = "N/A"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total posts generated", total_posts)
    with c2:
        st.metric("Total cost (session)", f"${total_cost:.6f}")
    with c3:
        st.metric("Average quality", avg_quality or "N/A")
    with c4:
        st.metric("Most used template", most_used_template_name)

    st.subheader("Generation history (this session)")
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True)
    else:
        st.write("No generations recorded yet.")


if __name__ == "__main__":
    main()
