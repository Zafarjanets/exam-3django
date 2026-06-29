/* ==========================================================================
   ZAF CHEF — app.js
   Renders dynamic content from {{ x|json_script:"..." }} blocks.
   ========================================================================== */

(function () {
  "use strict";

  function readJSON(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      console.error("Не удалось разобрать JSON для #" + id, e);
      return null;
    }
  }

  function el(tag, className, html) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (html !== undefined) node.innerHTML = html;
    return node;
  }

  /* ---------- generic ingredient badge renderer ---------- */
  function renderIngredientBadges(container, list) {
    if (!container || !Array.isArray(list)) return;
    container.innerHTML = "";
    list.forEach((name, i) => {
      const span = el(
        "span",
        "badge badge-ingredients ingredient-pop",
        `<span class="badge-icon">•</span> ${escapeHTML(name)}`
      );
      span.style.animationDelay = `${i * 0.04}s`;
      container.appendChild(span);
    });
  }

  function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
  }

  /* ---------- dish detail page: ai_dish_detail.html ---------- */
  function renderIngredientsPanel() {
    const data = readJSON("ingredients-json");
    const container = document.getElementById("ingredients-badges");
    if (!data || !container) return;
    renderIngredientBadges(container, data);
  }

  function renderCookingSteps() {
    const data = readJSON("dish-detail-json");
    const container = document.getElementById("cooking-steps");
    if (!data || !container) return;

    // Accept either { steps: [...] } or a raw array of step strings.
    const steps = Array.isArray(data) ? data : data.steps || [];
    container.innerHTML = "";

    if (!steps.length) {
      container.appendChild(
        el("p", null, "Шаги приготовления не найдены.")
      );
      return;
    }

    steps.forEach((step, i) => {
      const text = typeof step === "string" ? step : step.text || step.description || "";
      const row = el("div", "cooking-step");
      row.appendChild(el("div", "cooking-step-num", String(i + 1)));
      row.appendChild(el("div", "cooking-step-text", escapeHTML(text)));
      container.appendChild(row);
    });
  }

  function renderVideoLinks() {
    const data = readJSON("video-links-json");
    const container = document.getElementById("video-links-list");
    if (!data || !container) return;

    container.innerHTML = "";
    data.forEach((item) => {
      const url = typeof item === "string" ? item : item.url;
      const title = typeof item === "string" ? item : item.title || url;
      if (!url) return;

      const a = el(
        "a",
        "video-link-item",
        `<span class="video-link-play">▶</span><span class="video-link-title">${escapeHTML(
          title
        )}</span>`
      );
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      container.appendChild(a);
    });
  }

  /* ---------- dish option cards (recipe_search / image_search results) ---------- */
  function renderDishCards() {
    const data = readJSON("dishes-json");
    const container = document.getElementById("dishes-grid");
    if (!data || !container) return;

    container.innerHTML = "";
    data.forEach((dish) => {
      const url = dish.url || dish.detail_url || (dish.id ? `/dish/${dish.id}/` : "#");
      const card = el(
        "a",
        "dish-option-card",
        `<div class="dish-option-title">${escapeHTML(dish.title || "Без названия")}</div>
         <div class="dish-option-summary">${escapeHTML(dish.summary || dish.description || "")}</div>
         <div class="recipe-badges">
           ${dish.cooking_time ? `<span class="badge"><span class="badge-icon">⏱</span> ${escapeHTML(dish.cooking_time)} мин</span>` : ""}
           ${dish.difficulty ? `<span class="badge badge-success">${escapeHTML(dish.difficulty)}</span>` : ""}
         </div>`
      );
      card.href = url;
      container.appendChild(card);
    });
  }

  /* ---------- image_search.html: detected ingredients ---------- */
  function renderDetectedIngredients() {
    const data = readJSON("detected-ingredients-json");
    const container = document.getElementById("badge-wrapper");
    if (!data || !container) return;
    renderIngredientBadges(container, data);
  }

  /* ---------- recipe_search.html: ingredients used in search ---------- */
  function renderSearchIngredients() {
    const data = readJSON("search-ingredients-json");
    const container = document.getElementById("search-ingredients");
    if (!data || !container) return;
    renderIngredientBadges(container, data);
  }

  /* ---------- history.html: ingredient badges per request ---------- */
  function renderHistoryBadges() {
    document.querySelectorAll(".history-badges-list").forEach((container) => {
      const raw = container.dataset.ingredients;
      if (!raw) return;
      let list;
      try {
        list = JSON.parse(raw);
      } catch (e) {
        // Fallback: plain comma-separated text.
        list = raw.split(",").map((s) => s.trim()).filter(Boolean);
      }
      renderIngredientBadges(container, list);
    });
  }

  /* ---------- profile.html: animated stat counters ---------- */
  function renderStatCounters() {
    document.querySelectorAll(".stat-value[data-count]").forEach((node) => {
      const target = parseInt(node.dataset.count, 10) || 0;
      const duration = 700;
      const start = performance.now();

      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        node.textContent = Math.round(eased * target);
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  /* ---------- image_search.html: upload UX ---------- */
  function wireImageUpload() {
    const input = document.getElementById("image-input");
    const fileName = document.getElementById("file-name");
    const form = document.getElementById("image-form");
    const submitBtn = document.getElementById("submit-btn");
    const loader = document.getElementById("loader-overlay");

    if (input && fileName) {
      input.addEventListener("change", () => {
        fileName.textContent = input.files.length
          ? input.files[0].name
          : "JPG, PNG, WEBP";
      });
    }

    if (form && submitBtn) {
      form.addEventListener("submit", () => {
        submitBtn.disabled = true;
        submitBtn.innerHTML =
          '<span class="btn-loading"><span class="spin-icon">⟳</span> Анализ изображения...</span>';
        if (loader) loader.classList.remove("hidden");
      });
    }
  }

  /* ---------- video button: point "Смотреть видео" at first rendered link ---------- */
  function wireMainVideoButton() {
    const btn = document.getElementById("main-video-btn");
    const data = readJSON("video-links-json");
    if (btn && data && data.length) {
      const first = data[0];
      btn.href = typeof first === "string" ? first : first.url;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderIngredientsPanel();
    renderCookingSteps();
    renderVideoLinks();
    renderDishCards();
    renderDetectedIngredients();
    renderSearchIngredients();
    renderHistoryBadges();
    renderStatCounters();
    wireImageUpload();
    wireMainVideoButton();
  });
})();
