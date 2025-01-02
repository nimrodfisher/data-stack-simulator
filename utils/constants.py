# Data categories with their properties
DATA_CATEGORIES = {
    "transactional": {
        "label": "Transactional Data",
        "description": "Payment processing, orders, subscriptions",
        "examples": "Stripe, Shopify, Adapty",
        "cost_per_record": 0.0001,
        "storage_multiplier": 1.5,
    },
    "product": {
        "label": "Product Analytics",
        "description": "User behavior, feature usage, engagement",
        "examples": "Amplitude, Mixpanel, Heap",
        "cost_per_record": 0.00005,
        "storage_multiplier": 2,
    },
    "marketing": {
        "label": "Marketing Data",
        "description": "Campaigns, email marketing, advertising",
        "examples": "HubSpot, Marketo, Google Ads",
        "cost_per_record": 0.00015,
        "storage_multiplier": 1.8,
    },
    "customer": {
        "label": "Customer Data",
        "description": "Customer relationship management",
        "examples": "Salesforce, HubSpot",
        "cost_per_record": 0.0002,
        "storage_multiplier": 1.7,
    }
}

# Updated cloud provider configurations with detailed pricing
CLOUD_PROVIDERS = {
    "aws": {
        "name": "Amazon Web Services (AWS)",
        "storage": {
            "standard": {
                "name": "S3 Standard",
                "cost_per_gb": 0.023,
                "description": "For frequently accessed data",
                "request_costs": {
                    "put": 0.005,  # per 1000 requests
                    "get": 0.0004  # per 1000 requests
                }
            },
            "infrequent_access": {
                "name": "S3 Infrequent Access",
                "cost_per_gb": 0.0125,
                "description": "For infrequent access (minimum 30 days)",
                "request_costs": {
                    "put": 0.01,
                    "get": 0.001
                }
            },
            "glacier": {
                "name": "S3 Glacier",
                "cost_per_gb": 0.004,
                "description": "For archival storage",
                "retrieval_cost": 0.03  # per GB retrieved
            }
        },
        "compute": {
            "instances": {
                "small": {
                    "name": "t2.micro",
                    "cost_per_hour": 0.0116,
                    "vcpus": 1,
                    "memory_gb": 1
                },
                "medium": {
                    "name": "m5.large",
                    "cost_per_hour": 0.096,
                    "vcpus": 2,
                    "memory_gb": 8
                },
                "large": {
                    "name": "m5.xlarge",
                    "cost_per_hour": 0.192,
                    "vcpus": 4,
                    "memory_gb": 16
                }
            },
            "data_processing": 0.048  # per million records
        }
    },
    "gcp": {
        "name": "Google Cloud Platform (GCP)",
        "storage": {
            "standard": {
                "name": "Standard Storage",
                "cost_per_gb": 0.0204,
                "description": "For frequently accessed data",
                "operation_costs": {
                    "class_a": 0.005,  # per 1000 operations
                    "class_b": 0.0004  # per 1000 operations
                }
            },
            "nearline": {
                "name": "Nearline Storage",
                "cost_per_gb": 0.0102,
                "description": "For infrequent access (minimum 30 days)",
                "retrieval_cost": 0.01  # per GB retrieved
            },
            "coldline": {
                "name": "Coldline Storage",
                "cost_per_gb": 0.004,
                "description": "For rarely accessed data (minimum 90 days)",
                "retrieval_cost": 0.02
            },
            "archive": {
                "name": "Archive Storage",
                "cost_per_gb": 0.0012,
                "description": "For long-term archival (minimum 365 days)",
                "retrieval_cost": 0.05
            }
        },
        "compute": {
            "instances": {
                "small": {
                    "name": "n1-standard-1",
                    "cost_per_hour": 0.0475,
                    "vcpus": 1,
                    "memory_gb": 3.75
                },
                "medium": {
                    "name": "n1-standard-2",
                    "cost_per_hour": 0.095,
                    "vcpus": 2,
                    "memory_gb": 7.5
                },
                "large": {
                    "name": "n1-standard-4",
                    "cost_per_hour": 0.19,
                    "vcpus": 4,
                    "memory_gb": 15
                }
            },
            "data_processing": 0.045,  # per million records
            "additional": {
                "ip_address": 0.005,  # per hour
                "load_balancing": 0.025  # per hour
            }
        }
    },
    "azure": {
        "name": "Microsoft Azure",
        "storage": {
            "hot": {
                "name": "Blob Storage (Hot)",
                "cost_per_gb": 0.0184,
                "description": "For frequently accessed data"
            },
            "cool": {
                "name": "Blob Storage (Cool)",
                "cost_per_gb": 0.01,
                "description": "For infrequently accessed data",
                "min_duration": 30
            },
            "archive": {
                "name": "Blob Storage (Archive)",
                "cost_per_gb": 0.00099,
                "description": "For long-term archival",
                "min_duration": 365
            }
        },
        "compute": {
            "instances": {
                "small": {
                    "name": "B1ls",
                    "cost_per_hour": 0.008,
                    "vcpus": 1,
                    "memory_gb": 0.5
                },
                "medium": {
                    "name": "D2s_v3",
                    "cost_per_hour": 0.096,
                    "vcpus": 2,
                    "memory_gb": 8
                },
                "large": {
                    "name": "D4s_v3",
                    "cost_per_hour": 0.192,
                    "vcpus": 4,
                    "memory_gb": 16
                }
            },
            "data_processing": 0.046  # per million records
        }
    }
}

# Tool configurations remain the same but I'll share if you'd like to see the complete updated version
TOOLS_DATA = {
    "extraction": [
        {
            "name": "Fivetran",
            "base_price": 500,
            "complexity": 2,
            "pricing": "Base price $500/month + $0.50 per 1000 monthly active rows",
            "price_formula": "rows_in_thousands * 0.50 + 500",
            "pros": "Wide connector library, reliable syncs, minimal maintenance",
            "cons": "Can be expensive at scale, limited customization",
            "integrations": "Supports 150+ pre-built connectors",
            "license_type": "SaaS"
        },
{
        "name": "Rivery",
        "base_price": 200,  # Starter tier price
        "complexity": 2,
        "pricing": "Starts at $200/month (Starter), $1000/month (Growth), Custom (Enterprise)",
        "price_formula": "base_price + (rows_in_thousands * 0.45)",  # Note: actual pricing may vary based on tier
        "pros": "Data transformation capabilities, logic-based workflows, serverless, native Git integration",
        "cons": "Different tiers have feature limitations, premium features require higher tiers",
        "integrations": "190+ data sources and destinations",
        "license_type": "SaaS",
        "pricing_tiers": {
            "starter": {
                "price": 200,
                "features": [
                    "5 users",
                    "Unlimited sources & targets",
                    "Email support"
                ]
            },
            "growth": {
                "price": 1000,
                "features": [
                    "10 users",
                    "Advanced transformations",
                    "Priority support"
                ]
            },
            "enterprise": {
                "price": "Custom",
                "features": [
                    "Unlimited users",
                    "Custom SLAs",
                    "Dedicated support"
                ]
            }
        }
    },
        {
            "name": "Stitch",
            "base_price": 400,
            "complexity": 1,
            "pricing": "Base price $400/month + $0.40 per 1000 monthly active rows",
            "price_formula": "rows_in_thousands * 0.40 + 400",
            "pros": "Simple setup, good documentation, cost-effective",
            "cons": "Less customization options, fewer advanced features",
            "integrations": "Supports 100+ data sources",
            "license_type": "SaaS"
        },
        {
            "name": "Airbyte",
            "base_price": 300,
            "complexity": 3,
            "pricing": "Base price $300/month + $0.30 per 1000 monthly active rows",
            "price_formula": "rows_in_thousands * 0.30 + 300",
            "pros": "Open-source, highly customizable, growing community",
            "cons": "Requires more technical expertise, newer platform",
            "integrations": "Supports 140+ connectors, custom connector development",
            "license_type": "Open Source / SaaS"
        }
    ],
    "modeling": [
        {
            "name": "dbt",
            "base_price": 100,
            "complexity": 2,
            "pricing": "Base price $100/month + $0.01 per 1000 models executed",
            "price_formula": "monthly_models_thousands * 0.10 + 100",
            "pros": "Industry standard, great documentation, strong community",
            "cons": "Steep learning curve, requires SQL expertise",
            "integrations": "Works with all major data warehouses",
            "license_type": "Open Source / SaaS"
        },
        {
            "name": "Dataform",
            "base_price": 250,
            "complexity": 2,
            "pricing": "Base price $250/month + $0.15 per 1000 models executed",
            "price_formula": "monthly_models_thousands * 0.15 + 250",
            "pros": "User-friendly interface, GCP native integration",
            "cons": "Less flexible than dbt, smaller community",
            "integrations": "Native BigQuery integration, supports other warehouses",
            "license_type": "SaaS"
        }
    ],
    "warehousing": [
        {
            "name": "Snowflake",
            "base_price": 1000,
            "complexity": 2,
            "pricing": "Pay-as-you-go; storage $23/TB/month, compute varies",
            "price_formula": "base_price + (storage_tb * 23) + (compute_units * 2.5)",
            "pros": "Highly scalable; supports multiple data formats",
            "cons": "Complex pricing; can be expensive with high usage",
            "integrations": "Works with various ETL tools and BI platforms",
            "license_type": "SaaS",
            "compute_pricing": {
                "warehouse_sizes": {
                    "x-small": 1,
                    "small": 2,
                    "medium": 4,
                    "large": 8
                },
                "cost_per_credit": 2.5
            }
        },
        {
            "name": "BigQuery",
            "base_price": 800,
            "complexity": 1,
            "pricing": "$5/TB queried (on-demand) or $2,000/month (flat-rate)",
            "price_formula": "base_price + (tb_queried * 5)",
            "pros": "Serverless; easy for SQL users",
            "cons": "Costs can add up with large queries",
            "integrations": "Seamless with Google Cloud and various ETL tools",
            "license_type": "SaaS",
            "storage_pricing": {
                "active": 0.02,  # per GB
                "long_term": 0.01  # per GB
            }
        },
        {
            "name": "Redshift",
            "base_price": 1200,
            "complexity": 3,
            "pricing": "Starts at $0.25/hour per DC2.Large node",
            "price_formula": "base_price + (node_hours * node_type_cost)",
            "pros": "Integrated with AWS ecosystem; good for large datasets",
            "cons": "Requires more hands-on management; less flexible scaling",
            "integrations": "Strong integration with AWS services and various BI tools",
            "license_type": "SaaS",
            "node_types": {
                "dc2.large": 0.25,
                "dc2.8xlarge": 2.00,
                "ra3.xlplus": 1.086,
                "ra3.4xlarge": 4.344
            }
        }
    ],
    "visualization": [
        {
            "name": "Tableau",
            "base_price": 70,
            "seat_cost": 70,
            "complexity": 2,
            "pricing": "Starts at $70/user/month (Creator)",
            "price_formula": "seats * seat_cost",
            "pros": "Powerful visualization; wide integrations",
            "cons": "High cost for full features; steep learning curve",
            "integrations": "Connects to numerous data sources",
            "license_type": "Per-user",
            "license_types": {
                "creator": 70,
                "explorer": 35,
                "viewer": 15
            }
        },
        {
            "name": "Power BI",  # Balanced option
            "base_price": 20,
            "seat_cost": 20,
            "complexity": 2,
            "pricing": "Pro $20/user/month, Premium from $4,995/month",
            "price_formula": "seats * seat_cost",
            "pros": "Cost-effective; strong Microsoft integration; good balance of features",
            "cons": "Limited free version; some features require Premium",
            "integrations": "Excellent with Microsoft products and services",
            "license_type": "Per-user / Premium",
            "license_types": {
                "pro": 20,
                "premium_per_user": 30,
                "premium_per_capacity": 4995
            },
            "best_for": "Mid-size teams using Microsoft stack"
        },
        {
            "name": "Looker Studio",  # formerly Google Data Studio
            "base_price": 0,
            "seat_cost": 0,
            "complexity": 1,  # Changed from 3 to 1
            "pricing": "Free",
            "price_formula": "0",
            "pros": "Easy to use; good for simple visualizations; free",
            "cons": "Limited advanced features; basic customization options",
            "integrations": "Works well with Google products",
            "license_type": "Free",
            "best_for": "Teams getting started with data visualization"
        },
        {
            "name": "Looker Enterprise",  # Added as separate product
            "base_price": 3000,
            "seat_cost": 100,
            "complexity": 3,
            "pricing": "Enterprise pricing (contact sales)",
            "price_formula": "basePrice + (seats * seat_cost)",
            "pros": "Advanced analytics; LookML for data modeling; enterprise features",
            "cons": "High cost; requires technical expertise; complex setup",
            "integrations": "Enterprise-grade integrations with major data warehouses",
            "license_type": "Enterprise",
            "best_for": "Large organizations with complex analytics needs"
        }
    ]
}
