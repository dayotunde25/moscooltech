/* Moscool Tech - admin dashboard JavaScript */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        /* --- Confirmation for direct-action forms (e.g. cleanup) ---------- */
        document.querySelectorAll('form.js-confirm').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                var message = form.getAttribute('data-confirm-message') || 'Are you sure?';
                if (!window.confirm(message)) {
                    e.preventDefault();
                }
            });
        });

        /* --- Delete confirmation modals (posts + news) -------------------- */
        var deleteModalEl = document.getElementById('deleteModal');
        var deletePostForm = document.getElementById('deleteForm');
        var deleteNewsForm = document.getElementById('deleteNewsForm');
        var deleteTitleSpan = document.getElementById('deletePostTitle') || document.getElementById('deleteArticleTitle');

        document.querySelectorAll('.delete-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var postId = btn.getAttribute('data-post-id');
                var postTitle = btn.getAttribute('data-post-title');
                if (deleteTitleSpan) deleteTitleSpan.textContent = postTitle;
                if (deletePostForm) deletePostForm.action = '/admin/posts/' + postId + '/delete';
                if (deleteModalEl && window.bootstrap) {
                    new bootstrap.Modal(deleteModalEl).show();
                }
            });
        });

        document.querySelectorAll('.delete-news-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var articleId = btn.getAttribute('data-article-id');
                var articleTitle = btn.getAttribute('data-article-title');
                if (deleteTitleSpan) deleteTitleSpan.textContent = articleTitle;
                if (deleteNewsForm) deleteNewsForm.action = '/admin/news/' + articleId + '/delete';
                if (deleteModalEl && window.bootstrap) {
                    new bootstrap.Modal(deleteModalEl).show();
                }
            });
        });

        /* --- Post type toggle on the create/edit form ---------------------- */
        var postTypeSelect = document.getElementById('post_type');
        if (postTypeSelect) {
            var priceGroups = document.querySelectorAll('.price-group');
            var currencyGroups = document.querySelectorAll('.currency-group');
            var negotiableGroups = document.querySelectorAll('.negotiable-group');
            var itemLinkGroups = document.querySelectorAll('.item-link-group');

            function toggleSaleFields() {
                var isSale = postTypeSelect.value === 'sale';
                priceGroups.forEach(function (g) { g.style.display = isSale ? 'block' : 'none'; });
                currencyGroups.forEach(function (g) { g.style.display = isSale ? 'block' : 'none'; });
                negotiableGroups.forEach(function (g) { g.style.display = isSale ? 'block' : 'none'; });
                itemLinkGroups.forEach(function (g) { g.style.display = isSale ? 'block' : 'none'; });
            }

            toggleSaleFields();
            postTypeSelect.addEventListener('change', toggleSaleFields);
        }

        /* --- "Mark Reviewed" (feedback page) ------------------------------- */
        var successModalEl = document.getElementById('successModal');
        document.querySelectorAll('.mark-reviewed-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                if (successModalEl && window.bootstrap) {
                    new bootstrap.Modal(successModalEl).show();
                }
                btn.innerHTML = '<i class="fas fa-check-circle me-1"></i>Reviewed';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-secondary');
                btn.disabled = true;
            });
        });
    });
})();
