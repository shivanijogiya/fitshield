/**
 * FilterBar – date picker, tag dropdown, and search input.
 * All filters are combinable and update together.
 */

const ALLOWED_TAGS = ["", "vegetarian", "non-vegetarian", "vegan", "high-protein", "low-carb", "snack"];

export default function FilterBar({ filters, onChange, trendDateFilter, onClearTrendFilter }) {
  return (
    <div className="filter-bar">
      {trendDateFilter && (
        <div className="trend-filter-notice">
          Showing meals for <strong>{trendDateFilter}</strong>
          <button className="btn-clear-trend" onClick={onClearTrendFilter}>
            ✕ Clear
          </button>
        </div>
      )}
      <div className="filter-bar__controls">
        <div className="filter-field">
          <label htmlFor="filter-date">Date</label>
          <input
            id="filter-date"
            type="date"
            value={filters.date}
            onChange={(e) => onChange({ date: e.target.value })}
            disabled={!!trendDateFilter}
          />
        </div>

        <div className="filter-field">
          <label htmlFor="filter-tag">Tag</label>
          <select
            id="filter-tag"
            value={filters.tag}
            onChange={(e) => onChange({ tag: e.target.value })}
          >
            <option value="">All tags</option>
            {ALLOWED_TAGS.filter(Boolean).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-field filter-field--grow">
          <label htmlFor="filter-search">Search</label>
          <input
            id="filter-search"
            type="search"
            placeholder="Search meals…"
            value={filters.search}
            onChange={(e) => onChange({ search: e.target.value })}
          />
        </div>
      </div>
    </div>
  );
}
