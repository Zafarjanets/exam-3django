/**
 * Zaf Chef — UI animations & JSON-driven components
 */
(function () {
    'use strict';

    const FOOD_ICONS = ['🍳', '🥘', '🍲', '🥗', '🍕', '🌮', '🥙', '🍜', '🧀', '🥚'];

    function readJson(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch {
            return null;
        }
    }

    /* ── Floating background orbs ── */
    function initOrbs() {
        const wrap = document.querySelector('.bg-orbs');
        if (!wrap) return;
        wrap.querySelectorAll('.orb').forEach((orb, i) => {
            orb.style.animationDelay = `${i * 1.4}s`;
        });
    }

    /* ── Floating food emojis ── */
    function initFloatingIcons() {
        const container = document.getElementById('floating-icons');
        if (!container) return;

        for (let i = 0; i < 14; i++) {
            const span = document.createElement('span');
            span.className = 'float-icon';
            span.textContent = FOOD_ICONS[i % FOOD_ICONS.length];
            span.style.left = `${Math.random() * 100}%`;
            span.style.top = `${Math.random() * 100}%`;
            span.style.animationDuration = `${12 + Math.random() * 18}s`;
            span.style.animationDelay = `${Math.random() * 8}s`;
            span.style.fontSize = `${18 + Math.random() * 22}px`;
            span.style.opacity = `${0.04 + Math.random() * 0.08}`;
            container.appendChild(span);
        }
    }

    /* ── Scroll reveal ── */
    function initReveal() {
        const els = document.querySelectorAll('.reveal, .dish-option-card, .dashboard-card, .fav-card, .history-card');
        if (!els.length) return;

        const io = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');
                        io.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
        );

        els.forEach((el, i) => {
            el.style.setProperty('--reveal-delay', `${i * 0.08}s`);
            io.observe(el);
        });
    }

    /* ── Navbar scroll glow ── */
    function initNavbar() {
        const nav = document.querySelector('.navbar');
        if (!nav) return;
        window.addEventListener('scroll', () => {
            nav.classList.toggle('navbar-scrolled', window.scrollY > 20);
        }, { passive: true });
    }

    /* ── Animated icon wiggle on hover ── */
    function initIconHover() {
        document.querySelectorAll('.icon-bounce, .card-icon, .dish-option-icon').forEach((el) => {
            el.addEventListener('mouseenter', () => el.classList.add('icon-wiggle'));
            el.addEventListener('animationend', () => el.classList.remove('icon-wiggle'));
        });
    }

    /* ── Dish cards from JSON ── */
    function initDishGrid(jsonId, containerId) {
        const data = readJson(jsonId);
        const container = document.getElementById(containerId);
        if (!data || !container) return;

        container.innerHTML = '';

        data.forEach((dish, index) => {
            const card = document.createElement('a');
            card.href = dish.url;
            card.className = 'dish-option-card glass-panel reveal';
            card.style.setProperty('--reveal-delay', `${index * 0.12}s`);
            card.style.setProperty('--card-accent', dish.accent || '#ff6b35');

            card.innerHTML = `
                <div class="dish-card-glow"></div>
                <div class="dish-option-icon icon-bounce">${dish.icon}</div>
                <span class="dish-card-number">#${index + 1}</span>
                <h3>${escapeHtml(dish.title)}</h3>
                <p>${escapeHtml(dish.summary)}</p>
                <div class="recipe-badges dish-card-badges">
                    <span class="badge badge-animated"><span class="badge-icon">⏱️</span> ${dish.cooking_time} мин</span>
                    <span class="badge badge-success badge-animated"><span class="badge-icon">✨</span> ${escapeHtml(dish.difficulty)}</span>
                </div>
                <span class="dish-option-link">
                    <span>Читать рецепт</span>
                    <span class="arrow-slide">→</span>
                </span>
            `;

            container.appendChild(card);
        });

        initReveal();
        initIconHover();
    }

    /* ── Ingredient badges from JSON ── */
    function initIngredientBadges(jsonId, containerId) {
        const items = readJson(jsonId);
        const container = document.getElementById(containerId);
        if (!items || !container) return;

        container.innerHTML = '';
        items.forEach((name, i) => {
            const span = document.createElement('span');
            span.className = 'badge badge-ingredients badge-animated ingredient-pop';
            span.style.animationDelay = `${i * 0.07}s`;
            span.innerHTML = `<span class="badge-icon">🥕</span> ${escapeHtml(name)}`;
            container.appendChild(span);
        });
    }

    /* ── Cooking steps from JSON text ── */
    function initCookingSteps(jsonId, containerId) {
        const data = readJson(jsonId);
        const container = document.getElementById(containerId);
        if (!data || !container) return;

        const steps = parseSteps(data.instructions);
        container.innerHTML = '';

        steps.forEach((step, i) => {
            const div = document.createElement('div');
            div.className = 'cooking-step reveal';
            div.style.setProperty('--reveal-delay', `${i * 0.1}s`);
            div.innerHTML = `
                <div class="step-number">${i + 1}</div>
                <div class="step-content">${escapeHtml(step)}</div>
            `;
            container.appendChild(div);
        });

        initReveal();
    }

    function parseSteps(text) {
        if (!text) return [];
        const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
        const numbered = lines.filter((l) => /^\d+[\.\)]\s*/.test(l));
        if (numbered.length >= 2) {
            return numbered.map((l) => l.replace(/^\d+[\.\)]\s*/, ''));
        }
        if (lines.length >= 2) return lines;
        return text.split(/(?<=[.!?])\s+/).filter((s) => s.length > 10);
    }

    /* ── Video links from JSON ── */
    function initVideoLinks(jsonId, listId, mainBtnId) {
        const links = readJson(jsonId);
        const list = document.getElementById(listId);
        if (!links || !list) return;

        list.innerHTML = '';
        links.forEach((link, i) => {
            const a = document.createElement('a');
            a.href = link.url;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.className = 'video-link-item reveal';
            a.style.setProperty('--reveal-delay', `${i * 0.1}s`);
            a.innerHTML = `
                <span class="video-link-icon pulse-play">▶</span>
                <span class="video-link-text">${escapeHtml(link.label)}</span>
                <span class="video-link-arrow">↗</span>
            `;
            list.appendChild(a);
        });

        if (mainBtnId && links[0]) {
            const btn = document.getElementById(mainBtnId);
            if (btn) btn.href = links[0].url;
        }

        initReveal();
    }

    /* ── Counter animation for stats ── */
    function initCounters() {
        document.querySelectorAll('[data-count]').forEach((el) => {
            const target = parseInt(el.dataset.count, 10);
            if (isNaN(target)) return;
            let current = 0;
            const step = Math.max(1, Math.ceil(target / 30));
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                el.textContent = current;
            }, 30);
        });
    }

    /* ── Loader pulse rings ── */
    function initLoader() {
        const loader = document.querySelector('.loader-rings');
        if (!loader) return;
        for (let i = 0; i < 3; i++) {
            const ring = document.createElement('div');
            ring.className = 'loader-ring';
            ring.style.animationDelay = `${i * 0.5}s`;
            loader.appendChild(ring);
        }
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    /* ── Boot ── */
    document.addEventListener('DOMContentLoaded', () => {
        initOrbs();
        initFloatingIcons();
        initNavbar();
        initIconHover();
        initReveal();
        initCounters();
        initLoader();

        initDishGrid('dishes-json', 'dishes-grid');
        initIngredientBadges('ingredients-json', 'ingredients-badges');
        initCookingSteps('dish-detail-json', 'cooking-steps');
        initVideoLinks('video-links-json', 'video-links-list', 'main-video-btn');

        initIngredientBadges('detected-ingredients-json', 'badge-wrapper');
    });
})();
