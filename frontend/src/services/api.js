/**
 * api.js – Centralized Axios instance for all backend communication.
 *
 * Base URL is read from the VITE_API_BASE_URL environment variable so that
 * the same build artifact can target different environments without code changes.
 *
 * All functions return the data payload directly and throw on error so that
 * callers can handle errors in a uniform way.
 */

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});

// ---------------------------------------------------------------------------
// Meals
// ---------------------------------------------------------------------------

/**
 * Fetch a paginated list of meals with optional filters.
 * @param {Object} params – { date, tag, search, page }
 */
export async function listMeals(params = {}) {
  // Remove empty/undefined params so the URL stays clean
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== "" && v != null)
  );
  const { data } = await api.get("/meals/", { params: clean });
  return data; // { count, next, previous, results }
}

/**
 * Create a new meal entry.
 * @param {Object} payload – { name, calories, protein_g, carbs_g, fat_g, tags, eaten_at }
 * @returns {Promise<Object>} Created meal object.
 * @throws {AxiosError} 400 for validation errors, 409 for duplicates.
 */
export async function createMeal(payload) {
  const { data } = await api.post("/meals/", payload);
  return data;
}

/**
 * Delete a meal by ID.
 * @param {number} id
 * @throws {AxiosError} 404 if not found.
 */
export async function deleteMeal(id) {
  await api.delete(`/meals/${id}/`);
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

/**
 * Fetch the daily summary for a given date (defaults to today on the server).
 * @param {string|null} date – YYYY-MM-DD or null for today.
 */
export async function getDailySummary(date = null) {
  const params = date ? { date } : {};
  const { data } = await api.get("/meals/summary/", { params });
  return data;
}

// ---------------------------------------------------------------------------
// Trends
// ---------------------------------------------------------------------------

/**
 * Fetch the N-day calorie trend series.
 * @param {number} days – 1–30, defaults to 7 on the server.
 */
export async function getTrends(days = 7) {
  const { data } = await api.get("/meals/trends/", { params: { days } });
  return data;
}

export default api;
