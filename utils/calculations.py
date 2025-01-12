from typing import Dict, List
from .constants import DATA_CATEGORIES, CLOUD_PROVIDERS, TOOLS_DATA
import math


def calculate_detailed_cloud_costs(provider_key: str, storage_gb: float, monthly_records: float,
                                   historical_records: float) -> Dict:
    """Calculate detailed cloud provider costs including storage tiers and compute."""
    # Handle case where provider_key might be None or invalid
    if not provider_key or provider_key not in CLOUD_PROVIDERS:
        # Default to AWS if no valid provider is specified
        provider_key = 'aws'

    provider = CLOUD_PROVIDERS[provider_key]

    # Determine storage distribution based on data age
    storage_distribution = {
        'hot': 0.7,  # 70% of data in hot storage
        'warm': 0.2,  # 20% in infrequent access
        'cold': 0.1  # 10% in archive
    }

    # Calculate storage costs based on tiers
    storage_costs = {}
    if provider_key == 'aws':
        storage_costs = {
            'standard': storage_gb * storage_distribution['hot'] * provider['storage']['standard']['cost_per_gb'],
            'ia': storage_gb * storage_distribution['warm'] * provider['storage']['infrequent_access']['cost_per_gb'],
            'glacier': storage_gb * storage_distribution['cold'] * provider['storage']['glacier']['cost_per_gb']
        }
    elif provider_key == 'gcp':
        storage_costs = {
            'standard': storage_gb * storage_distribution['hot'] * provider['storage']['standard']['cost_per_gb'],
            'nearline': storage_gb * storage_distribution['warm'] * provider['storage']['nearline']['cost_per_gb'],
            'coldline': storage_gb * storage_distribution['cold'] * provider['storage']['coldline']['cost_per_gb']
        }
    else:  # azure
        storage_costs = {
            'hot': storage_gb * storage_distribution['hot'] * provider['storage']['hot']['cost_per_gb'],
            'cool': storage_gb * storage_distribution['warm'] * provider['storage']['cool']['cost_per_gb'],
            'archive': storage_gb * storage_distribution['cold'] * provider['storage']['archive']['cost_per_gb']
        }

    # Calculate compute costs based on data processing volume
    compute_instance = provider['compute']['instances']['medium']  # Default to medium instance
    compute_hours = 24 * 30  # Assume 24/7 operation
    compute_costs = {
        'instance': compute_instance['cost_per_hour'] * compute_hours,
        'processing': (monthly_records / 1_000_000) * provider['compute']['data_processing']
    }

    return {
        'storage_costs': storage_costs,
        'compute_costs': compute_costs,
        'total_storage_cost': sum(storage_costs.values()),
        'total_compute_cost': sum(compute_costs.values()),
        'total_cost': sum(storage_costs.values()) + sum(compute_costs.values())
    }


def calculate_extraction_cost(tool: Dict, monthly_records: float) -> float:
    """Calculate extraction tool cost based on monthly records."""
    # Convert to thousands of rows and round up
    rows_in_thousands = math.ceil(monthly_records / 1000)

    if tool['name'] == 'Fivetran':
        return tool['base_price'] + (rows_in_thousands * 0.50)
    elif tool['name'] == 'Stitch':
        return tool['base_price'] + (rows_in_thousands * 0.40)
    else:  # Airbyte
        return tool['base_price'] + (rows_in_thousands * 0.30)


def calculate_costs(infrastructure: Dict, selected_sources: List[str], volume_estimates: Dict) -> Dict:
    """Calculate infrastructure and tool costs with detailed explanations."""
    total_storage_gb = 0
    total_monthly_records = 0
    total_historical_records = 0
    processing_cost = 0
    cost_breakdown = {}

    # Handle case where infrastructure might be None
    if not infrastructure:
        infrastructure = {'type': 'new', 'provider': 'aws', 'preferred_provider': None}

    for source in selected_sources:
        category = DATA_CATEGORIES[source]
        estimates = volume_estimates.get(source, {})

        # Calculate monthly records with growth
        daily_records = float(estimates.get('daily', 0))
        yearly_growth_rate = float(estimates.get('growth', 0)) / 100
        monthly_growth_rate = (1 + yearly_growth_rate) ** (1 / 12) - 1
        monthly_records = daily_records * 30 * (1 + monthly_growth_rate)

        total_monthly_records += monthly_records

        # Calculate storage requirements
        historical_records = float(estimates.get('historical', 0))
        total_historical_records += historical_records
        record_size_kb = 1  # 1KB per record assumption
        storage_gb = (historical_records + monthly_records) * record_size_kb / (1024 * 1024)
        total_storage_gb += storage_gb

        # Calculate processing costs
        source_processing_cost = monthly_records * category['cost_per_record']
        processing_cost += source_processing_cost

        # Store breakdown
        cost_breakdown[source] = {
            'monthly_records': monthly_records,
            'storage_gb': storage_gb,
            'processing_cost': source_processing_cost
        }

    # Determine provider key based on infrastructure type
    provider_key = None
    if infrastructure['type'] == 'existing':
        provider_key = infrastructure.get('provider')
    else:
        provider_key = infrastructure.get('preferred_provider')

    # Calculate cloud costs
    cloud_costs = calculate_detailed_cloud_costs(
        provider_key,
        total_storage_gb,
        total_monthly_records,
        total_historical_records
    )

    return {
        'total_storage_gb': total_storage_gb,
        'total_records_per_month': total_monthly_records,
        'storage_cost': cloud_costs['total_storage_cost'],
        'compute_cost': cloud_costs['total_compute_cost'],
        'processing_cost': processing_cost,
        'total_cost': cloud_costs['total_cost'] + processing_cost,
        'breakdown': cost_breakdown,
        'cloud_costs': cloud_costs,
        'provider': provider_key,
        'volume_estimates': volume_estimates
    }


def recommend_cloud_provider(data_volume: float, growth_rate: float) -> str:
    """Recommend the most suitable cloud provider based on requirements."""
    if data_volume > 10_000_000:  # Over 10M records
        if growth_rate > 50:  # High growth
            return 'gcp'  # GCP for high growth, large volumes
        else:
            return 'aws'  # AWS for stable, large volumes
    else:
        if growth_rate > 50:
            return 'gcp'  # GCP for high growth
        else:
            return 'azure'  # Azure for smaller, stable workloads


def get_stack_recommendations(costs: Dict, infrastructure: Dict, visualization_seats: int = 1, exclude_modeling: bool = False) -> List[Dict]:
    """Generate stack recommendations based on data volume and costs."""
    monthly_active_rows = costs['total_records_per_month']
    monthly_models = int(costs['total_records_per_month'] / 1000)

    # Get provider and filter warehousing options
    provider = infrastructure.get('provider') or infrastructure.get('preferred_provider')
    warehousing_options = []
    for warehouse in TOOLS_DATA['warehousing']:
        if provider == 'gcp' and warehouse['name'] == 'BigQuery':
            warehousing_options.append(warehouse)
        elif provider == 'aws' and warehouse['name'] == 'Snowflake':
            warehousing_options.append(warehouse)
        elif provider == 'azure':
            if warehouse['name'] in ['BigQuery', 'Snowflake']:
                warehousing_options.append(warehouse)

    def get_extraction_tool(level: str) -> Dict:
        """Get appropriate extraction tool based on stack level."""
        tools = TOOLS_DATA['extraction']

        if level == 'simple':
            # For simple stack, choose between Airbyte and Stitch only
            simple_tools = [t for t in tools if t['name'] in ['Airbyte', 'Stitch']]
            return min(simple_tools, key=lambda x: x['base_price'] + (x['complexity'] * 50))
        else:
            # For both balanced and advanced, we'll work with Fivetran and Rivery
            premium_tools = [t for t in tools if t['name'] in ['Fivetran', 'Rivery']]
            # Sort by base price to determine which goes to balanced vs advanced
            sorted_premium = sorted(premium_tools, key=lambda x: x['base_price'])

            if level == 'balanced':
                # Return the cheaper of Fivetran/Rivery
                return sorted_premium[0]
            else:  # advanced
                # Return the more expensive of Fivetran/Rivery
                return sorted_premium[1]

    def get_modeling_tool(level: str) -> Dict:
        """Get appropriate modeling tool based on stack level."""
        tools = TOOLS_DATA['modeling']
        if level == 'simple':
            return min(tools, key=lambda x: x['base_price'])
        elif level == 'advanced':
            return max(tools, key=lambda x: x['complexity'])
        else:
            return sorted(tools, key=lambda x: x['base_price'] + (x['complexity'] * 100))[1]

    # Build stacks with all components
    stacks = {
        'simple': {
            'extraction': get_extraction_tool('simple'),
            'modeling': get_modeling_tool('simple'),
            'warehousing': warehousing_options[0],
            'visualization': next(t for t in TOOLS_DATA['visualization'] if t['name'] == 'Looker Studio')
        },
        'balanced': {
            'extraction': get_extraction_tool('balanced'),
            'modeling': get_modeling_tool('balanced'),
            'warehousing': warehousing_options[0],
            'visualization': next(t for t in TOOLS_DATA['visualization'] if t['name'] == 'Power BI')
        },
        'advanced': {
            'extraction': get_extraction_tool('advanced'),
            'modeling': get_modeling_tool('advanced'),
            'warehousing': warehousing_options[0],
            'visualization': next(t for t in TOOLS_DATA['visualization'] if t['name'] == 'Looker Enterprise')
        }
    }

    recommendations = []
    for level, stack in stacks.items():
        # Remove modeling if excluded
        working_stack = stack.copy()
        if exclude_modeling:
            working_stack.pop('modeling', None)

        # Calculate costs
        costs_dict = {
            'extraction': calculate_extraction_cost(working_stack['extraction'], monthly_active_rows),
            'warehousing': working_stack['warehousing']['base_price'],
            'visualization': working_stack['visualization'].get('seat_cost', 0) * visualization_seats
        }

        # Add modeling cost if included
        if not exclude_modeling:
            costs_dict['modeling'] = monthly_models * 0.0001 + working_stack['modeling']['base_price']

        # Calculate total cost
        total_cost = sum(costs_dict.values())

        # Add modeling capabilities note for Rivery
        modeling_note = None
        if working_stack['extraction']['name'] == 'Rivery':
            modeling_note = "Rivery provides built-in data modeling capabilities that can be leveraged without additional tools."

        recommendations.append({
            'level': level,
            'stack': working_stack,
            'costs': {
                **costs_dict,
                'total': total_cost
            },
            'modeling_note': modeling_note
        })

    # Ensure simple stack is the cheapest option
    recommendations.sort(key=lambda x: x['costs']['total'])
    if recommendations[0]['level'] != 'simple':
        simple_idx = next(i for i, r in enumerate(recommendations) if r['level'] == 'simple')
        recommendations[0], recommendations[simple_idx] = recommendations[simple_idx], recommendations[0]

    return recommendations
