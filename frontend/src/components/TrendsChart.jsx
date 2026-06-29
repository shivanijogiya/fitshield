/**
 * TrendsChart – hand-rolled SVG bar chart for 7-day calorie trends.
 *
 * Requirements met:
 *  - No chart library; uses only SVG primitives.
 *  - Bars over the daily goal are visually marked in a different colour.
 *  - Clicking a bar filters the meal list to that day.
 *  - Selected bar is highlighted.
 *  - Loading and error states handled.
 */

const CHART_WIDTH = 600;
const CHART_HEIGHT = 200;
const PADDING = { top: 20, right: 20, bottom: 48, left: 50 };
const INNER_W = CHART_WIDTH - PADDING.left - PADDING.right;
const INNER_H = CHART_HEIGHT - PADDING.top - PADDING.bottom;

function shortDate(isoDate) {
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString("en-IN", { weekday: "short", day: "numeric" });
}

export default function TrendsChart({ trends, loading, error, activeTrendDate, onBarClick, goalKcal = 2000 }) {
  if (loading) {
    return (
      <div className="trends-card">
        <h2 className="trends-title">7-Day Trend</h2>
        <div className="skeleton-chart" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="trends-card">
        <h2 className="trends-title">7-Day Trend</h2>
        <p className="state-error">{error}</p>
      </div>
    );
  }

  if (!trends?.series?.length) return null;

  const series = trends.series;
  const maxCal = Math.max(...series.map((d) => d.calories), goalKcal, 100);

  // Scale helpers
  const xScale = (i) => (i * INNER_W) / series.length + INNER_W / series.length / 2;
  const yScale = (cal) => INNER_H - (cal / maxCal) * INNER_H;
  const barW = Math.max((INNER_W / series.length) * 0.6, 8);

  // Y-axis ticks (goal + round 25%-steps)
  const yTicks = [0, Math.round(maxCal * 0.25), Math.round(maxCal * 0.5), Math.round(maxCal * 0.75), maxCal];

  return (
    <div className="trends-card">
      <div className="trends-header">
        <h2 className="trends-title">7-Day Trend</h2>
        <div className="trends-meta">
          <span>Avg: <strong>{trends.avg_daily_kcal} kcal/day</strong></span>
          {trends.days_over_goal > 0 && (
            <span className="trends-over-tag">{trends.days_over_goal}d over goal</span>
          )}
        </div>
      </div>

      <div className="trends-chart-wrap">
        <svg
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          role="img"
          aria-label="7-day calorie trend chart"
          className="trends-svg"
        >
          {/* Background grid + Y-axis ticks */}
          <g transform={`translate(${PADDING.left}, ${PADDING.top})`}>
            {yTicks.map((tick) => (
              <g key={tick}>
                <line
                  x1={0}
                  x2={INNER_W}
                  y1={yScale(tick)}
                  y2={yScale(tick)}
                  stroke="var(--color-border)"
                  strokeDasharray="4 3"
                  strokeWidth={0.8}
                />
                <text
                  x={-6}
                  y={yScale(tick)}
                  textAnchor="end"
                  dominantBaseline="middle"
                  className="chart-tick-label"
                >
                  {tick > 0 ? `${Math.round(tick / 100) * 100}` : "0"}
                </text>
              </g>
            ))}

            {/* Goal line */}
            <line
              x1={0}
              x2={INNER_W}
              y1={yScale(goalKcal)}
              y2={yScale(goalKcal)}
              stroke="var(--color-accent)"
              strokeWidth={1.5}
              strokeDasharray="6 3"
              opacity={0.7}
            />
            <text
              x={INNER_W + 4}
              y={yScale(goalKcal)}
              dominantBaseline="middle"
              className="chart-goal-label"
            >
              goal
            </text>

            {/* Bars */}
            {series.map((day, i) => {
              const x = xScale(i);
              const barH = Math.max((day.calories / maxCal) * INNER_H, day.calories > 0 ? 2 : 0);
              const y = INNER_H - barH;
              const isOver = day.calories > goalKcal;
              const isActive = activeTrendDate === day.date;
              const isEmpty = day.calories === 0;

              return (
                <g
                  key={day.date}
                  className="chart-bar-group"
                  onClick={() => !isEmpty && onBarClick(day.date)}
                  style={{ cursor: isEmpty ? "default" : "pointer" }}
                  role={isEmpty ? undefined : "button"}
                  aria-label={isEmpty ? `${shortDate(day.date)}: no data` : `${shortDate(day.date)}: ${day.calories} kcal`}
                >
                  {/* Hover / active highlight */}
                  <rect
                    x={x - INNER_W / series.length / 2}
                    y={0}
                    width={INNER_W / series.length}
                    height={INNER_H}
                    fill={isActive ? "var(--color-highlight-bg)" : "transparent"}
                    rx={4}
                  />

                  {/* Bar */}
                  {day.calories > 0 && (
                    <rect
                      x={x - barW / 2}
                      y={y}
                      width={barW}
                      height={barH}
                      rx={4}
                      fill={
                        isActive
                          ? "var(--color-accent-dark)"
                          : isOver
                          ? "var(--color-over-goal)"
                          : "var(--color-bar)"
                      }
                      className="chart-bar"
                    />
                  )}

                  {/* Zero marker */}
                  {day.calories === 0 && (
                    <text
                      x={x}
                      y={INNER_H - 4}
                      textAnchor="middle"
                      className="chart-zero-label"
                    >
                      —
                    </text>
                  )}

                  {/* Calorie label above bar */}
                  {day.calories > 0 && (
                    <text
                      x={x}
                      y={y - 4}
                      textAnchor="middle"
                      className="chart-bar-label"
                    >
                      {day.calories}
                    </text>
                  )}

                  {/* X-axis day label */}
                  <text
                    x={x}
                    y={INNER_H + 18}
                    textAnchor="middle"
                    className={`chart-x-label ${isActive ? "chart-x-label--active" : ""}`}
                  >
                    {shortDate(day.date)}
                  </text>

                  {/* Meal count below day label */}
                  <text
                    x={x}
                    y={INNER_H + 34}
                    textAnchor="middle"
                    className="chart-meal-count"
                  >
                    {day.meal_count > 0 ? `${day.meal_count} meal${day.meal_count !== 1 ? "s" : ""}` : ""}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {activeTrendDate && (
        <p className="trends-click-hint">
          Showing meals for <strong>{activeTrendDate}</strong> — click the bar again or use filters above to reset.
        </p>
      )}
    </div>
  );
}
