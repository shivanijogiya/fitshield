/**
 * useMeals – encapsulates all meal-related state and API calls.
 *
 * Centralizing state here means:
 *  - The summary and meal list stay in sync after add/delete.
 *  - Components receive data and callbacks; they don't touch the API directly.
 *  - State updates are optimistic (or immediate after confirmation) so there
 *    is never a stale page reload.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  createMeal,
  deleteMeal,
  getDailySummary,
  getTrends,
  listMeals,
} from "../services/api";

const today = () => new Date().toISOString().slice(0, 10);

export function useMeals() {
  // ── Filters ----------------------------------------------------------------
  const [filters, setFilters] = useState({ date: today(), tag: "", search: "", page: 1 });

  // ── Meals list ──────────────────────────────────────────────────────────────
  const [meals, setMeals] = useState([]);
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });
  const [mealsLoading, setMealsLoading] = useState(false);
  const [mealsError, setMealsError] = useState(null);

  // ── Summary ─────────────────────────────────────────────────────────────────
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState(null);

  // ── Trends ──────────────────────────────────────────────────────────────────
  const [trends, setTrends] = useState(null);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [trendsError, setTrendsError] = useState(null);

  // ── Trend day click filter ──────────────────────────────────────────────────
  // When user clicks a bar, we filter the meal list to that day.
  const [trendDateFilter, setTrendDateFilter] = useState(null);

  // Abort controller to cancel stale requests
  const abortRef = useRef(null);

  // ---------------------------------------------------------------------------
  // Fetch meals list
  // ---------------------------------------------------------------------------
  const fetchMeals = useCallback(async (f = filters) => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setMealsLoading(true);
    setMealsError(null);
    try {
      const activeDate = trendDateFilter || f.date;
      const result = await listMeals({ ...f, date: activeDate });
      setMeals(result.results);
      setPagination({ count: result.count, next: result.next, previous: result.previous });
    } catch (err) {
      if (err.name !== "CanceledError") {
        setMealsError("Unable to load meals. Please try again.");
      }
    } finally {
      setMealsLoading(false);
    }
  }, [filters, trendDateFilter]);

  // ---------------------------------------------------------------------------
  // Fetch summary
  // ---------------------------------------------------------------------------
  const fetchSummary = useCallback(async (date = filters.date) => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const data = await getDailySummary(date || null);
      setSummary(data);
    } catch {
      setSummaryError("Unable to load summary.");
    } finally {
      setSummaryLoading(false);
    }
  }, [filters.date]);

  // ---------------------------------------------------------------------------
  // Fetch trends
  // ---------------------------------------------------------------------------
  const fetchTrends = useCallback(async () => {
    setTrendsLoading(true);
    setTrendsError(null);
    try {
      const data = await getTrends(7);
      setTrends(data);
    } catch {
      setTrendsError("Unable to load trends.");
    } finally {
      setTrendsLoading(false);
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Effects
  // ---------------------------------------------------------------------------
  useEffect(() => {
    fetchMeals(filters);
  }, [filters, trendDateFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchSummary(trendDateFilter || filters.date);
  }, [filters.date, trendDateFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchTrends();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  /**
   * Add a meal and immediately refresh the list + summary without a full page reload.
   * Throws on validation / duplicate errors so the form can display them.
   */
  const addMeal = useCallback(async (payload) => {
    const created = await createMeal(payload);
    // Prepend to current list if the created meal matches current filters
    setMeals((prev) => [created, ...prev]);
    // Refresh summary for the meal's date
    const mealDate = created.eaten_at.slice(0, 10);
    if (!filters.date || filters.date === mealDate) {
      fetchSummary(filters.date || mealDate);
    }
    fetchTrends();
    return created;
  }, [filters.date, fetchSummary, fetchTrends]);

  /**
   * Delete a meal and immediately remove it from state + refresh summary.
   */
  const removeMeal = useCallback(async (id) => {
    await deleteMeal(id);
    setMeals((prev) => prev.filter((m) => m.id !== id));
    fetchSummary(trendDateFilter || filters.date);
    fetchTrends();
  }, [filters.date, trendDateFilter, fetchSummary, fetchTrends]);

  /**
   * Update filters; resets page to 1 whenever non-page filter changes.
   */
  const updateFilters = useCallback((patch) => {
    setTrendDateFilter(null); // clear trend day selection when user changes filters
    setFilters((prev) => ({
      ...prev,
      ...patch,
      page: "page" in patch ? patch.page : 1,
    }));
  }, []);

  /**
   * Click a trend bar → filter meal list to that date.
   */
  const handleTrendBarClick = useCallback((date) => {
    setTrendDateFilter((prev) => (prev === date ? null : date));
  }, []);

  return {
    // State
    meals,
    pagination,
    mealsLoading,
    mealsError,
    summary,
    summaryLoading,
    summaryError,
    trends,
    trendsLoading,
    trendsError,
    filters,
    trendDateFilter,
    // Actions
    addMeal,
    removeMeal,
    updateFilters,
    handleTrendBarClick,
  };
}
