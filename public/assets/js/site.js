// Coque du site : menu mobile, bascule de thème, inscription newsletter du pied de page.
(function () {
    var root = document.documentElement;
    var body = document.body;

    // ---------- Menu latéral (mobile) ----------
    function setSidebar(open) {
        body.classList.toggle('sidebar-open', open);
        document.querySelectorAll('[data-sidebar-toggle]').forEach(function (b) {
            b.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
    }
    document.querySelectorAll('[data-sidebar-toggle]').forEach(function (b) {
        b.addEventListener('click', function () { setSidebar(!body.classList.contains('sidebar-open')); });
    });
    document.querySelectorAll('[data-sidebar-close]').forEach(function (b) {
        b.addEventListener('click', function () { setSidebar(false); });
    });
    document.querySelectorAll('.sidebar-premium a').forEach(function (a) {
        a.addEventListener('click', function () { setSidebar(false); });
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') setSidebar(false);
    });

    // ---------- Thème clair / sombre ----------
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
        b.addEventListener('click', function () {
            var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
            root.setAttribute('data-theme', next);
            try { localStorage.setItem('digita-theme', next); } catch (e) { /* navigation privée */ }
        });
    });

    // ---------- Newsletter ----------
    document.querySelectorAll('[data-newsletter-form]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var msg = form.querySelector('.footer-newsletter-message');
            var btn = form.querySelector('button[type=submit]');
            btn.disabled = true;
            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: { 'Accept': 'application/json' }
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    msg.textContent = data.message;
                    msg.className = 'footer-newsletter-message ' + (data.success ? 'ok' : 'error');
                    if (data.success) form.reset();
                })
                .catch(function () {
                    msg.textContent = 'Une erreur est survenue, merci de réessayer.';
                    msg.className = 'footer-newsletter-message error';
                })
                .finally(function () { btn.disabled = false; });
        });
    });
})();
