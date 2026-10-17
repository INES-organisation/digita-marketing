// Coque du site : menus (accueil et pages internes), bascule de thème, inscription newsletter du pied de page.
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

    // ---------- Menu agence (pages internes) ----------
    var agence = document.getElementById('sidebar-agence');
    function setAgence(open) {
        if (!agence) return;
        body.classList.toggle('agence-open', open);
        agence.setAttribute('aria-hidden', open ? 'false' : 'true');
        document.querySelectorAll('[data-agence-open]').forEach(function (b) {
            b.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
    }
    // Noms d'origine, encore appelés par d'anciens contenus
    window.ouvrirSidebarAgence = function () { setAgence(true); };
    window.fermerSidebarAgence = function () { setAgence(false); };
    document.querySelectorAll('[data-agence-open]').forEach(function (b) {
        b.addEventListener('click', function () { setAgence(true); });
    });
    document.querySelectorAll('[data-agence-close]').forEach(function (b) {
        b.addEventListener('click', function () { setAgence(false); });
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') setAgence(false);
    });

    // ---------- Accueil : section visible surlignée dans le menu ----------
    var sectionLinks = document.querySelectorAll('[data-section-link]');
    if (sectionLinks.length && 'IntersectionObserver' in window) {
        var byId = {};
        sectionLinks.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                sectionLinks.forEach(function (a) { a.classList.remove('active'); a.removeAttribute('aria-current'); });
                var link = byId[entry.target.id];
                if (link) { link.classList.add('active'); link.setAttribute('aria-current', 'true'); }
            });
        }, { rootMargin: '-45% 0px -50% 0px' });
        // Le héros n'a pas d'entrée : quand il est visible, aucun lien n'est surligné
        Object.keys(byId).concat(['hero-premium']).forEach(function (id) {
            var section = document.getElementById(id);
            if (section) observer.observe(section);
        });
    }

    // ---------- Thème clair / sombre ----------
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
        b.addEventListener('click', function () {
            var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
            root.setAttribute('data-theme', next);
            // Composants Bootstrap (cartes, formulaires, textes atténués) suivent le même thème
            root.setAttribute('data-bs-theme', next);
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
