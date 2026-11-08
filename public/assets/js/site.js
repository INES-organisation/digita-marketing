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
    var sectionLinks = Array.prototype.slice.call(document.querySelectorAll('[data-section-link]'));
    if (sectionLinks.length) {
        // La section active est la dernière dont le haut a dépassé le premier tiers de l'écran
        // (fiable quelle que soit la hauteur de l'écran, même pour une section courte).
        // En bas de page, la dernière section est active ; dans le héros, aucune.
        var spy = sectionLinks.map(function (a) {
            return { link: a, section: document.getElementById(a.getAttribute('href').slice(1)) };
        }).filter(function (x) { return x.section; });
        var setActive = function (link) {
            sectionLinks.forEach(function (a) {
                var on = a === link;
                a.classList.toggle('active', on);
                if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
            });
        };
        var updateSpy = function () {
            var line = Math.min(window.innerHeight * 0.33, 320);
            var current = null;
            spy.forEach(function (x) { if (x.section.getBoundingClientRect().top <= line) current = x.link; });
            var atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
            if (atBottom && spy.length) current = spy[spy.length - 1].link;
            setActive(current);
        };
        var spyTicking = false;
        window.addEventListener('scroll', function () {
            if (spyTicking) return;
            spyTicking = true;
            window.requestAnimationFrame(function () { updateSpy(); spyTicking = false; });
        }, { passive: true });
        window.addEventListener('resize', updateSpy);
        // Au clic, le lien choisi est surligné tout de suite
        spy.forEach(function (x) { x.link.addEventListener('click', function () { setActive(x.link); }); });
        updateSpy();
    }

    // ---------- Arrivée sur une ancre depuis une autre page ----------
    // Le navigateur saute à l'ancre avant la fin du chargement (polices, images) : le contenu
    // se décale ensuite et la cible finit sous la barre fixe. On la recale une fois tout chargé.
    // (Le catalogue a son propre calage, plus fin : on le laisse faire.)
    if (location.hash.length > 1 && !document.querySelector('[data-catalogue-nav]')) {
        var realignHash = function () {
            var target;
            try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (e) { return; }
            if (!target || target.closest('.modal')) return;
            if (target.hasAttribute('data-aos')) target.classList.add('aos-animate');
            target.scrollIntoView({ block: 'start', behavior: 'instant' });
        };
        window.addEventListener('load', function () { realignHash(); setTimeout(realignHash, 350); });
        if (document.fonts && document.fonts.ready) document.fonts.ready.then(realignHash);
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

    // ---------- Carrousels horizontaux (Réalisations de l'accueil) ----------
    document.querySelectorAll('[data-carousel]').forEach(function (carousel) {
        var track = carousel.querySelector('[data-carousel-track]');
        var prev = carousel.querySelector('[data-carousel-prev]');
        var next = carousel.querySelector('[data-carousel-next]');
        var dotsBox = carousel.parentElement.querySelector('[data-carousel-dots]');
        var dots = dotsBox ? Array.prototype.slice.call(dotsBox.querySelectorAll('button')) : [];
        var slides = Array.prototype.slice.call(track.children);
        function step() { return slides.length > 1 ? slides[1].offsetLeft - slides[0].offsetLeft : track.clientWidth; }
        function current() { return Math.round(track.scrollLeft / step()); }
        function go(i) {
            i = Math.max(0, Math.min(slides.length - 1, i));
            track.scrollTo({ left: slides[i].offsetLeft - slides[0].offsetLeft, behavior: 'smooth' });
        }
        function update() {
            var max = track.scrollWidth - track.clientWidth - 2;
            if (prev) prev.disabled = track.scrollLeft <= 2;
            if (next) next.disabled = track.scrollLeft >= max;
            var index = track.scrollLeft >= max ? slides.length - 1 : current();
            dots.forEach(function (d, i) { d.classList.toggle('active', i === index); });
        }
        if (prev) prev.addEventListener('click', function () { go(current() - 1); });
        if (next) next.addEventListener('click', function () { go(current() + 1); });
        dots.forEach(function (d, i) { d.addEventListener('click', function () { go(i); }); });
        track.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowRight') { e.preventDefault(); go(current() + 1); }
            if (e.key === 'ArrowLeft') { e.preventDefault(); go(current() - 1); }
        });
        track.addEventListener('scroll', function () { window.requestAnimationFrame(update); }, { passive: true });
        window.addEventListener('resize', update);
        update();
    });
})();
