/**
 * App – root component that wires together all sections of the dashboard.
 *
 * Layout:
 *  ┌─────────────────────────────────────────────┐
 *  │  Header                                     │
 *  ├────────────────────┬────────────────────────┤
 *  │  Left column       │  Right column          │
 *  │  ┌──────────────┐  │  ┌──────────────────┐  │
 *  │  │ AddMealForm  │  │  │   SummaryBar     │  │
 *  │  └──────────────┘  │  ├──────────────────┤  │
 *  │                    │  │   FilterBar      │  │
 *  │                    │  ├──────────────────┤  │
 *  │                    │  │   MealList       │  │
 *  │                    │  └──────────────────┘  │
 *  ├────────────────────┴────────────────────────┤
 *  │  TrendsChart (full width)                   │
 *  └─────────────────────────────────────────────┘
 */

import AddMealForm from "./components/AddMealForm";
import FilterBar from "./components/FilterBar";
import MealList from "./components/MealList";
import SummaryBar from "./components/SummaryBar";
import TrendsChart from "./components/TrendsChart";
import { useMeals } from "./hooks/useMeals";

export default function App() {
  const {
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
    addMeal,
    removeMeal,
    updateFilters,
    handleTrendBarClick,
  } = useMeals();

  return (
    <div className="app">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="app-header__inner">
          <div className="app-header__brand">
            <span className="brand-icon" aria-hidden="true">🥗</span>
            <span className="brand-name">Plate</span>
          </div>
          <p className="app-header__tagline">Your daily nutrition, at a glance.</p>
        </div>
      </header>

      <main className="app-main">
        {/* ── Two-column layout ───────────────────────────────────── */}
        <div className="dashboard-grid">
          {/* Left: form */}
          <aside className="col-form">
            <AddMealForm onAdd={addMeal} />
          </aside>

          {/* Right: summary + filters + list */}
          <section className="col-content">
            <SummaryBar
              summary={summary}
              loading={summaryLoading}
              error={summaryError}
              activeDate={trendDateFilter || filters.date}
            />

            <FilterBar
              filters={filters}
              onChange={updateFilters}
              trendDateFilter={trendDateFilter}
              onClearTrendFilter={() => handleTrendBarClick(trendDateFilter)}
            />

            <MealList
              meals={meals}
              pagination={pagination}
              loading={mealsLoading}
              error={mealsError}
              filters={filters}
              onDelete={removeMeal}
              onPageChange={(page) => updateFilters({ page })}
            />
          </section>
        </div>

        {/* ── Full-width trends chart ──────────────────────────────── */}
        <TrendsChart
          trends={trends}
          loading={trendsLoading}
          error={trendsError}
          activeTrendDate={trendDateFilter}
          onBarClick={handleTrendBarClick}
          goalKcal={summary?.goal_kcal || 2000}
        />
      </main>

      <footer className="app-footer">
        <p>Plate · Fitshield Dietfood · Built with Django + React</p>
      </footer>
    </div>
  );
}
