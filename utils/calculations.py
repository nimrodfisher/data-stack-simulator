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


def get_stack_recommendations(costs: Dict, infrastructure: Dict, visualization_seats: int = 1) -> List[Dict]:
    """Generate stack recommendations based on data volume and costs."""
    monthly_active_rows = costs['total_records_per_month']
    monthly_models = int(costs['total_records_per_month'] / 1000)

    # If this is a new setup, recommend a provider
    if infrastructure['type'] == 'new':
        avg_growth_rate = sum(
            float(vol.get('growth', 0))
            for vol in costs['volume_estimates'].values()
        ) / len(costs['volume_estimates'])

        infrastructure['provider'] = recommend_cloud_provider(
            monthly_active_rows,
            avg_growth_rate
        )

    # Get the provider (either existing or recommended)
    provider = infrastructure.get('provider') or infrastructure.get('preferred_provider')

    # Filter warehousing options based on cloud provider
    warehousing_options = []
    for warehouse in TOOLS_DATA['warehousing']:
        if provider == 'gcp' and warehouse['name'] == 'BigQuery':
            warehousing_options.append(warehouse)
        elif provider == 'aws' and warehouse['name'] == 'Snowflake':
            warehousing_options.append(warehouse)
        elif provider == 'azure':
            # For Azure, include both but sort by cost+complexity
            if warehouse['name'] in ['BigQuery', 'Snowflake']:
                warehousing_options.append(warehouse)

    # Sort warehousing options by combined score of cost and complexity
    if provider == 'azure':
        warehousing_options.sort(key=lambda x: x['base_price'] + (x['complexity'] * 100))

    recommendations = []

    # Simple Stack (optimize for simplicity)
    simple_stack = {
        'extraction': min(TOOLS_DATA['extraction'], key=lambda x: x['complexity']),
        'modeling': min(TOOLS_DATA['modeling'], key=lambda x: x['complexity']),
        'warehousing': warehousing_options[0],  # Already filtered/sorted based on provider
        'visualization': min(TOOLS_DATA['visualization'], key=lambda x: x['complexity'])
    }

    # Advanced Stack (optimize for features/capabilities)
    advanced_stack = {
        'extraction': max(TOOLS_DATA['extraction'], key=lambda x: x['complexity']),
        'modeling': max(TOOLS_DATA['modeling'], key=lambda x: x['complexity']),
        'warehousing': warehousing_options[0],  # Already filtered/sorted based on provider
        'visualization': max(TOOLS_DATA['visualization'], key=lambda x: x['complexity'])
    }
    for rec in recommendations:
      if exclude_modeling:
          # Remove modeling costs from total if excluded
          modeling_cost = rec['costs'].get('modeling', 0)
          rec['costs']['total'] -= modeling_cost
    return recommendations

    # Balanced Stack (optimize for both cost and complexity)
    def get_balanced_tool(tools):
        # Sort tools by a combined score of cost and complexity
        return sorted(tools, key=lambda x: (x['base_price'] + (x['complexity'] * 100)))[len(tools) // 2]

    balanced_stack = {
        'extraction': get_balanced_tool(TOOLS_DATA['extraction']),
        'modeling': get_balanced_tool(TOOLS_DATA['modeling']),
        'warehousing': warehousing_options[0],  # Already filtered/sorted based on provider
        'visualization': get_balanced_tool(TOOLS_DATA['visualization'])
    }

    # Calculate costs for each stack
    for stack_type, stack in [
        ('simple', simple_stack),
        ('balanced', balanced_stack),
        ('advanced', advanced_stack)
    ]:
        # Calculate tool costs
        extraction_cost = calculate_extraction_cost(stack['extraction'], monthly_active_rows)
        modeling_cost = monthly_models * 0.0001 + stack['modeling']['base_price']
        warehousing_cost = stack['warehousing']['base_price']
        visualization_cost = stack['visualization'].get('seat_cost', 0) * visualization_seats

        recommendations.append({
            'level': stack_type,
            'stack': stack,
            'costs': {
                'extraction': extraction_cost,
                'modeling': modeling_cost,
                'warehousing': warehousing_cost,
                'visualization': visualization_cost,
                'total': (extraction_cost + modeling_cost + warehousing_cost + visualization_cost)
            }
        })

    return recommendations
