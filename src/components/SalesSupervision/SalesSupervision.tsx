import React, { useState, useEffect } from 'react';
import { AlertCircle, Package, Users, TrendingUp, ShoppingCart, CheckCircle, AlertTriangle, ChevronDown, ChevronRight, Brain, Filter, Search, RotateCcw } from 'lucide-react';
import { PageHeader, LoadingState, EmptyState, SectionHeader, Toast } from '../common';
import MultiSelect from '../common/MultiSelect';
import {
  getSalesSupervisionFilterOptions,
  getSalesSupervisionData,
  getRecommendedOrderData,
  salesSupervisionAPI,
  apiClient
} from '../../services/api';

// Import types from centralized types file
import type {
  FilterOption,
  DemandItem,
  CustomerItem,
  Customer,
  EditingItemState,
  CustomerAnalysisResult,
  RouteAnalysisResult,
  SessionSummary,
  SalesData,
  RefreshMessage,
  ToastMessage
} from './types';

// Import utility helpers
import { apiCallWithTimeout } from './utils/helpers';

// Import sub-components
import DemandSection from './components/DemandSection';

const SalesSupervision: React.FC = () => {
  const [filterOptions, setFilterOptions] = useState<{ routes: FilterOption[]; dates: string[] }>({
    routes: [],
    dates: []
  });
  const [selectedRoutes, setSelectedRoutes] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [salesData, setSalesData] = useState<SalesData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{message: string; type: 'success' | 'error' | 'warning' | 'info'} | null>(null);
  const [generatingRecommendations, setGeneratingRecommendations] = useState(false);
  const [expandedCustomers, setExpandedCustomers] = useState<Set<number>>(new Set());
  const [visitedCustomers, setVisitedCustomers] = useState<Set<string>>(new Set());
  const [visitSequence, setVisitSequence] = useState<Map<string, number>>(new Map());
  const [dynamicSession, setDynamicSession] = useState<SessionSummary | null>(null);
  const [actualQuantities, setActualQuantities] = useState<{ [key: string]: { [key: string]: number } }>({});
  const [editingItem, setEditingItem] = useState<EditingItemState | null>(null);
  const [saving, setSaving] = useState(false);
  const [processingVisit, setProcessingVisit] = useState<string | null>(null);
  const [isHistoricalMode, setIsHistoricalMode] = useState(false);
  const [savedSessionId, setSavedSessionId] = useState<string | null>(null);
  const [adjustments, setAdjustments] = useState<{ [key: string]: { [key: string]: number } }>({});
  const [showScoreModal, setShowScoreModal] = useState(false);
  const [showActualModal, setShowActualModal] = useState(false);
  const [showRecommendedModal, setShowRecommendedModal] = useState(false);
  const [endOfDaySummary, setEndOfDaySummary] = useState<SessionSummary | null>(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<CustomerAnalysisResult | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState<string | null>(null);
  const [showRouteAnalysisModal, setShowRouteAnalysisModal] = useState(false);
  const [routeAnalysis, setRouteAnalysis] = useState<RouteAnalysisResult | null>(null);
  const [loadingRouteAnalysis, setLoadingRouteAnalysis] = useState(false);
  const [showScoringMethodologyModal, setShowScoringMethodologyModal] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [customerAnalyses, setCustomerAnalyses] = useState<{[key: string]: CustomerAnalysisResult}>({});
  const [lastLLMCallTime, setLastLLMCallTime] = useState<{[key: string]: number}>({});

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMessage(null);

    try {
      const result: any = await apiClient.post('/refresh-data');

      if (result.success) {
        setRefreshMessage({
          type: 'success',
          text: 'Data refreshed successfully!'
        });
        setTimeout(() => setRefreshMessage(null), 5000);
      } else {
        setRefreshMessage({
          type: 'error',
          text: result.message || 'Failed to refresh data'
        });
      }
    } catch (error) {
      setRefreshMessage({
        type: 'error',
        text: 'Error connecting to server'
      });
    } finally {
      setRefreshing(false);
    }
  };

  const loadFilterOptions = async () => {
    try {
      const options = await getSalesSupervisionFilterOptions() as unknown as { routes: FilterOption[]; dates: string[] };
      setFilterOptions(options);
      // Don't set any default selections
    } catch (err) {
      console.error('Failed to load filter options:', err);
      setError('Failed to load filter options');
    }
  };

  const handleApplyFilters = async () => {
    const selectedRoute = selectedRoutes.length > 0 ? selectedRoutes[0] : '';

    if (!selectedRoute || !selectedDate) {
      setError('Please select both route and date');
      return;
    }

    setLoading(true);
    setError(null);
    if (!generatingRecommendations) {
      setToast(null);
    }

    // Reset all state
    setExpandedCustomers(new Set());
    setVisitedCustomers(new Set());
    setVisitSequence(new Map());
    setActualQuantities({});
    setAdjustments({});
    setIsHistoricalMode(false);
    setSavedSessionId(null);
    setDynamicSession(null);
    setCustomerAnalyses({});
    setRouteAnalysis(null);
    setLastLLMCallTime({});

    try {
      // STEP 1: Check if saved supervision session exists for this route+date
      const savedSession = await salesSupervisionAPI.loadSupervisionState(selectedRoute, selectedDate);

      // Load sales data (always needed for recommended order display)
      const data = await getSalesSupervisionData({
        route_code: selectedRoute,
        date: selectedDate
      }) as unknown as SalesData;
      setSalesData(data);

      // STEP 2: Determine mode based on saved session existence
      if (savedSession.exists && savedSession.mode === 'historical') {
        // HISTORICAL MODE - Load saved data and enable read-only
        setIsHistoricalMode(true);
        setSavedSessionId(savedSession.session_id);

        // Populate visited customers (read-only)
        const visitedSet = new Set<string>(savedSession.visited_customers);
        setVisitedCustomers(visitedSet);

        // Populate visit sequences (read-only)
        const sequenceMap = new Map<string, number>(
          Object.entries(savedSession.visit_sequences)
        );
        setVisitSequence(sequenceMap);

        // Populate actual quantities (read-only)
        setActualQuantities(savedSession.actual_quantities);

        // Populate adjustments (read-only)
        setAdjustments(savedSession.adjustments);

        // Set route analysis if available
        if (savedSession.route_analysis) {
          setRouteAnalysis({
            route_code: selectedRoute,
            date: selectedDate,
            route_summary: savedSession.route_analysis,
            high_performers: [],
            needs_attention: [],
            route_strengths: [],
            route_weaknesses: [],
            optimization_opportunities: [],
            overstocked_items: [],
            understocked_items: [],
            coaching_areas: [],
            best_practices: [],
            metrics: savedSession.session_summary
          });
        }

        // Set endOfDaySummary from saved session_summary for metrics display
        if (savedSession.session_summary) {
          const summary = savedSession.session_summary;
          setEndOfDaySummary({
            route_code: summary.route_code || selectedRoute,
            date: summary.date || selectedDate,
            session_id: savedSession.session_id || '',
            visited_customers: summary.total_customers_visited || visitedSet.size,
            total_customers: summary.total_customers_planned || data.recommendedOrderSection.totalCustomers,
            performance_rate: summary.qty_fulfillment_rate || 0,
            redistribution_count: summary.redistribution_count || 0,
            total_actual: summary.total_qty_actual || 0,
            total_recommended: summary.total_qty_recommended || 0,
            visited_recommended: summary.total_qty_recommended || 0, // Use total for visited in historical
            remaining_customers: (summary.total_customers_planned || 0) - (summary.total_customers_visited || 0)
          });
        }

        // Restore customer analyses if available
        if (savedSession.customer_analyses) {
          const parsedAnalyses: {[key: string]: CustomerAnalysisResult} = {};
          for (const [customerCode, analysisData] of Object.entries(savedSession.customer_analyses)) {
            try {
              if (typeof analysisData === 'string') {
                parsedAnalyses[customerCode] = JSON.parse(analysisData);
              } else {
                parsedAnalyses[customerCode] = analysisData as CustomerAnalysisResult;
              }
            } catch (e) {
              // Fallback: treat as plain text summary
              parsedAnalyses[customerCode] = {
                customer_code: customerCode,
                performance_summary: String(analysisData),
                strengths: [],
                weaknesses: [],
                likely_reasons: [],
                immediate_actions: [],
                follow_up_actions: [],
                identified_patterns: [],
                red_flags: [],
                performance_score: 0,
                total_items: 0,
                total_recommended: 0,
                total_actual: 0
              };
            }
          }
          setCustomerAnalyses(parsedAnalyses);
        }

        setToast({ message: `📋 Loaded saved session from ${selectedDate} (Read-Only Mode)`, type: 'info' });

      } else {
        // LIVE MODE - Enable real-time supervision
        setIsHistoricalMode(false);

        // Initialize dynamic supervision session if recommendations exist
        if (data.recommendedOrderSection.hasData) {
          try {
            const sessionResult = await apiCallWithTimeout(
              salesSupervisionAPI.initializeDynamicSession(selectedRoute, selectedDate),
              30000
            );
            setDynamicSession(sessionResult.session);
          } catch (err: any) {
            console.error('Failed to initialize dynamic session:', err);
            const errorMsg = err.message === 'Request timeout'
              ? 'Session initialization timed out. Real-time redistribution unavailable.'
              : 'Warning: Real-time redistribution unavailable. You can still supervise manually.';
            setError(errorMsg);
            setToast({ message: errorMsg, type: 'warning' });
          }
        }
      }
    } catch (err) {
      console.error('Failed to load sales data:', err);
      setError('Failed to load sales data');
      setSalesData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRecommendations = async () => {
    if (!selectedDate) return;

    setGeneratingRecommendations(true);
    setError(null);
    setToast(null);

    try {
      // Use unified endpoint - fetches from DB or auto-generates if missing
      // Backend generates for ALL routes if data doesn't exist
      const result = await getRecommendedOrderData({
        routeCodes: ['All'],
        customerCodes: ['All'],
        itemCodes: ['All'],
        date: selectedDate
      });

      // Show success message based on data source
      if (result.status === 'generated') {
        setToast({ message: `Successfully generated ${result.chart_data?.length || 0} recommendations for ${selectedDate}`, type: 'success' });
      } else {
        setToast({ message: `Loaded ${result.chart_data?.length || 0} recommendations from database for ${selectedDate}`, type: 'success' });
      }

      // Reload sales supervision data to show the new recommendations
      if (selectedRoutes.length > 0 && selectedDate) {
        await handleApplyFilters();
      }
    } catch (err) {
      console.error('Failed to get recommendations:', err);
      setError('Failed to get recommendations. Please try again.');
    } finally {
      setGeneratingRecommendations(false);
    }
  };

  const getScoreColor = (score: number) => {
    // Performance-based coloring (actual vs recommended)
    if (score >= 90) return 'text-green-600 bg-green-50 border-green-200';  // Excellent: 90-100%
    if (score >= 75) return 'text-blue-600 bg-blue-50 border-blue-200';    // Good: 75-89%
    if (score >= 50) return 'text-yellow-600 bg-yellow-50 border-yellow-200'; // Average: 50-74%
    return 'text-red-600 bg-red-50 border-red-200';  // Poor: <50%
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <CheckCircle className="w-4 h-4" />;
    if (score >= 75) return <CheckCircle className="w-4 h-4" />;
    if (score >= 50) return <AlertTriangle className="w-4 h-4" />;
    return <AlertCircle className="w-4 h-4" />;
  };

  const getPerformanceLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 75) return 'Good';
    if (score >= 50) return 'Average';
    return 'Poor';
  };

  // Backend handles all scoring calculations

  const toggleCustomerExpanded = (index: number) => {
    const newExpanded = new Set(expandedCustomers);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedCustomers(newExpanded);
  };

  const toggleCustomerVisited = async (customerCode: string) => {
    // Block in historical mode (read-only)
    if (isHistoricalMode) {
      return; // Silently ignore - button will be disabled anyway
    }

    // Prevent rapid clicks while processing
    if (processingVisit !== null) {
      return;
    }

    const isCurrentlyVisited = visitedCustomers.has(customerCode);

    if (isCurrentlyVisited) {
      // Allow un-visiting (just for UI, doesn't affect backend session)
      const newVisited = new Set(visitedCustomers);
      newVisited.delete(customerCode);
      setVisitedCustomers(newVisited);

      // Remove visit sequence
      const newSequence = new Map(visitSequence);
      newSequence.delete(customerCode);
      setVisitSequence(newSequence);
    } else {
      // Mark as visited and assign sequence number
      const newVisited = new Set(visitedCustomers);
      newVisited.add(customerCode);
      setVisitedCustomers(newVisited);

      // Assign visit sequence (next available number)
      const newSequence = new Map(visitSequence);
      const nextSequence = Math.max(0, ...Array.from(newSequence.values())) + 1;
      newSequence.set(customerCode, nextSequence);
      setVisitSequence(newSequence);

      // If dynamic session is active, process the visit
      const selectedRoute = selectedRoutes.length > 0 ? selectedRoutes[0] : '';
      if (dynamicSession && selectedRoute && selectedDate) {
        setProcessingVisit(customerCode);
        try {
          // Get actual sales for this customer
          const customerData = salesData?.recommendedOrderSection.customers.find(c => c.customerCode === customerCode);
          if (customerData) {
            // Build actual sales object from customer's actual quantities
            const actualSales: Record<string, number> = {};
            customerData.items.forEach(item => {
              // Use manually edited quantities if available, otherwise use actualQuantity from data
              const manualQty = actualQuantities[customerCode]?.[item.itemCode];
              actualSales[item.itemCode] = manualQty !== undefined ? manualQty : (item.actualQuantity || 0);
            });


            // Process visit in backend
            const visitResult = await salesSupervisionAPI.processCustomerVisit(
              selectedRoute,
              selectedDate,
              customerCode,
              actualSales
            );


            // Update adjustments state with redistribution results
            if (visitResult.adjustments) {
              setAdjustments(visitResult.adjustments);

              // Show redistribution message
              if (visitResult.redistribution && visitResult.redistribution.redistributed_count > 0) {
                setToast({ message: `Redistributed ${visitResult.redistribution.redistributed_count} items to remaining customers`, type: 'success' });
              }
            }
          }
        } catch (err) {
          console.error('Failed to process visit:', err);
          // Continue without redistribution on error
        } finally {
          setProcessingVisit(null);
        }
      }
    }
  };
  
  const updateActualQuantity = (customerCode: string, itemCode: string, quantity: number) => {
    // Validate quantity
    let validatedQty = quantity;

    if (isNaN(validatedQty) || validatedQty < 0) {
      validatedQty = 0;
    }

    if (validatedQty > 999999) {
      setError('Quantity cannot exceed 999,999');
      setTimeout(() => setError(null), 3000);
      return;
    }

    setActualQuantities(prev => ({
      ...prev,
      [customerCode]: {
        ...prev[customerCode],
        [itemCode]: validatedQty
      }
    }));
  };
  
  const handleItemQuantityEdit = (customerCode: string, itemCode: string, value: string) => {
    setEditingItem({ customerCode, itemCode, value });
  };
  
  const saveItemQuantity = (customerCode: string, itemCode: string) => {
    if (editingItem && editingItem.customerCode === customerCode && editingItem.itemCode === itemCode) {
      let quantity = parseInt(editingItem.value);

      // Validate input
      if (isNaN(quantity)) {
        quantity = 0;
      }

      updateActualQuantity(customerCode, itemCode, quantity);
    }
    setEditingItem(null);
  };
  
  const cancelItemQuantityEdit = () => {
    setEditingItem(null);
  };
  
  
  
  const getAllVisitedCustomers = () => {
    if (!salesData) return { customers: [], totalActual: 0, totalRecommended: 0, overallScore: 0 };

    const visitedCustomersList = salesData.recommendedOrderSection.customers.filter(customer =>
      visitedCustomers.has(customer.customerCode)
    );

    // Calculate totals using real actual quantities (including manual edits)
    let totalActual = 0;
    let totalRecommended = 0;

    visitedCustomersList.forEach(customer => {
      const actualQtys = actualQuantities[customer.customerCode] || {};
      customer.items.forEach(item => {
        const actual = actualQtys[item.itemCode] !== undefined ? actualQtys[item.itemCode] : item.actualQuantity;
        totalActual += actual;
        totalRecommended += item.recommendedQuantity;
      });
    });

    // Calculate average score of visited customers only
    const overallScore = visitedCustomersList.length > 0
      ? visitedCustomersList.reduce((sum, customer) => sum + customer.score, 0) / visitedCustomersList.length
      : 0;

    return { customers: visitedCustomersList, totalActual, totalRecommended, overallScore };
  };

  const getRouteOverallScore = () => {
    if (!salesData) return 0;

    // Calculate average score of ALL customers in the route (visited and non-visited)
    const allCustomers = salesData.recommendedOrderSection.customers;
    if (allCustomers.length === 0) return 0;

    const totalScore = allCustomers.reduce((sum, customer) => sum + customer.score, 0);
    return totalScore / allCustomers.length;
  };

  const getActualItemsSummary = () => {
    const { customers } = getAllVisitedCustomers();
    const itemsSummary: { [key: string]: { itemName: string; actualQuantity: number } } = {};
    
    customers.forEach(customer => {
      customer.items.forEach(item => {
        if (!itemsSummary[item.itemCode]) {
          itemsSummary[item.itemCode] = {
            itemName: item.itemName,
            actualQuantity: 0
          };
        }
        itemsSummary[item.itemCode].actualQuantity += item.actualQuantity;
      });
    });
    
    return Object.entries(itemsSummary).map(([itemCode, data]) => ({
      itemCode,
      itemName: data.itemName,
      actualQuantity: data.actualQuantity
    }));
  };
  
  const getRecommendedItemsSummary = () => {
    const { customers } = getAllVisitedCustomers();
    const itemsSummary: { [key: string]: { itemName: string; recommendedQuantity: number } } = {};

    customers.forEach(customer => {
      customer.items.forEach(item => {
        if (!itemsSummary[item.itemCode]) {
          itemsSummary[item.itemCode] = {
            itemName: item.itemName,
            recommendedQuantity: 0
          };
        }
        itemsSummary[item.itemCode].recommendedQuantity += item.recommendedQuantity;
      });
    });

    return Object.entries(itemsSummary).map(([itemCode, data]) => ({
      itemCode,
      itemName: data.itemName,
      recommendedQuantity: data.recommendedQuantity
    }));
  };


  const handleCustomerAnalysis = async (customerCode: string) => {
    const selectedRoute = selectedRoutes.length > 0 ? selectedRoutes[0] : '';
    if (!selectedRoute || !selectedDate) {
      setError('Missing route or date information');
      return;
    }

    // If already analyzed (in state or historical), show existing
    if (customerAnalyses[customerCode]) {
      setCurrentAnalysis(customerAnalyses[customerCode]);
      setShowAnalysisModal(true);
      return;
    }

    // Block new generation in historical mode
    if (isHistoricalMode) {
      setError('Customer analysis not available for this saved session');
      setTimeout(() => setError(null), 3000);
      return;
    }

    // Rate limiting: 5 seconds cooldown per customer
    const now = Date.now();
    const lastTime = lastLLMCallTime[`customer_${customerCode}`] || 0;
    const COOLDOWN_MS = 5000;

    if (now - lastTime < COOLDOWN_MS) {
      const remainingSeconds = Math.ceil((COOLDOWN_MS - (now - lastTime)) / 1000);
      setError(`Please wait ${remainingSeconds}s before requesting another analysis`);
      setTimeout(() => setError(null), 2000);
      return;
    }

    setLoadingAnalysis(customerCode);
    setLastLLMCallTime(prev => ({ ...prev, [`customer_${customerCode}`]: now }));

    try {
      // Get current actual quantities (including frontend edits)
      const actualQtys = actualQuantities[customerCode] || {};

      // Find the customer data to get all items
      const customer = salesData?.recommendedOrderSection.customers.find(c => c.customerCode === customerCode);
      if (!customer) {
        setError('Customer data not found');
        return;
      }

      // Build complete actual quantities map (use actualQtys if available, else use item.actualQuantity)
      const completeActualQtys: { [key: string]: number } = {};
      customer.items.forEach(item => {
        completeActualQtys[item.itemCode] = actualQtys[item.itemCode] !== undefined
          ? actualQtys[item.itemCode]
          : item.actualQuantity;
      });

      // Call backend API with timeout
      const result = await apiCallWithTimeout(
        salesSupervisionAPI.analyzeCustomerPerformanceWithUpdates(
          selectedRoute,
          selectedDate,
          customerCode,
          completeActualQtys
        ),
        60000
      );

      // Calculate SKUs sold from frontend data if not returned from backend
      if (result.skus_sold === undefined || result.skus_sold === null) {
        result.skus_sold = Object.values(completeActualQtys).filter(qty => qty > 0).length;
      }

      // Save to state for later use
      setCustomerAnalyses(prev => ({
        ...prev,
        [customerCode]: result
      }));

      setCurrentAnalysis(result);
      setShowAnalysisModal(true);
    } catch (err: any) {
      console.error('Failed to generate customer analysis:', err);
      const errorMsg = err.message === 'Request timeout'
        ? 'Customer analysis timed out. Please try again.'
        : 'Failed to generate AI analysis. Please try again.';
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoadingAnalysis(null);
    }
  };

  const handleRouteAnalysis = async () => {
    const selectedRoute = selectedRoutes.length > 0 ? selectedRoutes[0] : '';
    if (!selectedRoute || !selectedDate || !salesData) {
      setError('Missing route, date, or sales data information');
      return;
    }

    // If in historical mode and analysis exists, just show it
    if (isHistoricalMode) {
      if (routeAnalysis) {
        setShowRouteAnalysisModal(true);
      } else {
        setError('Route analysis not available for this saved session');
        setTimeout(() => setError(null), 3000);
      }
      return;
    }

    // If already analyzed in current session, show existing
    if (routeAnalysis) {
      setShowRouteAnalysisModal(true);
      return;
    }

    // Rate limiting: 10 seconds cooldown for route analysis
    const now = Date.now();
    const lastTime = lastLLMCallTime['route_analysis'] || 0;
    const COOLDOWN_MS = 10000;

    if (now - lastTime < COOLDOWN_MS) {
      const remainingSeconds = Math.ceil((COOLDOWN_MS - (now - lastTime)) / 1000);
      setError(`Please wait ${remainingSeconds}s before requesting route analysis`);
      setTimeout(() => setError(null), 2000);
      return;
    }

    setLoadingRouteAnalysis(true);
    setLastLLMCallTime(prev => ({ ...prev, 'route_analysis': now }));

    try {
      // First fetch the session summary to get consistent metrics
      if (!endOfDaySummary) {
        const summary = await apiCallWithTimeout(
          salesSupervisionAPI.getDynamicSessionSummary(selectedRoute, selectedDate),
          30000
        );
        setEndOfDaySummary(summary);
      }

      // Build real context with visited customers and their actual data
      const allCustomers = salesData.recommendedOrderSection.customers;
      const visitedCustomersList = allCustomers.filter(customer =>
        visitedCustomers.has(customer.customerCode)
      );

      // Get all actual quantities including frontend edits for visited customers
      const visitedCustomersData = visitedCustomersList.map(customer => {
        const actualQtys = actualQuantities[customer.customerCode] || {};
        return {
          customerCode: customer.customerCode,
          customerName: customer.customerName,
          score: customer.score,
          items: customer.items.map(item => ({
            itemCode: item.itemCode,
            itemName: item.itemName,
            recommendedQuantity: item.recommendedQuantity,
            actualQuantity: actualQtys[item.itemCode] !== undefined ? actualQtys[item.itemCode] : item.actualQuantity,
            tier: item.tier
          }))
        };
      });

      // Call backend API with timeout
      const result = await apiCallWithTimeout(
        salesSupervisionAPI.analyzeRoutePerformanceWithVisitedData(
          selectedRoute,
          selectedDate,
          allCustomers, // Complete recommended order
          visitedCustomersData // Real visited customers with actual quantities
        ),
        60000
      );

      setRouteAnalysis(result);
      setShowRouteAnalysisModal(true);
    } catch (err: any) {
      console.error('Failed to generate route analysis:', err);
      const errorMsg = err.message === 'Request timeout'
        ? 'Route analysis timed out. Please try again.'
        : 'Failed to generate route AI analysis. Please try again.';
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoadingRouteAnalysis(false);
    }
  };

  const handleSaveSupervisionState = async () => {
    const selectedRoute = selectedRoutes.length > 0 ? selectedRoutes[0] : '';
    if (!selectedRoute || !selectedDate || !salesData) {
      setError('Missing route, date, or sales data information');
      return;
    }

    if (visitedCustomers.size === 0) {
      setError('No visited customers to save');
      return;
    }

    setSaving(true);
    setError(null);
    setToast(null);

    try {
      // Build visited customers array with visit sequence and customer analyses
      const visitedCustomersArray = Array.from(visitedCustomers).map(customerCode => {
        const analysis = customerAnalyses[customerCode];
        return {
          customer_code: customerCode,
          visit_sequence: visitSequence.get(customerCode) || 0,
          llm_analysis: analysis ? JSON.stringify(analysis) : '' // Save as JSON string
        };
      });

      // Get route-level LLM analysis if available
      const routeLLMAnalysis = routeAnalysis?.route_summary || '';

      // Prepare the payload
      const payload = {
        route_code: selectedRoute,
        date: selectedDate,
        visited_customers: visitedCustomersArray,
        actual_quantities: actualQuantities,
        adjustments: adjustments,
        route_llm_analysis: routeLLMAnalysis
      };

      // Call the save API
      const result = await salesSupervisionAPI.saveSupervisionState(payload);

      if (result.success) {
        setToast({ message: `Session saved successfully! ${result.customers_saved} customers and ${result.items_saved} items saved.`, type: 'success' });
      } else {
        setError(result.message || 'Failed to save supervision state');
      }
    } catch (err) {
      console.error('Failed to save supervision state:', err);
      setError('Failed to save supervision session. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="ui-page-container">
        <PageHeader
          title="Sales Supervision"
          subtitle="Monitor demand and recommended orders for route supervision"
          legend={{
            items: [
              { color: 'bg-cyan-600', label: 'Demand' },
              { color: 'bg-blue-600', label: 'Orders' }
            ]
          }}
          onRefresh={handleRefresh}
          refreshing={refreshing}
        />

        {refreshMessage && (
          <div className={`mb-4 p-4 rounded-md ${
            refreshMessage.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            <div className="flex items-center">
              {refreshMessage.type === 'success' ? (
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
              <span className="text-sm font-medium">{refreshMessage.text}</span>
            </div>
          </div>
        )}

        {/* Filters Section */}
        <div className="ui-card mb-5">
          <div className="flex items-center justify-between mb-4">
            <SectionHeader
              icon={<Filter className="text-cyan-600" />}
              title="Filters"
              subtitle="Select route and date to supervise"
            />
            {error && (
              <div className="text-xs text-red-600 bg-red-50 px-2.5 py-1.5 rounded-md border border-red-200">
                {error}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
            <div>
              <label className="ui-filter-label">
                Routes <span className="text-red-500">*</span>
              </label>
              <MultiSelect
                value={selectedRoutes}
                onChange={(value) => setSelectedRoutes(value)}
                options={[
                  { value: 'All', label: 'All Routes' },
                  ...filterOptions.routes.map(route => ({
                    value: route.code,
                    label: route.name
                  }))
                ]}
                placeholder="Select Route"
              />
            </div>

            <div>
              <label className="ui-filter-label">
                Date <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="ui-filter-input"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSelectedRoutes([]);
                setSelectedDate('');
                setSalesData(null);
                setError(null);
                setToast(null);
              }}
              className="ui-button-neutral text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              Clear
            </button>
            <button
              onClick={handleApplyFilters}
              disabled={loading || selectedRoutes.length === 0 || !selectedDate}
              className={`ui-button-primary text-xs ${selectedRoutes.length === 0 || !selectedDate ? 'disabled' : ''}`}
            >
              <Search className="w-3.5 h-3.5 mr-1.5" />
              {loading ? 'Loading...' : 'Apply'}
            </button>
          </div>
        </div>

        {loading && (
          <LoadingState
            title="Loading Sales Data"
            message="Fetching supervision data..."
            spinnerColor="border-t-cyan-600"
          />
        )}

        {/* Sales Data Sections */}
        {!loading && salesData && (
          <div className="ui-space-y">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="ui-card p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600">Unique Customers to Visit</p>
                    <p className="text-xl font-bold text-gray-900">{salesData.recommendedOrderSection.totalCustomers}</p>
                  </div>
                  <Users className="w-5 h-5 text-purple-500" />
                </div>
              </div>

              <div className="ui-card p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600">Unique Items Loaded</p>
                    <p className="text-xl font-bold text-gray-900">{salesData.demandSection.totalItems}</p>
                  </div>
                  <Package className="w-5 h-5 text-blue-500" />
                </div>
              </div>

              <div className="ui-card p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600">Total Allocated Quantity</p>
                    <p className="text-xl font-bold text-gray-900">{salesData.demandSection.totalAllocatedQty}</p>
                  </div>
                  <ShoppingCart className="w-5 h-5 text-green-500" />
                </div>
              </div>
            </div>
            
            {/* Visited Customers Summary - Show when all customers are visited */}
            {visitedCustomers.size === salesData.recommendedOrderSection.totalCustomers && visitedCustomers.size > 0 && (
              <div className="ui-card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Overall Performance Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="ui-card p-3 cursor-pointer hover:bg-gray-50 transition-colors" onClick={() => setShowScoreModal(true)}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-gray-600">Score</p>
                        <p className={`text-xl font-bold ${getScoreColor(getAllVisitedCustomers().overallScore).split(' ')[0]}`}>
                          {getAllVisitedCustomers().overallScore.toFixed(1)}%
                        </p>
                        <p className="text-[10px] text-gray-500">{getPerformanceLabel(getAllVisitedCustomers().overallScore)} • Click for details</p>
                      </div>
                      <TrendingUp className="w-5 h-5 text-orange-500" />
                    </div>
                  </div>
                  
                  <div className="ui-card p-3 cursor-pointer hover:bg-gray-50 transition-colors" onClick={() => setShowActualModal(true)}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-gray-600">Actual Quantity</p>
                        <p className="text-xl font-bold text-gray-900">{getAllVisitedCustomers().totalActual}</p>
                        <p className="text-[10px] text-gray-500">Click to view items</p>
                      </div>
                      <ShoppingCart className="w-5 h-5 text-green-500" />
                    </div>
                  </div>
                  
                  <div className="ui-card p-3 cursor-pointer hover:bg-gray-50 transition-colors" onClick={() => setShowRecommendedModal(true)}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-gray-600">Recommended Quantity</p>
                        <p className="text-xl font-bold text-gray-900">{getAllVisitedCustomers().totalRecommended}</p>
                        <p className="text-[10px] text-gray-500">Click to view items</p>
                      </div>
                      <Package className="w-5 h-5 text-blue-500" />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Demand Section */}
            <DemandSection items={salesData.demandSection.items} />

            {/* Recommended Order Section */}
            <div className="ui-card">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <ShoppingCart className="w-5 h-5 mr-2 text-green-600" />
                  Recommended Orders
                </h3>
                
                {!salesData.recommendedOrderSection.hasData && (
                  <button
                    onClick={handleGenerateRecommendations}
                    disabled={generatingRecommendations}
                    className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 text-xs"
                  >
                    {generatingRecommendations ? 'Generating...' : 'Generate Recommendations'}
                  </button>
                )}
              </div>

              {salesData.recommendedOrderSection.hasData ? (
                <div className="space-y-3">
                  {salesData.recommendedOrderSection.customers.map((customer, customerIndex) => {
                    const isExpanded = expandedCustomers.has(customerIndex);
                    const isVisited = visitedCustomers.has(customer.customerCode);

                    // Check if customer has actual sales (visited in reality)
                    const hasActualSales = customer.items.some(item => {
                      const actualQty = isVisited
                        ? (actualQuantities[customer.customerCode]?.[item.itemCode] || item.actualQuantity)
                        : (actualQuantities[customer.customerCode]?.[item.itemCode] || item.actualQuantity || 0);
                      return actualQty > 0;
                    });

                    return (
                      <div key={customerIndex} className="border border-gray-200 rounded-lg">
                        {/* Collapsible Header */}
                        <div className="p-3 bg-gray-50">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleCustomerExpanded(customerIndex)}
                                className="p-1 hover:bg-gray-200 rounded transition-colors"
                              >
                                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                              </button>
                              <div>
                                <h4 className="text-sm font-semibold text-gray-900">{customer.customerName}</h4>
                                <p className="text-xs text-gray-600 flex items-center gap-1">
                                  Code: {customer.customerCode}
                                  {hasActualSales && (
                                    <CheckCircle className="w-3.5 h-3.5 text-green-600" title="Customer has sales data (visited)" />
                                  )}
                                </p>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-3">
                              {/* Visited Toggle */}
                              <div className="flex items-center gap-2">
                                <label className="text-xs font-medium text-gray-700">Visited</label>
                                <button
                                  onClick={() => toggleCustomerVisited(customer.customerCode)}
                                  disabled={isHistoricalMode || processingVisit === customer.customerCode}
                                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors disabled:opacity-50 ${
                                    isVisited ? 'bg-green-600' : 'bg-gray-300'
                                  }`}
                                >
                                  {processingVisit === customer.customerCode ? (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                      <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    </div>
                                  ) : (
                                    <span
                                      className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                                        isVisited ? 'translate-x-4' : 'translate-x-1'
                                      }`}
                                    />
                                  )}
                                </button>
                              </div>
                              
                              {/* Performance Score Badge - Only show when visited */}
                              {isVisited && (
                                <div className="flex items-center gap-2">
                                  <div
                                    className={`flex flex-col gap-0.5 px-2 py-1 rounded-lg border text-xs cursor-pointer hover:opacity-80 transition-opacity ${getScoreColor(customer.score)}`}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setShowScoringMethodologyModal(true);
                                    }}
                                    title="Click to see scoring methodology"
                                  >
                                    <div className="flex items-center gap-1">
                                      {getScoreIcon(customer.score)}
                                      <span className="font-semibold">Score: {customer.score}%</span>
                                    </div>
                                    <div className="text-[9px] ml-4">
                                      Coverage: {customer.coverage}% | Accuracy: {customer.accuracy}%
                                    </div>
                                  </div>

                                  {/* AI Analysis Button */}
                                  <button
                                    onClick={() => handleCustomerAnalysis(customer.customerCode)}
                                    disabled={loadingAnalysis === customer.customerCode}
                                    className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-lg border border-purple-200 hover:bg-purple-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-xs"
                                    title="Get Customer Review"
                                  >
                                    {loadingAnalysis === customer.customerCode ? (
                                      <div className="w-3 h-3 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                                    ) : (
                                      <Brain className="w-3 h-3" />
                                    )}
                                    <span className="font-medium">Review</span>
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Summary Stats (Always Visible) */}
                          <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                            <div className="bg-white p-1 rounded border border-gray-200">
                              <span className="text-gray-600">Items:</span>
                              <span className="ml-1 font-semibold">{customer.totalItems}</span>
                            </div>
                            <div className="bg-white p-1 rounded border border-gray-200">
                              <span className="text-gray-600">Rec Qty:</span>
                              <span className="ml-1 font-semibold">
                                {customer.totalRecommendedQty}
                                {/* Show total adjustments for this customer */}
                                {!isVisited && adjustments[customer.customerCode] && (
                                  (() => {
                                    const totalAdjustment = Object.values(adjustments[customer.customerCode] || {}).reduce((sum, adj) => sum + adj, 0);
                                    return totalAdjustment > 0 ? (
                                      <span className="text-green-600 ml-1">
                                        (+{totalAdjustment})
                                      </span>
                                    ) : null;
                                  })()
                                )}
                              </span>
                            </div>
                            <div className="bg-white p-1 rounded border border-gray-200">
                              <span className="text-gray-600">Act Qty:</span>
                              <span className="ml-1 font-semibold">
                                {isVisited ? 
                                  (Object.values(actualQuantities[customer.customerCode] || {}).reduce((sum: number, qty) => sum + (qty as number), 0) || customer.totalActualQty) 
                                  : 0}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Expandable Content */}
                        {isExpanded && (
                          <div className="p-3 border-t">
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b border-gray-200">
                                    <th className="text-left py-1.5 px-2 font-medium text-gray-700">Item Code</th>
                                    <th className="text-left py-1.5 px-2 font-medium text-gray-700">Item Name</th>
                                    <th className="text-right py-1.5 px-2 font-medium text-gray-700">Actual</th>
                                    <th className="text-right py-1.5 px-2 font-medium text-gray-700">Recommended</th>
                                    {!isVisited && <th className="text-center py-1.5 px-2 font-medium text-gray-700 w-20">Edit</th>}
                                  </tr>
                                </thead>
                                <tbody>
                                  {customer.items.map((item, itemIndex) => {
                                    const actualQty = isVisited ? (actualQuantities[customer.customerCode]?.[item.itemCode] || item.actualQuantity) : (actualQuantities[customer.customerCode]?.[item.itemCode] || 0);
                                    const isEditing = editingItem?.customerCode === customer.customerCode && editingItem?.itemCode === item.itemCode;
                                    
                                    return (
                                      <tr key={itemIndex} className="border-b border-gray-100">
                                        <td className="py-1.5 px-2 text-gray-900">{item.itemCode}</td>
                                        <td className="py-1.5 px-2 text-gray-700">{item.itemName}</td>
                                        <td className="py-1.5 px-2 text-right text-gray-900">
                                          {isVisited || isHistoricalMode ? (
                                            actualQty
                                          ) : (
                                            isEditing ? (
                                              <div className="flex items-center justify-end gap-1">
                                                <input
                                                  type="number"
                                                  min="0"
                                                  value={editingItem.value}
                                                  onChange={(e) => setEditingItem({...editingItem, value: e.target.value})}
                                                  onBlur={() => saveItemQuantity(customer.customerCode, item.itemCode)}
                                                  onKeyDown={(e) => {
                                                    if (e.key === 'Enter') saveItemQuantity(customer.customerCode, item.itemCode);
                                                    if (e.key === 'Escape') cancelItemQuantityEdit();
                                                  }}
                                                  className="w-16 px-1 py-0.5 border border-blue-300 rounded text-xs text-right focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                  autoFocus
                                                />
                                              </div>
                                            ) : (
                                              <span
                                                className="cursor-pointer hover:bg-blue-50 px-1 py-0.5 rounded"
                                                onClick={() => handleItemQuantityEdit(customer.customerCode, item.itemCode, actualQty.toString())}
                                              >
                                                {actualQty}
                                              </span>
                                            )
                                          )}
                                        </td>
                                        <td className="py-1.5 px-2 text-right text-gray-900">
                                          <div className="flex items-center justify-end gap-1">
                                            <span className="font-semibold">{item.recommendedQuantity}</span>
                                            {/* Show adjustment if exists and customer not visited */}
                                            {!isVisited && adjustments[customer.customerCode]?.[item.itemCode] > 0 && (
                                              <span className="text-green-600 font-semibold">
                                                (+{adjustments[customer.customerCode][item.itemCode]})
                                              </span>
                                            )}
                                          </div>
                                        </td>
                                        {!isVisited && (
                                          <td className="py-1.5 px-2 text-center">
                                            {!isEditing && (
                                              <button
                                                onClick={() => handleItemQuantityEdit(customer.customerCode, item.itemCode, actualQty.toString())}
                                                className="text-blue-600 hover:text-blue-800 text-xs px-1 py-0.5 rounded hover:bg-blue-50"
                                              >
                                                Edit
                                              </button>
                                            )}
                                          </td>
                                        )}
                                      </tr>
                                    );
                                  })}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <ShoppingCart className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500 mb-2 text-sm">No recommended order data available for the selected date</p>
                  <p className="text-xs text-gray-400">Click "Generate Recommendations" to create recommendations for this date</p>
                </div>
              )}
            </div>

            {/* Route Summary and Save Buttons - Shows when at least 1 customer is visited */}
            {visitedCustomers.size > 0 && (dynamicSession || isHistoricalMode) && (
              <>
                <div className="mt-4 flex justify-center gap-3">
                  {/* Route Summary - Available in both modes */}
                  <button
                    onClick={handleRouteAnalysis}
                    disabled={loadingRouteAnalysis || (isHistoricalMode && !routeAnalysis)}
                    className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
                  >
                    {loadingRouteAnalysis ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <TrendingUp className="w-5 h-5" />
                    )}
                    {isHistoricalMode && routeAnalysis ? 'View Route Summary' : 'Route Summary'}
                    <span className="text-sm bg-white/20 px-2 py-0.5 rounded-full ml-2">
                      {visitedCustomers.size}/{salesData?.recommendedOrderSection.totalCustomers || 0} visited
                    </span>
                  </button>

                  {/* Save Button - Only in LIVE mode */}
                  {!isHistoricalMode && (
                    <button
                      onClick={handleSaveSupervisionState}
                      disabled={saving}
                      className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold rounded-lg shadow-lg hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
                    >
                      {saving ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <CheckCircle className="w-5 h-5" />
                      )}
                      Save Session
                    </button>
                  )}

                  {/* Historical Mode Badge */}
                  {isHistoricalMode && (
                    <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border-2 border-blue-200 rounded-lg">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm font-semibold text-blue-700">Saved Session (Read-Only)</span>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {!loading && !salesData && (
          <EmptyState
            title="No Data Loaded"
            message='Select a route and date, then click "Apply Filters" to view sales supervision data'
            icon={<Package className="h-5 w-5 text-gray-400" />}
          />
        )}
        
        {/* Overall Performance Summary - Show at bottom when all customers are visited */}
        {!loading && salesData && visitedCustomers.size === salesData.recommendedOrderSection.totalCustomers && visitedCustomers.size > 0 && (
          <div className="ui-card mt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-orange-600" />
              Overall Performance Summary
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="ui-card p-4 cursor-pointer hover:bg-gray-50 transition-colors border-2 hover:border-orange-200" onClick={() => setShowScoreModal(true)}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium">Overall Score</p>
                    <p className={`text-2xl font-bold ${getScoreColor(getAllVisitedCustomers().overallScore).split(' ')[0]}`}>
                      {getAllVisitedCustomers().overallScore.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500">{getPerformanceLabel(getAllVisitedCustomers().overallScore)} • Click for details</p>
                  </div>
                  <div className="text-right">
                    {getScoreIcon(getAllVisitedCustomers().overallScore)}
                    <p className="text-xs text-gray-400 mt-1">📊</p>
                  </div>
                </div>
              </div>
              
              <div className="ui-card p-4 cursor-pointer hover:bg-gray-50 transition-colors border-2 hover:border-green-200" onClick={() => setShowActualModal(true)}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium">Actual Quantity</p>
                    <p className="text-2xl font-bold text-gray-900">{getAllVisitedCustomers().totalActual}</p>
                    <p className="text-xs text-gray-500">Click to view items</p>
                  </div>
                  <div className="text-right">
                    <ShoppingCart className="w-6 h-6 text-green-500" />
                    <p className="text-xs text-gray-400 mt-1">📦</p>
                  </div>
                </div>
              </div>
              
              <div className="ui-card p-4 cursor-pointer hover:bg-gray-50 transition-colors border-2 hover:border-blue-200" onClick={() => setShowRecommendedModal(true)}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium">Recommended Quantity</p>
                    <p className="text-2xl font-bold text-gray-900">{getAllVisitedCustomers().totalRecommended}</p>
                    <p className="text-xs text-gray-500">Click to view items</p>
                  </div>
                  <div className="text-right">
                    <Package className="w-6 h-6 text-blue-500" />
                    <p className="text-xs text-gray-400 mt-1">📋</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Score Modal */}
        {showScoreModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Performance Score Details</h3>
                <button onClick={() => setShowScoreModal(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="space-y-3">
                <div className={`p-3 rounded-lg border ${getScoreColor(getAllVisitedCustomers().overallScore)}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {getScoreIcon(getAllVisitedCustomers().overallScore)}
                    <span className="font-semibold">Overall Score: {getAllVisitedCustomers().overallScore.toFixed(1)}%</span>
                  </div>
                  <p className="text-sm">Performance Level: {getPerformanceLabel(getAllVisitedCustomers().overallScore)}</p>
                </div>
                <div className="text-sm text-gray-600 space-y-2">
                  <h4 className="font-semibold text-gray-900">Scoring System:</h4>
                  <ul className="space-y-1">
                    <li>• <strong>Coverage (40%):</strong> Percentage of recommended items sold</li>
                    <li>• <strong>Accuracy (60%):</strong> Quantity precision (75-120% = Perfect)</li>
                    <li>• <strong>Perfect Zone:</strong> Selling 75-120% of recommended gets full accuracy</li>
                    <li>• <strong>Penalties:</strong> Linear penalties for under/over selling outside range</li>
                  </ul>
                </div>
                <div className="text-xs text-gray-500 mt-3">
                  <p><strong>Visited Customers:</strong> {visitedCustomers.size} of {salesData?.recommendedOrderSection.totalCustomers}</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Actual Quantity Modal */}
        {showActualModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Actual Quantities Sold</h3>
                <button onClick={() => setShowActualModal(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="mb-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="font-semibold text-green-800">Total Actual Quantity: {getAllVisitedCustomers().totalActual}</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 font-medium text-gray-700">Item Code</th>
                      <th className="text-left py-2 px-3 font-medium text-gray-700">Item Name</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-700">Actual Quantity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getActualItemsSummary().map((item, index) => (
                      <tr key={index} className="border-b border-gray-100">
                        <td className="py-2 px-3 text-gray-900">{item.itemCode}</td>
                        <td className="py-2 px-3 text-gray-700">{item.itemName}</td>
                        <td className="py-2 px-3 text-right font-semibold text-gray-900">{item.actualQuantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
        
        {/* Recommended Quantity Modal */}
        {showRecommendedModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Recommended Quantities</h3>
                <button onClick={() => setShowRecommendedModal(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="font-semibold text-blue-800">Total Recommended Quantity: {getAllVisitedCustomers().totalRecommended}</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 font-medium text-gray-700">Item Code</th>
                      <th className="text-left py-2 px-3 font-medium text-gray-700">Item Name</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-700">Recommended Quantity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getRecommendedItemsSummary().map((item, index) => (
                      <tr key={index} className="border-b border-gray-100">
                        <td className="py-2 px-3 text-gray-900">{item.itemCode}</td>
                        <td className="py-2 px-3 text-gray-700">{item.itemName}</td>
                        <td className="py-2 px-3 text-right font-semibold text-gray-900">{item.recommendedQuantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Customer AI Analysis Modal */}
        {showAnalysisModal && currentAnalysis && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900 flex items-center">
                  <Brain className="w-5 h-5 mr-2 text-purple-600" />
                  Customer Review
                </h3>
                <button onClick={() => setShowAnalysisModal(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Metrics Section */}
              <div className="mb-4 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3 pb-3 border-b border-purple-100">
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Customer</p>
                    <p className="text-lg font-bold text-gray-900">{currentAnalysis.customer_code}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Total SKUs</p>
                    <p className="text-lg font-bold text-gray-900">{currentAnalysis.total_items}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">SKUs Sold</p>
                    <p className="text-lg font-bold text-green-700">{currentAnalysis.skus_sold || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Coverage</p>
                    <p className="text-lg font-bold text-blue-700">{currentAnalysis.coverage || 0}%</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Units Sold</p>
                    <p className="text-lg font-bold text-blue-700">{currentAnalysis.total_actual}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Recommended</p>
                    <p className="text-lg font-bold text-purple-700">{currentAnalysis.total_recommended}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Accuracy</p>
                    <p className="text-lg font-bold text-orange-700">{currentAnalysis.accuracy || 0}%</p>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-purple-100 text-center">
                  <p className="text-xs text-gray-600 font-medium">Overall Score</p>
                  <p className={`text-2xl font-bold ${getScoreColor(currentAnalysis.performance_score).split(' ')[0]}`}>
                    {currentAnalysis.performance_score}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Coverage (40%) + Accuracy (60%)
                  </p>
                </div>
              </div>

              {/* AI Analysis Content - Structured Format */}
              <div className="space-y-4">
                {/* Performance Summary */}
                {currentAnalysis.performance_summary && (
                  <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                    <p className="text-sm text-gray-700 leading-relaxed">{currentAnalysis.performance_summary}</p>
                  </div>
                )}

                {/* Strengths */}
                {currentAnalysis.strengths && currentAnalysis.strengths.length > 0 && (
                  <div className="bg-green-50 rounded-lg border border-green-200 p-4">
                    <h4 className="text-sm font-bold text-green-800 mb-2 flex items-center">
                      <span className="mr-2">✓</span>Strengths
                    </h4>
                    <ul className="space-y-1">
                      {currentAnalysis.strengths.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Weaknesses */}
                {currentAnalysis.weaknesses && currentAnalysis.weaknesses.length > 0 && (
                  <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-4">
                    <h4 className="text-sm font-bold text-yellow-800 mb-2 flex items-center">
                      <span className="mr-2">⚠</span>Areas for Improvement
                    </h4>
                    <ul className="space-y-1">
                      {currentAnalysis.weaknesses.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-yellow-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Likely Reasons */}
                {currentAnalysis.likely_reasons && currentAnalysis.likely_reasons.length > 0 && (
                  <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
                    <h4 className="text-sm font-bold text-blue-800 mb-2 flex items-center">
                      <span className="mr-2">🔍</span>Root Cause Analysis
                    </h4>
                    <ul className="space-y-1">
                      {currentAnalysis.likely_reasons.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-blue-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Immediate Actions */}
                {currentAnalysis.immediate_actions && currentAnalysis.immediate_actions.length > 0 && (
                  <div className="bg-red-50 rounded-lg border border-red-200 p-4">
                    <h4 className="text-sm font-bold text-red-800 mb-2 flex items-center">
                      <span className="mr-2">🚨</span>Urgent Actions (Next 24 Hours)
                    </h4>
                    <ul className="space-y-1">
                      {currentAnalysis.immediate_actions.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-red-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Follow-up Actions */}
                {currentAnalysis.follow_up_actions && currentAnalysis.follow_up_actions.length > 0 && (
                  <div className="bg-purple-50 rounded-lg border border-purple-200 p-4">
                    <h4 className="text-sm font-bold text-purple-800 mb-2 flex items-center">
                      <span className="mr-2">📅</span>Follow-Up Actions (Next Visit/Week)
                    </h4>
                    <ul className="space-y-1">
                      {currentAnalysis.follow_up_actions.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-purple-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Historical Patterns */}
                {currentAnalysis.identified_patterns && currentAnalysis.identified_patterns.length > 0 && (
                  <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
                    <h4 className="text-sm font-bold text-blue-800 mb-2 flex items-center">
                      <span className="mr-2">📈</span>Historical Patterns Detected
                    </h4>
                    <ul className="space-y-1">
                      {currentAnalysis.identified_patterns.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-blue-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Red Flags */}
                {currentAnalysis.red_flags && currentAnalysis.red_flags.length > 0 && (
                  <div className="bg-red-50 rounded-lg border-2 border-red-300 p-4">
                    <h4 className="text-sm font-bold text-red-800 mb-2 flex items-center">
                      <span className="mr-2">🔴</span>Red Flags Requiring Attention
                    </h4>
                    <ul className="space-y-1">
                      {currentAnalysis.red_flags.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-red-600 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-4">
                <button
                  onClick={() => setShowAnalysisModal(false)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                >
                  Got it
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Route Summary Modal */}
        {showRouteAnalysisModal && routeAnalysis && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2 text-purple-600" />
                  Route Summary
                </h3>
                <button onClick={() => setShowRouteAnalysisModal(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Route Information */}
              <div className="mb-4 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Route</p>
                    <p className="text-lg font-bold text-gray-900">{selectedRoutes[0] || ''}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Date</p>
                    <p className="text-lg font-bold text-gray-900">{selectedDate}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Customers Visited</p>
                    <p className="text-lg font-bold text-blue-700">{visitedCustomers.size}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600 font-medium">Total Customers</p>
                    <p className="text-lg font-bold text-gray-900">{salesData?.recommendedOrderSection.customers.length || 0}</p>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-white border border-blue-200 rounded-lg p-3 text-center">
                  <Users className="w-5 h-5 text-blue-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-blue-700">
                    {salesData ? Math.round((visitedCustomers.size / salesData.recommendedOrderSection.customers.length) * 100) : 0}%
                  </p>
                  <p className="text-xs text-gray-600 font-medium">Coverage</p>
                </div>

                <div className="bg-white border border-green-200 rounded-lg p-3 text-center">
                  <TrendingUp className="w-5 h-5 text-green-600 mx-auto mb-2" />
                  <p className={`text-2xl font-bold ${
                    getRouteOverallScore() >= 75 ? 'text-green-700' :
                    getRouteOverallScore() >= 50 ? 'text-yellow-700' : 'text-red-700'
                  }`}>
                    {getRouteOverallScore().toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-600 font-medium">Score</p>
                </div>

                <div className="bg-white border border-purple-200 rounded-lg p-3 text-center">
                  <Package className="w-5 h-5 text-purple-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-purple-700">
                    {endOfDaySummary?.total_actual || getAllVisitedCustomers().totalActual}
                  </p>
                  <p className="text-xs text-gray-600 font-medium">Units Sold</p>
                </div>

                <div className="bg-white border border-orange-200 rounded-lg p-3 text-center">
                  <ShoppingCart className="w-5 h-5 text-orange-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-orange-700">{endOfDaySummary?.redistribution_count || 0}</p>
                  <p className="text-xs text-gray-600 font-medium">Redistributions</p>
                </div>
              </div>

              {/* Performance Breakdown */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">Performance Breakdown</h4>

                <div className="mb-3 p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-green-800">Visited Customers</p>
                    <span className="text-xs bg-green-100 px-2 py-0.5 rounded-full text-green-700">
                      {visitedCustomers.size} customers
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-white rounded-lg p-3 border border-green-100 text-center">
                      <p className="text-xs text-gray-600">Actual Sold</p>
                      <p className="text-lg font-bold text-green-700">{endOfDaySummary?.total_actual || getAllVisitedCustomers().totalActual}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-100 text-center">
                      <p className="text-xs text-gray-600">Target</p>
                      <p className="text-lg font-bold text-emerald-700">{endOfDaySummary?.visited_recommended || getAllVisitedCustomers().totalRecommended}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-100 text-center">
                      <p className="text-xs text-gray-600">Achievement</p>
                      <p className="text-lg font-bold text-green-800">
                        {endOfDaySummary && endOfDaySummary.visited_recommended > 0
                          ? ((endOfDaySummary.total_actual / endOfDaySummary.visited_recommended) * 100).toFixed(1)
                          : ((getAllVisitedCustomers().totalActual / Math.max(getAllVisitedCustomers().totalRecommended, 1)) * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-blue-800">Route Overall</p>
                    <span className="text-xs bg-blue-100 px-2 py-0.5 rounded-full text-blue-700">
                      {endOfDaySummary?.total_customers || salesData?.recommendedOrderSection.customers.length || 0} total
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white rounded-lg p-3 border border-blue-100 text-center">
                      <p className="text-xs text-gray-600">Total Plan</p>
                      <p className="text-lg font-bold text-blue-700">{endOfDaySummary?.total_recommended || 0}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-blue-100 text-center">
                      <p className="text-xs text-gray-600">Achievement</p>
                      <p className="text-lg font-bold text-indigo-700">
                        {endOfDaySummary && endOfDaySummary.total_recommended > 0
                          ? ((endOfDaySummary.total_actual / endOfDaySummary.total_recommended) * 100).toFixed(1)
                          : '0.0'}%
                      </p>
                      <p className="text-xs text-gray-500 mt-1">{endOfDaySummary?.total_actual || 0} units</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-gray-600 mb-2">
                  <span className="font-medium">Route Completion</span>
                  <span>{(salesData?.recommendedOrderSection.customers.length || 0) - visitedCustomers.size} customers remaining</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-indigo-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(visitedCustomers.size / (salesData?.recommendedOrderSection.customers.length || 1)) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* AI Analysis - Structured Format */}
              <div className="space-y-4">
                {/* Route Summary */}
                {routeAnalysis.route_summary && (
                  <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                    <p className="text-sm text-gray-700 leading-relaxed">{routeAnalysis.route_summary}</p>
                  </div>
                )}

                {/* High Performers */}
                {routeAnalysis.high_performers && routeAnalysis.high_performers.length > 0 && (
                  <div className="bg-green-50 rounded-lg border border-green-200 p-4">
                    <h4 className="text-sm font-bold text-green-800 mb-2">Top Performing Customers</h4>
                    <ul className="space-y-1">
                      {routeAnalysis.high_performers.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Needs Attention */}
                {routeAnalysis.needs_attention && routeAnalysis.needs_attention.length > 0 && (
                  <div className="bg-red-50 rounded-lg border border-red-200 p-4">
                    <h4 className="text-sm font-bold text-red-800 mb-2">Customers Requiring Immediate Attention</h4>
                    <ul className="space-y-1">
                      {routeAnalysis.needs_attention.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-red-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Route Strengths */}
                {routeAnalysis.route_strengths && routeAnalysis.route_strengths.length > 0 && (
                  <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
                    <h4 className="text-sm font-bold text-blue-800 mb-2">What's Working Well</h4>
                    <ul className="space-y-1">
                      {routeAnalysis.route_strengths.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-blue-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Route Weaknesses */}
                {routeAnalysis.route_weaknesses && routeAnalysis.route_weaknesses.length > 0 && (
                  <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-4">
                    <h4 className="text-sm font-bold text-yellow-800 mb-2">Areas Needing Improvement</h4>
                    <ul className="space-y-1">
                      {routeAnalysis.route_weaknesses.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-yellow-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Optimization Opportunities */}
                {routeAnalysis.optimization_opportunities && routeAnalysis.optimization_opportunities.length > 0 && (
                  <div className="bg-purple-50 rounded-lg border border-purple-200 p-4">
                    <h4 className="text-sm font-bold text-purple-800 mb-2">Route Optimization Opportunities</h4>
                    <ul className="space-y-1">
                      {routeAnalysis.optimization_opportunities.map((item: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-purple-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Inventory Insights */}
                {((routeAnalysis.overstocked_items && routeAnalysis.overstocked_items.length > 0) ||
                  (routeAnalysis.understocked_items && routeAnalysis.understocked_items.length > 0)) && (
                  <div className="bg-indigo-50 rounded-lg border border-indigo-200 p-4">
                    <h4 className="text-sm font-bold text-indigo-800 mb-3">Inventory Insights</h4>

                    {routeAnalysis.overstocked_items && routeAnalysis.overstocked_items.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-600 mb-1">Overstocked Items (Reduce Next Week):</p>
                        <ul className="space-y-1">
                          {routeAnalysis.overstocked_items.map((item: string, idx: number) => (
                            <li key={idx} className="text-sm text-gray-700 flex items-start">
                              <span className="inline-block w-1.5 h-1.5 bg-orange-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {routeAnalysis.understocked_items && routeAnalysis.understocked_items.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-1">Understocked Items (Increase Next Week):</p>
                        <ul className="space-y-1">
                          {routeAnalysis.understocked_items.map((item: string, idx: number) => (
                            <li key={idx} className="text-sm text-gray-700 flex items-start">
                              <span className="inline-block w-1.5 h-1.5 bg-cyan-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Team Performance Insights */}
                {((routeAnalysis.coaching_areas && routeAnalysis.coaching_areas.length > 0) ||
                  (routeAnalysis.best_practices && routeAnalysis.best_practices.length > 0)) && (
                  <div className="bg-teal-50 rounded-lg border border-teal-200 p-4">
                    <h4 className="text-sm font-bold text-teal-800 mb-3">Team Performance Insights</h4>

                    {routeAnalysis.coaching_areas && routeAnalysis.coaching_areas.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-600 mb-1">Training Needs:</p>
                        <ul className="space-y-1">
                          {routeAnalysis.coaching_areas.map((item: string, idx: number) => (
                            <li key={idx} className="text-sm text-gray-700 flex items-start">
                              <span className="inline-block w-1.5 h-1.5 bg-teal-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {routeAnalysis.best_practices && routeAnalysis.best_practices.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-1">Best Practices to Share:</p>
                        <ul className="space-y-1">
                          {routeAnalysis.best_practices.map((item: string, idx: number) => (
                            <li key={idx} className="text-sm text-gray-700 flex items-start">
                              <span className="inline-block w-1.5 h-1.5 bg-emerald-500 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-4">
                <button
                  onClick={() => setShowRouteAnalysisModal(false)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* FMCG Scoring Methodology Modal */}
        {showScoringMethodologyModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
                  Performance Scoring
                </h3>
                <button
                  onClick={() => setShowScoringMethodologyModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Overview */}
              <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  Two-component scoring system measuring item variety (Coverage) and quantity precision (Accuracy).
                </p>
              </div>

              {/* Scoring Formula */}
              <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h5 className="font-semibold text-gray-900 mb-2 text-sm">Scoring Formula</h5>
                <div className="text-center text-base font-mono bg-white p-3 rounded border border-gray-300">
                  Score = (Coverage × 40%) + (Accuracy × 60%)
                </div>
              </div>

              {/* Scoring Components */}
              <div className="space-y-3 mb-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                    <div>
                      <h5 className="font-semibold text-gray-900">Coverage</h5>
                      <p className="text-xs text-gray-600">Items sold / Total items recommended</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold text-blue-600">40%</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-orange-500 rounded-full mr-3"></div>
                    <div>
                      <h5 className="font-semibold text-gray-900">Accuracy</h5>
                      <p className="text-xs text-gray-600">Quantity precision (75-120% = Perfect)</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold text-orange-600">60%</span>
                </div>
              </div>

              {/* Accuracy Perfect Zone */}
              <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
                <h5 className="font-semibold text-green-900 mb-1 text-sm">Perfect Accuracy Zone</h5>
                <p className="text-xs text-green-800">75-120% of recommended quantity = 100% accuracy score</p>
                <p className="text-xs text-green-700 mt-1">Outside this range: Linear penalty applied</p>
              </div>

              {/* Performance Levels */}
              <div className="bg-gray-50 rounded-lg p-3 mb-4">
                <h5 className="font-semibold text-gray-900 mb-2 text-sm">Performance Levels</h5>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <span>90%+ Excellent</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                    <span>75%+ Good</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
                    <span>50%+ Average</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                    <span>Below 50% Poor</span>
                  </div>
                </div>
              </div>

              {/* Close Button */}
              <div className="flex justify-end">
                <button
                  onClick={() => setShowScoringMethodologyModal(false)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  Got it
                </button>
              </div>
            </div>
          </div>
        )}

        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
            duration={5000}
          />
        )}

      </div>
    </div>
  );
};

export default SalesSupervision;