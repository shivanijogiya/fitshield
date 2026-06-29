/**
 * SummaryBar – displays daily calorie progress and macro totals.
 *
 * Updates immediately after every add/delete without page refresh because
 * parent hook refreshes summary state directly.
 */

export default function SummaryBar({ summary, loading, error, activeDate }) {
  if (loading) {
    return <div className="summary-bar summary-bar--loading"><div className="skeleton-line" /></div>;
  }

  if (error) {
    return <div className="summary-bar summary-bar--error"><p>{error}</p></div>;
  }

  if (!summary) return null;

  const pct = Math.min(Math.round((summary.total_calories / summary.goal_kcal) * 100), 100);
  const over = summary.total_calories > summary.goal_kcal;

  const dateLabel = activeDate
    ? new Date(activeDate + "T00:00:00").toLocaleDateString("en-IN", {
        weekday: "short",
        day: "numeric",
        month: "short",
      })
    : "Today";

  return (
    <section className="summary-bar">
      <div className="summary-bar__header">
        <h2 className="summary-bar__title">
          {dateLabel} <span className="summary-bar__count">— {summary.meal_count} meal{summary.meal_count !== 1 ? "s" : ""}</span>
        </h2>
        <span className={`summary-bar__kcal ${over ? "summary-bar__kcal--over" : ""}`}>
          {summary.total_calories} / {summary.goal_kcal} kcal
        </span>
      </div>

      {/* Calorie progress bar */}
      <div className="progress-track" title={`${pct}% of daily goal`}>
        <div
          className={`progress-fill ${over ? "progress-fill--over" : ""}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="progress-labels">
        <span className={over ? "label--over" : ""}>{over ? `${summary.total_calories - summary.goal_kcal} over goal` : `${summary.remaining_kcal} kcal remaining`}</span>
        <span>{pct}%</span>
      </div>

      {/* Macros */}
      <div className="macro-row">
        <div className="macro-chip macro-chip--protein">
          <span className="macro-chip__val">{summary.macros.protein_g.toFixed(1)}g</span>
          <span className="macro-chip__label">Protein</span>
        </div>
        <div className="macro-chip macro-chip--carbs">
          <span className="macro-chip__val">{summary.macros.carbs_g.toFixed(1)}g</span>
          <span className="macro-chip__label">Carbs</span>
        </div>
        <div className="macro-chip macro-chip--fat">
          <span className="macro-chip__val">{summary.macros.fat_g.toFixed(1)}g</span>
          <span className="macro-chip__label">Fat</span>
        </div>
      </div>

      {/* Top tags */}
      {summary.top_tags?.length > 0 && (
        <p className="summary-bar__tags">
          Top tags: {summary.top_tags.join(", ")}
        </p>
      )}
    </section>
  );
}
