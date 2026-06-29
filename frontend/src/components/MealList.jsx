/**
 * MealList – displays paginated meals with loading / empty / error states
 * and per-meal delete confirmation.
 */

import { useState } from "react";

const ALLOWED_TAGS = ["vegetarian", "non-vegetarian", "vegan", "high-protein", "low-carb", "snack"];

const TAG_COLORS = {
  vegetarian: "#22c55e",
  "non-vegetarian": "#ef4444",
  vegan: "#16a34a",
  "high-protein": "#3b82f6",
  "low-carb": "#f59e0b",
  snack: "#a855f7",
};

function formatDate(iso) {
  return new Date(iso).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function MealCard({ meal, onDelete }) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setDeleting(true);
    try {
      await onDelete(meal.id);
    } finally {
      setDeleting(false);
      setConfirming(false);
    }
  };

  return (
    <article className="meal-card">
      <div className="meal-card__body">
        <div className="meal-card__header">
          <h3 className="meal-card__name">{meal.name}</h3>
          <span className="meal-card__cal">{meal.calories} kcal</span>
        </div>
        <div className="meal-card__macros">
          <span>P {parseFloat(meal.protein_g).toFixed(1)}g</span>
          <span>C {parseFloat(meal.carbs_g).toFixed(1)}g</span>
          <span>F {parseFloat(meal.fat_g).toFixed(1)}g</span>
        </div>
        {meal.tags?.length > 0 && (
          <div className="meal-card__tags">
            {meal.tags.map((t) => (
              <span
                key={t}
                className="tag-badge"
                style={{ "--tag-color": TAG_COLORS[t] || "#6b7280" }}
              >
                {t}
              </span>
            ))}
          </div>
        )}
        <time className="meal-card__time">{formatDate(meal.eaten_at)}</time>
      </div>
      <button
        className={`btn-delete ${confirming ? "btn-delete--confirm" : ""}`}
        onClick={handleDelete}
        disabled={deleting}
        title={confirming ? "Click again to confirm" : "Delete meal"}
      >
        {deleting ? "…" : confirming ? "Confirm?" : "Delete"}
      </button>
    </article>
  );
}

export default function MealList({ meals, pagination, loading, error, filters, onDelete, onPageChange }) {
  if (loading) {
    return (
      <div className="meal-list">
        {[1, 2, 3].map((i) => (
          <div key={i} className="meal-card meal-card--skeleton" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-error">
        <p>{error}</p>
        <p className="state-error__hint">Check your connection and try again.</p>
      </div>
    );
  }

  if (!meals.length) {
    return (
      <div className="state-empty">
        <p className="state-empty__icon">🍽️</p>
        <p className="state-empty__msg">No meals found.</p>
        {(filters.search || filters.tag) && (
          <p className="state-empty__hint">Try adjusting your filters.</p>
        )}
      </div>
    );
  }

  const currentPage = filters.page || 1;
  const totalPages = Math.ceil(pagination.count / 10);

  return (
    <div>
      <p className="meal-list__count">
        {pagination.count} meal{pagination.count !== 1 ? "s" : ""} found
      </p>
      <div className="meal-list">
        {meals.map((meal) => (
          <MealCard key={meal.id} meal={meal} onDelete={onDelete} />
        ))}
      </div>
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn-page"
            disabled={!pagination.previous}
            onClick={() => onPageChange(currentPage - 1)}
          >
            ← Prev
          </button>
          <span className="pagination__info">
            Page {currentPage} of {totalPages}
          </span>
          <button
            className="btn-page"
            disabled={!pagination.next}
            onClick={() => onPageChange(currentPage + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
