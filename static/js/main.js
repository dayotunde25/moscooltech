/* Moscool Tech - public site JavaScript (loaded on all public pages) */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        /* Scroll buttons: elements with [data-scroll="#target"] smooth-scroll to an element. */
        document.querySelectorAll('[data-scroll]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var targetId = btn.getAttribute('data-scroll');
                if (!targetId) return;
                var el = document.querySelector(targetId);
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });

        /* Inline anchor smooth scrolling (skip external/hash-only links without targets). */
        document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
            anchor.addEventListener('click', function (e) {
                var hash = anchor.getAttribute('href');
                var target = null;
                try {
                    target = document.querySelector(hash);
                } catch (err) { /* invalid selector */ }
                if (!target) return; // let the browser handle it (jump to top etc.)
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });

        /* Portfolio / Marketplace tab switching (home page). */
        var tabRadios = document.querySelectorAll('input[name="portfolio-tab"]');
        if (tabRadios.length) {
            var portfolioContent = document.getElementById('portfolio-content');
            var marketplaceContent = document.getElementById('marketplace-content');

            function updateTabs() {
                var activeId = document.querySelector('input[name="portfolio-tab"]:checked');
                if (!activeId) return;
                var showPortfolio = activeId.id === 'portfolio-tab';
                if (portfolioContent) portfolioContent.style.display = showPortfolio ? 'block' : 'none';
                if (marketplaceContent) marketplaceContent.style.display = showPortfolio ? 'none' : 'block';
            }

            tabRadios.forEach(function (radio) {
                radio.addEventListener('change', updateTabs);
            });
            updateTabs();
        }

        /* Subtle hover lift on marketplace/portfolio cards. */
        var hoverCards = document.querySelectorAll('.marketplace-item, .portfolio-item');
        hoverCards.forEach(function (card) {
            card.addEventListener('mouseenter', function () {
                card.style.transform = 'translateY(-5px)';
                card.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
            });
            card.addEventListener('mouseleave', function () {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            });
        });
    });
})();
