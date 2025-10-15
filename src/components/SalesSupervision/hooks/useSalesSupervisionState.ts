/**
 * Custom hook for managing Sales Supervision state
 * Consolidates all state management in one place
 */

import { useState } from 'react';
import type {
  FilterOption,
  SalesData,
  ToastMessage,
  RefreshMessage,
  EditingItemState,
  SessionSummary,
  CustomerAnalysisResult,
  RouteAnalysisResult
} from '../types';

export const useSalesSupervisionState = () => {
  // Filter state
  const [filterOptions, setFilterOptions] = useState<{ routes: FilterOption[]; dates: string[] }>({
    routes: [],
    dates: []
  });
  const [selectedRoutes, setSelectedRoutes] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');

  // Data state
  const [salesData, setSalesData] = useState<SalesData | null>(null);

  // Loading & error state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [generatingRecommendations, setGeneratingRecommendations] = useState(false);
  const [saving, setSaving] = useState(false);
  const [processingVisit, setProcessingVisit] = useState<string | null>(null);

  // Toast & messages
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [refreshMessage, setRefreshMessage] = useState<RefreshMessage | null>(null);

  // UI state
  const [expandedCustomers, setExpandedCustomers] = useState<Set<number>>(new Set());
  const [showScoreModal, setShowScoreModal] = useState(false);
  const [showActualModal, setShowActualModal] = useState(false);
  const [showRecommendedModal, setShowRecommendedModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [showRouteAnalysisModal, setShowRouteAnalysisModal] = useState(false);
  const [showScoringMethodologyModal, setShowScoringMethodologyModal] = useState(false);

  // Visit tracking state
  const [visitedCustomers, setVisitedCustomers] = useState<Set<string>>(new Set());
  const [visitSequence, setVisitSequence] = useState<Map<string, number>>(new Map());

  // Session state
  const [dynamicSession, setDynamicSession] = useState<SessionSummary | null>(null);
  const [endOfDaySummary, setEndOfDaySummary] = useState<SessionSummary | null>(null);
  const [isHistoricalMode, setIsHistoricalMode] = useState(false);
  const [savedSessionId, setSavedSessionId] = useState<string | null>(null);

  // Editing state
  const [editingItem, setEditingItem] = useState<EditingItemState | null>(null);
  const [actualQuantities, setActualQuantities] = useState<{ [key: string]: { [key: string]: number } }>({});
  const [adjustments, setAdjustments] = useState<{ [key: string]: { [key: string]: number } }>({});

  // Analysis state
  const [currentAnalysis, setCurrentAnalysis] = useState<CustomerAnalysisResult | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState<string | null>(null);
  const [routeAnalysis, setRouteAnalysis] = useState<RouteAnalysisResult | null>(null);
  const [loadingRouteAnalysis, setLoadingRouteAnalysis] = useState(false);
  const [customerAnalyses, setCustomerAnalyses] = useState<{[key: string]: CustomerAnalysisResult}>({});
  const [lastLLMCallTime, setLastLLMCallTime] = useState<{[key: string]: number}>({});

  // Reset all state (used when applying new filters)
  const resetState = () => {
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
  };

  return {
    // Filter state
    filterOptions,
    setFilterOptions,
    selectedRoutes,
    setSelectedRoutes,
    selectedDate,
    setSelectedDate,

    // Data state
    salesData,
    setSalesData,

    // Loading & error state
    loading,
    setLoading,
    error,
    setError,
    refreshing,
    setRefreshing,
    generatingRecommendations,
    setGeneratingRecommendations,
    saving,
    setSaving,
    processingVisit,
    setProcessingVisit,

    // Toast & messages
    toast,
    setToast,
    refreshMessage,
    setRefreshMessage,

    // UI state
    expandedCustomers,
    setExpandedCustomers,
    showScoreModal,
    setShowScoreModal,
    showActualModal,
    setShowActualModal,
    showRecommendedModal,
    setShowRecommendedModal,
    showAnalysisModal,
    setShowAnalysisModal,
    showRouteAnalysisModal,
    setShowRouteAnalysisModal,
    showScoringMethodologyModal,
    setShowScoringMethodologyModal,

    // Visit tracking state
    visitedCustomers,
    setVisitedCustomers,
    visitSequence,
    setVisitSequence,

    // Session state
    dynamicSession,
    setDynamicSession,
    endOfDaySummary,
    setEndOfDaySummary,
    isHistoricalMode,
    setIsHistoricalMode,
    savedSessionId,
    setSavedSessionId,

    // Editing state
    editingItem,
    setEditingItem,
    actualQuantities,
    setActualQuantities,
    adjustments,
    setAdjustments,

    // Analysis state
    currentAnalysis,
    setCurrentAnalysis,
    loadingAnalysis,
    setLoadingAnalysis,
    routeAnalysis,
    setRouteAnalysis,
    loadingRouteAnalysis,
    setLoadingRouteAnalysis,
    customerAnalyses,
    setCustomerAnalyses,
    lastLLMCallTime,
    setLastLLMCallTime,

    // Utilities
    resetState
  };
};
