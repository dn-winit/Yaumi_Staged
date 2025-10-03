from pydantic import BaseModel, Field
from typing import Optional, List

class DashboardFilters(BaseModel):
    route_codes: List[str] = Field(alias="routeCodes")  # Changed to support multiple routes
    item_codes: List[str] = Field(default=["All"], alias="itemCodes")  # Changed to support multiple items
    period: str = "Daily"  # Daily, Weekly, Monthly
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")

    class Config:
        populate_by_name = True

class ForecastFilters(BaseModel):
    route_codes: List[str] = Field(alias="routeCodes")  # Support multiple routes
    item_codes: List[str] = Field(default=["All"], alias="itemCodes")  # Support multiple items
    period: str = "Daily"  # Daily, Weekly, Monthly

    class Config:
        populate_by_name = True

class RecommendedOrderFilters(BaseModel):
    route_codes: List[str] = Field(alias="routeCodes")  # Support multiple routes
    customer_codes: List[str] = Field(default=["All"], alias="customerCodes")  # Support multiple customers
    item_codes: List[str] = Field(default=["All"], alias="itemCodes")  # Support multiple items
    date: str  # Expected format: YYYY-MM-DD

    class Config:
        populate_by_name = True

class GenerateRecommendationsRequest(BaseModel):
    date: str  # Expected format: YYYY-MM-DD
    route_code: Optional[str] = Field(default=None, alias="routeCode")  # Optional route code parameter

    class Config:
        populate_by_name = True

class DashboardData(BaseModel):
    date: str
    route: str  # Route code
    item: str
    actual: float
    predicted: float
    route_code: str
    item_code: str
    item_breakdown: Optional[List[dict]] = None  # For expandable rows: list of items for this date

class ForecastData(BaseModel):
    date: str
    route: str  # Route code
    item: str
    predicted: float

class HistoricalAverages(BaseModel):
    period: str
    data: dict

class FilterOptions(BaseModel):
    routes: List[dict]
    items: List[dict]

class PaginationInfo(BaseModel):
    current_page: int
    page_size: int
    total_pages: int
    total_records: int
    has_next: bool
    has_previous: bool

class PaginatedResponse(BaseModel):
    data: List[dict]
    pagination: PaginationInfo

class SalesSupervisionFilters(BaseModel):
    route_code: str
    date: str  # Expected format: YYYY-MM-DD

class SupervisionSessionRequest(BaseModel):
    route_code: str
    date: str  # Expected format: YYYY-MM-DD

class ProcessCustomerVisitRequest(BaseModel):
    route_code: str
    date: str
    customer_code: str
    actual_sales: dict  # {item_code: quantity}

# ============= ANALYSIS MODELS =============

class CustomerAnalysisResponse(BaseModel):
    """Structured response for customer-level analysis"""
    customer_code: str
    performance_summary: str = Field(
        default="",
        description="2-3 sentence overview of visit performance"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="What went well in this visit (3-5 points)"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="What needs improvement (3-5 points)"
    )
    likely_reasons: List[str] = Field(
        default_factory=list,
        description="Root causes for performance gaps (3-5 points)"
    )
    immediate_actions: List[str] = Field(
        default_factory=list,
        description="Actions to take within 24 hours (3-5 points)"
    )
    follow_up_actions: List[str] = Field(
        default_factory=list,
        description="Actions for next visit or week (3-5 points)"
    )
    identified_patterns: List[str] = Field(
        default_factory=list,
        description="Historical patterns observed (2-4 points)"
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Warning signs requiring attention (2-4 points)"
    )

    class Config:
        extra = "ignore"  # Ignore extra fields from analysis
        json_schema_extra = {
            "example": {
                "customer_code": "C001",
                "performance_summary": "Customer showed moderate performance with 68.5% score...",
                "strengths": ["Dairy items performed well at 95%"],
                "weaknesses": ["Fresh Bread zero-sale despite recommendation"],
                "immediate_actions": ["Call customer to verify bread stock situation"]
            }
        }

class RouteAnalysisResponse(BaseModel):
    """Structured response for route-level analysis"""
    route_code: str
    route_summary: str = Field(
        default="",
        description="Overall route performance overview (2-3 sentences)"
    )
    high_performers: List[str] = Field(
        default_factory=list,
        description="Top performing customers with scores and brief reason (3-5 customers)"
    )
    needs_attention: List[str] = Field(
        default_factory=list,
        description="Customers requiring follow-up with specific issues (3-5 customers)"
    )
    route_strengths: List[str] = Field(
        default_factory=list,
        description="What's working well across the route (3-5 points)"
    )
    route_weaknesses: List[str] = Field(
        default_factory=list,
        description="Areas needing improvement route-wide (3-5 points)"
    )
    optimization_opportunities: List[str] = Field(
        default_factory=list,
        description="Strategic suggestions for route efficiency (3-5 points)"
    )
    overstocked_items: List[str] = Field(
        default_factory=list,
        description="Items with consistent overselling (3-5 items with details)"
    )
    understocked_items: List[str] = Field(
        default_factory=list,
        description="Items with consistent underselling (3-5 items with details)"
    )
    coaching_areas: List[str] = Field(
        default_factory=list,
        description="Training needs identified (3-4 points)"
    )
    best_practices: List[str] = Field(
        default_factory=list,
        description="Successful strategies to replicate (3-4 points)"
    )

    class Config:
        extra = "ignore"  # Ignore extra fields from analysis
        json_schema_extra = {
            "example": {
                "route_code": "R001",
                "route_summary": "Route R001 completed 10 of 15 visits with 72.3% overall score...",
                "high_performers": ["C005 - XYZ Mart (92.5%) - Excellent execution across categories"],
                "route_strengths": ["Dairy category strong across route (87% avg)"]
            }
        }