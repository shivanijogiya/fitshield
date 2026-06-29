/**
 * AddMealForm – inline-validated form for logging a new meal.
 *
 * Mirrors backend validation rules:
 *   name   : required, max 100 chars
 *   calories: 1–5000
 *   macros  : ≥ 0
 *   tags    : one or more from the allowed set
 *   eaten_at: not in the future
 *
 * On submit, shows per-field server errors if the backend returns 400.
 * Disables the submit button while the request is in flight.
 */

import { useState } from "react";

const ALLOWED_TAGS = [
  "vegetarian",
  "non-vegetarian",
  "vegan",
  "high-protein",
  "low-carb",
  "snack",
];

const todayLocal = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16); // "YYYY-MM-DDTHH:MM"
};

const INITIAL = {
  name: "",
  calories: "",
  protein_g: "",
  carbs_g: "",
  fat_g: "",
  tags: [],
  eaten_at: todayLocal(),
};

export default function AddMealForm({ onAdd }) {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const set = (key, value) => {
    setForm((p) => ({ ...p, [key]: value }));
    setErrors((p) => ({ ...p, [key]: undefined }));
  };

  const toggleTag = (tag) => {
    setForm((p) => ({
      ...p,
      tags: p.tags.includes(tag) ? p.tags.filter((t) => t !== tag) : [...p.tags, tag],
    }));
  };

  // Client-side validation mirrors backend rules
  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = "Name is required.";
    else if (form.name.trim().length > 100) e.name = "Max 100 characters.";

    const cal = Number(form.calories);
    if (!form.calories) e.calories = "Calories are required.";
    else if (!Number.isInteger(cal) || cal < 1 || cal > 5000)
      e.calories = "Must be an integer between 1 and 5 000.";

    if (form.protein_g !== "" && Number(form.protein_g) < 0)
      e.protein_g = "Must be 0 or greater.";
    if (form.carbs_g !== "" && Number(form.carbs_g) < 0)
      e.carbs_g = "Must be 0 or greater.";
    if (form.fat_g !== "" && Number(form.fat_g) < 0)
      e.fat_g = "Must be 0 or greater.";

    const eaten = new Date(form.eaten_at);
    if (!form.eaten_at) e.eaten_at = "Date/time is required.";
    else if (eaten > new Date()) e.eaten_at = "Cannot be in the future.";

    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const clientErrors = validate();
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }

    setSubmitting(true);
    setErrors({});
    setSuccessMsg("");

    try {
      const payload = {
        name: form.name.trim(),
        calories: Number(form.calories),
        protein_g: form.protein_g !== "" ? Number(form.protein_g) : 0,
        carbs_g: form.carbs_g !== "" ? Number(form.carbs_g) : 0,
        fat_g: form.fat_g !== "" ? Number(form.fat_g) : 0,
        tags: form.tags,
        eaten_at: new Date(form.eaten_at).toISOString(),
      };
      await onAdd(payload);
      setForm({ ...INITIAL, eaten_at: todayLocal() });
      setSuccessMsg("Meal logged!");
      setTimeout(() => setSuccessMsg(""), 2500);
    } catch (err) {
      if (err.response?.status === 400) {
        // Per-field server errors
        setErrors(err.response.data);
      } else if (err.response?.status === 409) {
        setErrors({ name: "A similar meal was already logged within 30 minutes." });
      } else {
        setErrors({ __all__: "Something went wrong. Please try again." });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="add-meal-form" onSubmit={handleSubmit} noValidate>
      <h2 className="form-title">Log a Meal</h2>

      {errors.__all__ && <p className="form-error-banner">{errors.__all__}</p>}
      {successMsg && <p className="form-success">{successMsg}</p>}

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="meal-name">Meal name *</label>
          <input
            id="meal-name"
            type="text"
            placeholder="e.g. Paneer Tikka"
            maxLength={100}
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            className={errors.name ? "input-error" : ""}
            disabled={submitting}
          />
          {errors.name && <span className="field-error">{errors.name}</span>}
        </div>

        <div className="form-field form-field--narrow">
          <label htmlFor="meal-calories">Calories (kcal) *</label>
          <input
            id="meal-calories"
            type="number"
            placeholder="320"
            min={1}
            max={5000}
            value={form.calories}
            onChange={(e) => set("calories", e.target.value)}
            className={errors.calories ? "input-error" : ""}
            disabled={submitting}
          />
          {errors.calories && <span className="field-error">{errors.calories}</span>}
        </div>
      </div>

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="meal-protein">Protein (g)</label>
          <input
            id="meal-protein"
            type="number"
            placeholder="0"
            min={0}
            step="0.1"
            value={form.protein_g}
            onChange={(e) => set("protein_g", e.target.value)}
            className={errors.protein_g ? "input-error" : ""}
            disabled={submitting}
          />
          {errors.protein_g && <span className="field-error">{errors.protein_g}</span>}
        </div>

        <div className="form-field">
          <label htmlFor="meal-carbs">Carbs (g)</label>
          <input
            id="meal-carbs"
            type="number"
            placeholder="0"
            min={0}
            step="0.1"
            value={form.carbs_g}
            onChange={(e) => set("carbs_g", e.target.value)}
            className={errors.carbs_g ? "input-error" : ""}
            disabled={submitting}
          />
          {errors.carbs_g && <span className="field-error">{errors.carbs_g}</span>}
        </div>

        <div className="form-field">
          <label htmlFor="meal-fat">Fat (g)</label>
          <input
            id="meal-fat"
            type="number"
            placeholder="0"
            min={0}
            step="0.1"
            value={form.fat_g}
            onChange={(e) => set("fat_g", e.target.value)}
            className={errors.fat_g ? "input-error" : ""}
            disabled={submitting}
          />
          {errors.fat_g && <span className="field-error">{errors.fat_g}</span>}
        </div>
      </div>

      <div className="form-field">
        <label htmlFor="meal-eaten-at">Eaten at *</label>
        <input
          id="meal-eaten-at"
          type="datetime-local"
          value={form.eaten_at}
          onChange={(e) => set("eaten_at", e.target.value)}
          className={errors.eaten_at ? "input-error" : ""}
          disabled={submitting}
        />
        {errors.eaten_at && <span className="field-error">{errors.eaten_at}</span>}
      </div>

      <div className="form-field">
        <label>Tags</label>
        <div className="tag-picker">
          {ALLOWED_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              className={`tag-chip ${form.tags.includes(tag) ? "tag-chip--active" : ""}`}
              onClick={() => toggleTag(tag)}
              disabled={submitting}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="btn-primary"
        disabled={submitting}
      >
        {submitting ? "Saving…" : "Log Meal"}
      </button>
    </form>
  );
}
