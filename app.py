import streamlit as st
from utils.constants import DATA_CATEGORIES, CLOUD_PROVIDERS, TOOLS_DATA
from utils.calculations import calculate_costs, get_stack_recommendations
from utils.visualizations import render_cost_breakdown_chart, render_stack_comparison_chart
from utils.state import init_session_state, get_state, update_state


def render_infrastructure_step():
    st.header("Step 1: Infrastructure Setup")

    # Initialize session state variables
    if 'setup_type' not in st.session_state:
        st.session_state.setup_type = "Yes"  # Default value
    if 'selected_provider' not in st.session_state:
        st.session_state.selected_provider = None

    def on_setup_change():
        st.session_state.selected_provider = None

    # Setup type selection
    setup_type = st.radio(
        "Do you have an existing data storage solution?",
        ("Yes", "No"),
        key="setup_type_radio",
        on_change=on_setup_change
    )

    # Provider selection based on setup type
    if setup_type == "Yes":
        selected_provider = st.selectbox(
            "Which cloud provider are you using?",
            options=list(CLOUD_PROVIDERS.keys()),
            format_func=lambda x: CLOUD_PROVIDERS[x]['name'],
            key="existing_provider"
        )
    else:
        selected_provider = st.selectbox(
            "Do you have a preferred cloud provider?",
            options=list(CLOUD_PROVIDERS.keys()),
            format_func=lambda x: CLOUD_PROVIDERS[x]['name'],
            key="preferred_provider",
            help="We'll analyze your requirements and may recommend a different provider in the final step"
        )

    # Show provider information based on selection
    if selected_provider:
        if setup_type == "Yes":
            # Show single provider details
            with st.expander("View current provider details", expanded=True):
                provider_info = CLOUD_PROVIDERS[selected_provider]
                st.write("**Storage Tiers:**")
                for tier_name, tier_info in provider_info['storage'].items():
                    st.write(f"- {tier_info['name']}: ${tier_info['cost_per_gb']:.4f}/GB - {tier_info['description']}")

                st.write("\n**Compute Options:**")
                for size, instance in provider_info['compute']['instances'].items():
                    st.write(
                        f"- {instance['name']}: ${instance['cost_per_hour']}/hour "
                        f"({instance['vcpus']} vCPUs, {instance['memory_gb']}GB RAM)"
                    )
        else:
            # Show provider comparison using tabs
            st.write("### Compare Cloud Providers")
            provider_tabs = st.tabs([CLOUD_PROVIDERS[p]['name'] for p in CLOUD_PROVIDERS])

            for tab, (provider_key, provider_info) in zip(provider_tabs, CLOUD_PROVIDERS.items()):
                with tab:
                    if provider_key == selected_provider:
                        st.write("**✓ Selected Provider**")

                    st.write("**Storage Options:**")
                    for tier_name, tier_info in provider_info['storage'].items():
                        st.write(
                            f"- {tier_info['name']}: ${tier_info['cost_per_gb']:.4f}/GB - {tier_info['description']}")

                    st.write("\n**Compute Options:**")
                    for size, instance in provider_info['compute']['instances'].items():
                        st.write(
                            f"- {instance['name']}: ${instance['cost_per_hour']}/hour "
                            f"({instance['vcpus']} vCPUs, {instance['memory_gb']}GB RAM)"
                        )

                    if 'additional' in provider_info['compute']:
                        st.write("\n**Additional Costs:**")
                        for cost_type, cost in provider_info['compute']['additional'].items():
                            st.write(f"- {cost_type.replace('_', ' ').title()}: ${cost}/hour")

    # Show recommendation info for "No" case
    if setup_type == "No":
        st.info("""
        Based on your data volume, growth rate, and processing requirements, 
        The tool analyzes and recommends the most cost-effective cloud provider in the final step.

        Key factors the tool considers:
        - Data volume and growth patterns
        - Processing requirements and compute needs
        - Storage access patterns and tier optimization
        - Geographic distribution and compliance needs
        - Cost optimization opportunities

        Your preferred provider will be compared against other options to make sure the best fit is made.
        """)

    # Navigation buttons
    col1, col2 = st.columns([4, 1])

    if st.button("Next →", disabled=not selected_provider):
        update_state(
            infrastructure={
                'type': 'existing' if setup_type == "Yes" else 'new',
                'provider': selected_provider if setup_type == "Yes" else None,
                'preferred_provider': selected_provider if setup_type == "No" else None
            }
        )
        update_state(step=2)
        st.rerun()

    if not selected_provider:
        st.warning("Please select a provider to proceed.")


def render_data_sources_step():
    st.header("Step 2: Data Sources Selection")

    state = get_state()

    selected = st.multiselect(
        "Select the types of data you want to include in your data hub:",
        options=list(DATA_CATEGORIES.keys()),
        format_func=lambda x: DATA_CATEGORIES[x]['label'],
        default=state.selected_sources
    )

    if selected:
        st.write("Selected data sources details:")
        for source in selected:
            with st.expander(f"{DATA_CATEGORIES[source]['label']}", expanded=True):
                st.write(f"**Description:** {DATA_CATEGORIES[source]['description']}")
                st.write(f"**Examples:** {DATA_CATEGORIES[source]['examples']}")

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        update_state(step=1)
        st.rerun()

    if col2.button("Next →", disabled=len(selected) == 0):
        update_state(step=3, selected_sources=selected)
        st.rerun()

    if not selected:
        st.warning("Please select at least one data source to proceed.")

def render_volume_estimation_step():
    st.header("Step 3: Volume Estimation")

    state = get_state()

    if not state.selected_sources:
        st.error("No data sources selected. Please go back and select data sources.")
        if st.button("← Back"):
            update_state(step=2)
            st.rerun()
        return

    volume_estimates = {}
    for source in state.selected_sources:
        category = DATA_CATEGORIES[source]
        st.subheader(category['label'])

        with st.expander("Enter volume details", expanded=True):
            cols = st.columns(3)
            daily = cols[0].number_input(
                "Daily Records",
                min_value=0,
                value=state.volume_estimates.get(source, {}).get('daily', 0),
                key=f"daily_{source}"
            )
            historical = cols[1].number_input(
                "Historical Records",
                min_value=0,
                value=state.volume_estimates.get(source, {}).get('historical', 0),
                key=f"historical_{source}"
            )
            growth = cols[2].number_input(
                "Expected Yearly Growth (%)",
                min_value=0.0,
                max_value=1000.0,
                value=state.volume_estimates.get(source, {}).get('growth', 0.0),
                key=f"growth_{source}"
            )
            volume_estimates[source] = {'daily': daily, 'historical': historical, 'growth': growth}

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        update_state(step=2)
        st.rerun()

    if col2.button("Next →"):
        update_state(step=4, volume_estimates=volume_estimates)
        st.rerun()

def render_review_step():
    st.header("Step 4: Review Your Selections")

    state = get_state()

    # Infrastructure Review
    with st.expander("Infrastructure", expanded=True):
        st.write("**Selected Infrastructure:**")
        if state.infrastructure['type'] == 'existing':
            provider = CLOUD_PROVIDERS[state.infrastructure['provider']]
            st.write(f"- Type: Existing Solution")
            st.write(f"- Cloud Provider: {provider['name']}")
        else:
            st.write("- Type: New Setup (provider will be recommended)")
            st.write(f"- Preferred Provider: {CLOUD_PROVIDERS[state.infrastructure['preferred_provider']]['name']}")

    # Data Sources Review
    with st.expander("Data Sources & Volumes", expanded=True):
        if not state.selected_sources:
            st.warning("No data sources selected")
        else:
            for source in state.selected_sources:
                category = DATA_CATEGORIES[source]
                estimates = state.volume_estimates.get(source, {})

                st.write(f"**{category['label']}**")
                cols = st.columns(3)
                cols[0].metric("Daily Records", f"{int(estimates.get('daily', 0)):,}")
                cols[1].metric("Historical Records", f"{int(estimates.get('historical', 0)):,}")
                cols[2].metric("Yearly Growth", f"{estimates.get('growth', 0)}%")

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        update_state(step=3)
        st.rerun()

    if col2.button("Next →"):
        update_state(step=5)
        st.rerun()


def render_recommendation_step():
    st.header("Step 5: Stack Recommendations")

    state = get_state()
    costs = calculate_costs(
        state.infrastructure,
        state.selected_sources,
        state.volume_estimates
    )

    visualization_seats = st.slider(
        "Number of visualization tool seats",
        min_value=1,
        max_value=50,
        value=state.visualization_seats,
        key="viz_seats"
    )
    update_state(visualization_seats=visualization_seats)

    # Get recommendations
    recommendations = get_stack_recommendations(costs, state.infrastructure, visualization_seats)

    # Display recommendations in tabs
    tabs = st.tabs(["Simple Stack", "Balanced Stack", "Advanced Stack"])

    for idx, (tab, rec) in enumerate(zip(tabs, recommendations)):
        with tab:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader(f"Option {idx + 1}: {rec['level'].title()} Stack")

                # Add summary based on complexity level
                if rec['level'] == 'simple':
                    st.info("✨ Optimized for ease of use and quick setup")
                elif rec['level'] == 'balanced':
                    st.info("⚖️ Good balance of features and complexity")
                else:  # advanced
                    st.info("🔧 Maximum flexibility and customization")

                for component, tool in rec['stack'].items():
                    with st.expander(f"{component.title()} Layer", expanded=True):
                        st.write(f"**Selected Tool:** {tool['name']}")
                        st.write(f"**Pricing:** {tool['pricing']}")
                        st.write("**Why this choice:**",
                                 "Easy to set up and use" if rec['level'] == 'simple' else
                                 "Good balance of features and usability" if rec['level'] == 'balanced' else
                                 "Advanced features and customization options"
                                 )
                        st.write("**Pros:**", tool['pros'])
                        st.write("**Cons:**", tool['cons'])
                        st.write("**Integrations:**", tool['integrations'])

                        # Show tool-specific details
                        if component == 'warehousing':
                            if tool.get('compute_pricing'):
                                st.write("\n**Compute Options:**")
                                for size, credits in tool['compute_pricing']['warehouse_sizes'].items():
                                    st.write(f"- {size}: {credits} credits/hour")
                        elif component == 'visualization':
                            if tool.get('license_types'):
                                st.write("\n**License Options:**")
                                for license_type, cost in tool['license_types'].items():
                                    st.write(f"- {license_type}: ${cost}/user/month")

            with col2:
                # Add cost explanation in expandable section
                with st.expander("💡 How are costs calculated?", expanded=False):
                    st.write("""
                    **Monthly costs are calculated based on:**
                    1. **Data Volume:**
                       - Daily records × 30 days
                       - Growth rate applied monthly
                       - Historical data storage
            
                    2. **Tool-Specific Pricing:**
                       - Base subscription costs
                       - Usage-based costs
                       - Per-seat licensing (where applicable)
                            """)    
                    
                st.subheader("Cost Breakdown")
                render_cost_breakdown_chart(rec['costs'])
                st.metric("Total Monthly Cost", f"${rec['costs']['total']:,.2f}")

                # Add cost considerations
                if rec['level'] == 'simple':
                    st.write("💡 Lower initial costs, may need to upgrade as you scale")
                elif rec['level'] == 'balanced':
                    st.write("💡 Moderate costs with room for growth")
                else:
                    st.write("💡 Higher initial cost but better economies of scale")

    # Show stack comparison if requested
    if st.checkbox("Show Stack Comparison"):
        render_stack_comparison_chart(recommendations)

        # Add comparison insights
        st.write("\n### Key Differences Between Stacks")
        cols = st.columns(3)

        with cols[0]:
            st.write("**Simple Stack**")
            st.write("- Quick to implement")
            st.write("- Minimal training needed")
            st.write("- Basic features")
            st.write("- Limited customization")

        with cols[1]:
            st.write("**Balanced Stack**")
            st.write("- Moderate setup time")
            st.write("- Some training required")
            st.write("- Advanced features")
            st.write("- Good customization")

        with cols[2]:
            st.write("**Advanced Stack**")
            st.write("- Complex implementation")
            st.write("- Significant training needed")
            st.write("- Full feature set")
            st.write("- Maximum flexibility")

    # Back button
    if st.button("← Back to Review"):
        update_state(step=4)
        st.rerun()

def main():
    st.set_page_config(page_title="Data Stack Builder", layout="wide")

    init_session_state()

    st.title("Data Stack Builder")
    st.write("Optimize your data infrastructure with tailored recommendations")

    state = get_state()
    st.progress(state.step / 5)

    if state.step == 1:
        render_infrastructure_step()
    elif state.step == 2:
        render_data_sources_step()
    elif state.step == 3:
        render_volume_estimation_step()
    elif state.step == 4:
        render_review_step()
    elif state.step == 5:
        render_recommendation_step()

if __name__ == "__main__":
    main()
