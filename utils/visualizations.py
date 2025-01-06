import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def render_cost_breakdown_chart(costs: dict):
    """
    Render a bar chart showing cost breakdown for a stack option.

    Args:
        costs (dict): Dictionary containing cost breakdowns for different components
    """
    # Skip total from components and ensure we only include actual costs
    components = [k for k, v in costs.items() if k.lower() != 'total' and v > 0]
    values = [costs[k] for k in components]

    # Create percentage of total for each component
    total = sum(values)
    percentages = [v / total * 100 for v in values]

    # Create horizontal bar chart with enhanced tooltips
    fig = go.Figure(data=[
        go.Bar(
            x=values,
            y=components,
            orientation='h',
            text=[f"${v:,.2f} ({p:.1f}%)" for v, p in zip(values, percentages)],
            textposition='auto',
            hovertemplate="<b>%{y}</b><br>" +
                          "Cost: $%{x:,.2f}<br>" +
                          "Percentage: %{customdata:.1f}%<extra></extra>",
            customdata=percentages
        )
    ])

    # Update layout
    fig.update_layout(
        title="Monthly Costs Breakdown",
        xaxis_title="Cost ($)",
        yaxis_title="Component",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
        yaxis=dict(
            showgrid=False,
        )
    )

    # Update bars appearance
    fig.update_traces(
        marker_color='rgb(0, 104, 201)',
        marker_line_color='rgb(0, 73, 141)',
        marker_line_width=1.5,
        opacity=0.8
    )

    st.plotly_chart(fig, use_container_width=True)


def render_stack_comparison_chart(recommendations: list, exclude_modeling: bool = False):
    """
    Render a stacked bar chart comparing different stack options.

    Args:
        recommendations (list): List of dictionaries containing stack recommendations
        exclude_modeling (bool): Whether modeling component is excluded
    """
    # Prepare data for visualization with tool names
    comparison_data = []
    for rec in recommendations:
        for component, cost in rec['costs'].items():
            # Skip the total component and modeling if excluded
            if component.lower() == 'total':
                continue
            if exclude_modeling and component.lower() == 'modeling':
                continue

            # Get tool name if it's a component with a tool
            tool_name = rec['stack'].get(component, {}).get('name', '') if component != 'infrastructure' else 'Cloud Infrastructure'

            if component != 'infrastructure':
                comparison_data.append({
                    'Stack': rec['level'].title(),
                    'Component': component.title(),
                    'Cost': cost,
                    'Tool': tool_name,
                    'text': f'${cost:,.0f}\n{tool_name}'
                })

    # Calculate percentages for each stack
    df = pd.DataFrame(comparison_data)
    stack_totals = df.groupby('Stack')['Cost'].sum().to_dict()
    df['percentage'] = df.apply(lambda row: (row['Cost'] / stack_totals[row['Stack']]) * 100, axis=1)

    # Define color map based on included components
    base_color_map = {
        'Extraction': '#66c2a5',
        'Warehousing': '#8da0cb',
        'Visualization': '#e78ac3'
    }
    if not exclude_modeling:
        base_color_map['Modeling'] = '#fc8d62'

    # Create stacked bar chart
    fig = px.bar(
        df,
        x='Stack',
        y='Cost',
        color='Component',
        color_discrete_map=base_color_map,
        title='Cost Comparison Across Stack Options',
        barmode='stack',
        height=500,
        labels={'Cost': 'Monthly Cost ($)', 'Stack': 'Stack Option'},
        text='text'
    )

    # Update traces to show text inside bars and remove hover
    fig.update_traces(
        textposition='inside',
        hoverinfo='skip',
        textangle=0,
        insidetextanchor='middle',
        textfont=dict(size=10)
    )

    # Update layout
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            title="Monthly Cost ($)",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
        xaxis=dict(
            title="Stack Option",
            showgrid=False
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Add total cost comparison below the chart
    st.write("**Total Estimated Monthly Cost by Stack:**")
    total_costs = pd.DataFrame(list(stack_totals.items()), columns=['Stack', 'Total Cost'])
    total_costs = total_costs.sort_values('Total Cost')
    cols = st.columns(len(stack_totals))
    for idx, (stack, total) in enumerate(total_costs.values):
        cols[idx].metric(stack, f"${total:,.2f}/month")


def render_monthly_growth_projection(initial_cost: float, growth_rate: float, months: int = 12):
    """
    Render a line chart showing projected costs over time.

    Args:
        initial_cost (float): Starting monthly cost
        growth_rate (float): Monthly growth rate as a percentage
        months (int): Number of months to project
    """
    # Calculate projected costs
    monthly_costs = []
    cumulative_costs = []
    running_total = 0

    for month in range(months):
        cost = initial_cost * (1 + growth_rate / 100) ** month
        running_total += cost
        monthly_costs.append(cost)
        cumulative_costs.append(running_total)

    # Create line chart
    fig = go.Figure()

    # Add monthly cost line
    fig.add_trace(go.Scatter(
        x=list(range(1, months + 1)),
        y=monthly_costs,
        mode='lines+markers',
        name='Monthly Cost',
        line=dict(color='rgb(0, 104, 201)', width=2),
        marker=dict(size=8)
    ))

    # Add cumulative cost line
    fig.add_trace(go.Scatter(
        x=list(range(1, months + 1)),
        y=cumulative_costs,
        mode='lines',
        name='Cumulative Cost',
        line=dict(color='rgb(201, 104, 0)', width=2, dash='dot')
    ))

    # Update layout
    fig.update_layout(
        title="12-Month Cost Projection",
        xaxis_title="Month",
        yaxis_title="Cost ($)",
        height=400,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Add hover templates
    fig.update_traces(
        hovertemplate="%{y:$,.2f}<br>Month: %{x}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)
