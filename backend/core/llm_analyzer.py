import os
import yaml
import json
import pandas as pd
from typing import Dict, Any, List
from groq import Groq
import logging
from pathlib import Path
from pydantic import ValidationError
from backend.models.data_models import CustomerAnalysisResponse, RouteAnalysisResponse

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """Advanced analysis service for sales supervision"""

    def __init__(self, api_key: str = None):
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = None
        self.is_available = False

        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                self.is_available = True
            except Exception as e:
                logger.warning(f"Failed to initialize analytics client: {e}")
        else:
            logger.info("GROQ_API_KEY not set. Advanced analysis features will be disabled.")
        self.prompts_dir = Path(__file__).parent.parent / 'prompts'

        # Load prompt templates
        self.customer_prompt = self._load_prompt_template('customer_analysis.yaml')
        self.route_prompt = self._load_prompt_template('route_analysis.yaml')

    def _load_prompt_template(self, filename: str) -> Dict[str, str]:
        """Load prompt template from YAML file"""
        try:
            with open(self.prompts_dir / filename, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load prompt template {filename}: {e}")
            return {}

    def _format_historical_context(self, customer_data: pd.DataFrame) -> str:
        """Format historical context table - all columns except ActualQuantity and RecommendedQuantity"""
        if customer_data.empty:
            return "No historical data available for this customer"

        # Get first row for header info
        first_row = customer_data.iloc[0]
        header = f"TrxDate: {first_row.get('TrxDate', 'N/A')} | RouteCode: {first_row.get('RouteCode', 'N/A')} | CustomerCode: {first_row.get('CustomerCode', 'N/A')}"

        # Create table header
        table_lines = [header, ""]
        table_lines.append("ItemCode    | ItemName                           | Tier          | VanLoad | PriorityScore | AvgQtyPerVisit | DaysSinceLastPurchase | PurchaseCycleDays | FrequencyPercent")

        # Add each item as a row
        for _, row in customer_data.iterrows():
            line = f"{str(row['ItemCode'])[:11]:<11} | "
            line += f"{str(row['ItemName'])[:35]:<35} | "
            line += f"{str(row.get('Tier', 'N/A'))[:13]:<13} | "
            line += f"{str(row.get('VanLoad', 0))[:7]:<7} | "
            line += f"{row.get('PriorityScore', 0):.<13.1f} | "
            line += f"{str(row.get('AvgQuantityPerVisit', 0))[:14]:<14} | "
            line += f"{str(row.get('DaysSinceLastPurchase', 0))[:21]:<21} | "
            line += f"{str(row.get('PurchaseCycleDays', 0))[:17]:<17} | "
            line += f"{row.get('FrequencyPercent', 0):.1f}"
            table_lines.append(line)

        return '\n'.join(table_lines)

    def _format_current_visit_table(self, items_data: List[Dict[str, Any]]) -> str:
        """Format current visit performance as exact table from UI"""
        if not items_data:
            return "No sales data for this visit"

        # Create table header
        table_lines = []
        table_lines.append("Item Code | Item Name | Actual | Recommended")

        # Add each item as a row
        for item in items_data:
            item_code = str(item.get('itemCode', 'N/A'))
            item_name = str(item.get('itemName', 'Unknown'))
            actual = str(item.get('actualQuantity', 0))
            recommended = str(item.get('recommendedQuantity', 0))

            table_lines.append(f"{item_code} | {item_name} | {actual} | {recommended}")

        # Add totals
        total_actual = sum(item.get('actualQuantity', 0) for item in items_data)
        total_recommended = sum(item.get('recommendedQuantity', 0) for item in items_data)
        table_lines.append("")
        table_lines.append(f"TOTAL | {total_actual} | {total_recommended}")

        return '\n'.join(table_lines)

    def analyze_customer_performance(
        self,
        customer_code: str,
        route_code: str,
        date: str,
        customer_data: pd.DataFrame,
        current_items: List[Dict[str, Any]],
        performance_score: float,
        coverage: float = 0.0,
        accuracy: float = 0.0
    ) -> Dict[str, Any]:
        """Generate advanced analysis for customer performance - returns structured JSON"""
        if not self.is_available:
            return {
                "customer_code": customer_code,
                "performance_summary": "Advanced analysis is not available. Please configure API key.",
                "strengths": [],
                "weaknesses": [],
                "likely_reasons": [],
                "immediate_actions": [],
                "follow_up_actions": [],
                "identified_patterns": [],
                "red_flags": []
            }

        try:
            # Format historical context
            historical_context = self._format_historical_context(customer_data)

            # Format current visit table
            current_visit_table = self._format_current_visit_table(current_items)

            # Build the prompt from template
            prompt = self.customer_prompt.get('customer_analysis_template', '').format(
                customer_code=customer_code,
                route_code=route_code,
                date=date,
                historical_context=historical_context,
                current_visit_table=current_visit_table,
                performance_score=performance_score,
                coverage=coverage,
                accuracy=accuracy
            )

            # Make API call with deterministic settings and retry logic
            max_retries = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    completion = self.client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": self.customer_prompt.get('system_prompt', '')},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0,  # Maximum determinism
                        max_tokens=2000,
                        top_p=0.1,  # Very focused sampling
                        frequency_penalty=0.0,
                        presence_penalty=0.0,
                        seed=42 + attempt,  # Vary seed on retry
                        response_format={"type": "json_object"}
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    if "json_validate_failed" in error_str and attempt < max_retries - 1:
                        logger.warning(f"JSON validation failed on attempt {attempt + 1}, retrying with adjusted parameters...")
                        continue
                    else:
                        raise  # Re-raise if not JSON error or last attempt
            else:
                # All retries failed
                if last_error:
                    raise last_error

            # Parse JSON response
            response_text = completion.choices[0].message.content

            # Try to clean up common JSON issues
            try:
                analysis_json = json.loads(response_text)
            except json.JSONDecodeError:
                # Attempt to fix common issues
                logger.warning(f"Initial JSON parse failed, attempting cleanup")
                # Remove any markdown code blocks
                response_text = response_text.strip()
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                response_text = response_text.strip()
                analysis_json = json.loads(response_text)

            # Ensure customer_code is set
            analysis_json['customer_code'] = customer_code

            # Validate with Pydantic to ensure structure and prevent hallucinations
            try:
                validated_response = CustomerAnalysisResponse(**analysis_json)
                return validated_response.model_dump()
            except ValidationError as e:
                logger.error(f"Pydantic validation failed for customer analysis: {e}")
                logger.error(f"Analysis JSON that failed validation: {json.dumps(analysis_json, indent=2)}")

                # Try to salvage what we can - use the data but ensure all required fields exist
                safe_response = {
                    "customer_code": customer_code,
                    "performance_summary": analysis_json.get("performance_summary", "Analysis completed but validation had issues."),
                    "strengths": analysis_json.get("strengths", []) if isinstance(analysis_json.get("strengths"), list) else [],
                    "weaknesses": analysis_json.get("weaknesses", []) if isinstance(analysis_json.get("weaknesses"), list) else [],
                    "likely_reasons": analysis_json.get("likely_reasons", []) if isinstance(analysis_json.get("likely_reasons"), list) else [],
                    "immediate_actions": analysis_json.get("immediate_actions", []) if isinstance(analysis_json.get("immediate_actions"), list) else [],
                    "follow_up_actions": analysis_json.get("follow_up_actions", []) if isinstance(analysis_json.get("follow_up_actions"), list) else [],
                    "identified_patterns": analysis_json.get("identified_patterns", []) if isinstance(analysis_json.get("identified_patterns"), list) else [],
                    "red_flags": analysis_json.get("red_flags", []) if isinstance(analysis_json.get("red_flags"), list) else []
                }
                return safe_response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis JSON response after cleanup: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return {
                "customer_code": customer_code,
                "performance_summary": "Analysis generated but JSON parsing failed. The output was malformed. Please try again.",
                "strengths": [],
                "weaknesses": [],
                "likely_reasons": [],
                "immediate_actions": [],
                "follow_up_actions": [],
                "identified_patterns": [],
                "red_flags": []
            }
        except Exception as e:
            logger.error(f"Failed to generate customer analysis: {e}")
            return {
                "customer_code": customer_code,
                "performance_summary": f"Unable to generate analysis at this time. Error: {str(e)}",
                "strengths": [],
                "weaknesses": [],
                "likely_reasons": [],
                "immediate_actions": [],
                "follow_up_actions": [],
                "identified_patterns": [],
                "red_flags": []
            }

    def _format_route_pre_context(self, route_data: pd.DataFrame) -> str:
        """Format route planning context - all columns except quantities"""
        if route_data.empty:
            return "No planning data available for this route"

        # Group by customer to show planning overview
        customers = route_data['CustomerCode'].unique()
        context_lines = [f"Total customers planned: {len(customers)}"]
        context_lines.append(f"Total SKUs in portfolio: {route_data['ItemCode'].nunique()}")
        context_lines.append("")

        # Show sample of planning data (first few customers)
        context_lines.append("Planning overview (sample customers):")
        for customer in customers[:5]:  # Show first 5 customers as sample
            customer_items = route_data[route_data['CustomerCode'] == customer]
            context_lines.append(f"\nCustomer {customer}: {len(customer_items)} SKUs planned")

            # Group by tier
            tier_counts = customer_items['Tier'].value_counts()
            for tier, count in tier_counts.items():
                context_lines.append(f"  - {tier}: {count} items")

        if len(customers) > 5:
            context_lines.append(f"\n... and {len(customers) - 5} more customers")

        return '\n'.join(context_lines)

    def _format_route_actual_data(self, visited_customers: List[Dict[str, Any]]) -> str:
        """Format actual performance data from visited customers"""
        if not visited_customers:
            return "No customers visited"

        table_lines = []
        table_lines.append("Customer Code | Score | Items | Recommended | Actual | Key Issues")
        table_lines.append("-" * 80)

        for customer in visited_customers:
            customer_code = customer.get('customerCode', 'N/A')
            score = customer.get('score', 0)
            total_items = customer.get('totalItems', 0)
            total_rec = customer.get('totalRecommendedQty', 0)
            total_act = customer.get('totalActualQty', 0)

            # Identify key issues
            achievement = (total_act / max(total_rec, 1)) * 100
            if achievement > 120:
                issue = "Overselling"
            elif achievement < 75:
                issue = "Underselling"
            else:
                issue = "Balanced"

            table_lines.append(
                f"{customer_code:<13} | {score:>5.1f}% | {total_items:>5} | {total_rec:>11} | {total_act:>6} | {issue}"
            )

        return '\n'.join(table_lines)

    def analyze_route_performance(
        self,
        route_code: str,
        date: str,
        route_data: pd.DataFrame,  # Full recommended order for context
        visited_customers: List[Dict[str, Any]],  # Actual visited customer data
        coverage_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate advanced analysis for route performance - returns structured JSON"""
        if not self.is_available:
            return {
                "route_code": route_code,
                "route_summary": "Advanced analysis is not available. Please configure API key.",
                "high_performers": [],
                "needs_attention": [],
                "route_strengths": [],
                "route_weaknesses": [],
                "optimization_opportunities": [],
                "overstocked_items": [],
                "understocked_items": [],
                "coaching_areas": [],
                "best_practices": []
            }

        try:
            # Format pre-context (planning data without quantities)
            pre_context = self._format_route_pre_context(route_data)

            # Format actual data (visited customers performance)
            actual_data = self._format_route_actual_data(visited_customers)

            # Calculate totals
            total_actual = sum(c.get('totalActualQty', 0) for c in visited_customers)
            total_recommended = sum(c.get('totalRecommendedQty', 0) for c in visited_customers)

            # Build the prompt from template
            prompt = self.route_prompt.get('route_analysis_template', '').format(
                route_code=route_code,
                date=date,
                visited_customers=coverage_metrics.get('visitedCustomers', 0),
                total_customers=coverage_metrics.get('totalCustomers', 0),
                coverage_percentage=coverage_metrics.get('coveragePercentage', 0),
                total_actual=total_actual,
                total_recommended=total_recommended,
                pre_context=pre_context,
                actual_data=actual_data
            )

            # Make API call with deterministic settings and retry logic
            max_retries = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    completion = self.client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": self.route_prompt.get('system_prompt', '')},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0,  # Maximum determinism
                        max_tokens=3000,
                        top_p=0.1,  # Very focused sampling
                        frequency_penalty=0.0,
                        presence_penalty=0.0,
                        seed=42 + attempt,  # Vary seed on retry
                        response_format={"type": "json_object"}
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    if "json_validate_failed" in error_str and attempt < max_retries - 1:
                        logger.warning(f"Route JSON validation failed on attempt {attempt + 1}, retrying...")
                        continue
                    else:
                        raise  # Re-raise if not JSON error or last attempt
            else:
                # All retries failed
                if last_error:
                    raise last_error

            # Parse JSON response
            response_text = completion.choices[0].message.content

            # Try to clean up common JSON issues
            try:
                analysis_json = json.loads(response_text)
            except json.JSONDecodeError:
                # Attempt to fix common issues
                logger.warning(f"Initial route JSON parse failed, attempting cleanup")
                response_text = response_text.strip()
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                response_text = response_text.strip()
                analysis_json = json.loads(response_text)

            # Ensure route_code is set
            analysis_json['route_code'] = route_code

            # Validate with Pydantic to ensure structure and prevent hallucinations
            try:
                validated_response = RouteAnalysisResponse(**analysis_json)
                return validated_response.model_dump()
            except ValidationError as e:
                logger.error(f"Pydantic validation failed for route analysis: {e}")
                logger.error(f"Analysis JSON that failed validation: {json.dumps(analysis_json, indent=2)}")

                # Try to salvage what we can - use the data but ensure all required fields exist
                safe_response = {
                    "route_code": route_code,
                    "route_summary": analysis_json.get("route_summary", "Analysis completed but validation had issues."),
                    "high_performers": analysis_json.get("high_performers", []) if isinstance(analysis_json.get("high_performers"), list) else [],
                    "needs_attention": analysis_json.get("needs_attention", []) if isinstance(analysis_json.get("needs_attention"), list) else [],
                    "route_strengths": analysis_json.get("route_strengths", []) if isinstance(analysis_json.get("route_strengths"), list) else [],
                    "route_weaknesses": analysis_json.get("route_weaknesses", []) if isinstance(analysis_json.get("route_weaknesses"), list) else [],
                    "optimization_opportunities": analysis_json.get("optimization_opportunities", []) if isinstance(analysis_json.get("optimization_opportunities"), list) else [],
                    "overstocked_items": analysis_json.get("overstocked_items", []) if isinstance(analysis_json.get("overstocked_items"), list) else [],
                    "understocked_items": analysis_json.get("understocked_items", []) if isinstance(analysis_json.get("understocked_items"), list) else [],
                    "coaching_areas": analysis_json.get("coaching_areas", []) if isinstance(analysis_json.get("coaching_areas"), list) else [],
                    "best_practices": analysis_json.get("best_practices", []) if isinstance(analysis_json.get("best_practices"), list) else []
                }
                return safe_response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse route analysis JSON response after cleanup: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return {
                "route_code": route_code,
                "route_summary": "Analysis generated but JSON parsing failed. The output was malformed. Please try again.",
                "high_performers": [],
                "needs_attention": [],
                "route_strengths": [],
                "route_weaknesses": [],
                "optimization_opportunities": [],
                "overstocked_items": [],
                "understocked_items": [],
                "coaching_areas": [],
                "best_practices": []
            }
        except Exception as e:
            logger.error(f"Failed to generate route analysis: {e}")
            return {
                "route_code": route_code,
                "route_summary": f"Unable to generate route analysis. Error: {str(e)}",
                "high_performers": [],
                "needs_attention": [],
                "route_strengths": [],
                "route_weaknesses": [],
                "optimization_opportunities": [],
                "overstocked_items": [],
                "understocked_items": [],
                "coaching_areas": [],
                "best_practices": []
            }

    def health_check(self) -> Dict[str, Any]:
        """Check if the analysis service is working properly"""
        if not self.is_available:
            return {
                "status": "disabled",
                "message": "Analysis service is disabled. Set GROQ_API_KEY to enable.",
                "prompt_loaded": bool(self.customer_prompt)
            }

        try:
            _ = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": "Hello, are you working?"}
                ],
                max_tokens=50
            )

            return {
                "status": "healthy",
                "model": "llama-3.1-8b-instant",
                "prompt_loaded": bool(self.customer_prompt)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "prompt_loaded": bool(self.customer_prompt)
            }

# Create a global instance - always succeeds
analysis_engine = AnalysisEngine()

# Maintain backward compatibility
llm_analyzer = analysis_engine