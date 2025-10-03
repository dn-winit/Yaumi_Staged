"""
API Routes Module
Clean and organized route definitions
"""

from .dashboard import router as dashboard
from .forecast import router as forecast
from .recommended_order import router as recommended_order
from .sales_supervision import router as sales_supervision

__all__ = [
    'dashboard',
    'forecast',
    'recommended_order',
    'sales_supervision'
]