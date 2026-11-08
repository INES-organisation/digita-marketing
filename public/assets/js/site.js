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

    // ---------- Listes déroulantes aux couleurs du site ----------
    // Sur ordinateur, le menu natif d'un <select> est dessiné par le système (gris sous macOS)
    // et ignore le CSS. On ouvre à la place une liste au thème du site ; le <select> reste
    // le vrai champ (envoi, validation, événements « change », options ajoutées en JS).
    // Sur écran tactile, le sélecteur natif du téléphone est conservé.
    if (window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
        var pop = null, popSelect = null, popIndex = -1;
        var usable = function (s) {
            return s && s.tagName === 'SELECT' && !s.multiple && !(s.size > 1) && !s.disabled && !s.hasAttribute('data-native');
        };
        var popItems = function () { return pop ? Array.prototype.slice.call(pop.querySelectorAll('.select-pop-item')) : []; };
        var highlight = function (i) {
            var items = popItems();
            if (!items.length) return;
            i = Math.max(0, Math.min(items.length - 1, i));
            items.forEach(function (it, n) { it.classList.toggle('is-active', n === i); });
            popIndex = i;
            items[i].scrollIntoView({ block: 'nearest' });
        };
        var closePop = function () {
            if (!pop) return;
            pop.remove();
            if (popSelect) popSelect.setAttribute('aria-expanded', 'false');
            pop = null; popSelect = null; popIndex = -1;
        };
        var choose = function (i) {
            var it = popItems()[i];
            var s = popSelect;
            if (!it || !s) return closePop();
            var idx = +it.getAttribute('data-index');
            closePop();
            if (s.selectedIndex !== idx) {
                s.selectedIndex = idx;
                s.dispatchEvent(new Event('input', { bubbles: true }));
                s.dispatchEvent(new Event('change', { bubbles: true }));
            }
            s.focus();
        };
        var placePop = function () {
            if (!pop || !popSelect) return;
            var r = popSelect.getBoundingClientRect();
            var below = window.innerHeight - r.bottom - 8, above = r.top - 8;
            var up = below < 200 && above > below;
            pop.style.left = Math.max(8, r.left) + 'px';
            pop.style.minWidth = r.width + 'px';
            pop.style.maxWidth = Math.max(r.width, Math.min(480, window.innerWidth - 16)) + 'px';
            pop.style.maxHeight = Math.min(320, up ? above : below) + 'px';
            pop.style.top = up ? '' : (r.bottom + 4) + 'px';
            pop.style.bottom = up ? (window.innerHeight - r.top + 4) + 'px' : '';
        };
        var openPop = function (s) {
            closePop();
            pop = document.createElement('div');
            pop.className = 'select-pop';
            pop.setAttribute('role', 'listbox');
            Array.prototype.forEach.call(s.options, function (o, n) {
                if (o.disabled || o.hidden) return;
                var it = document.createElement('div');
                it.className = 'select-pop-item' + (n === s.selectedIndex ? ' is-selected' : '');
                it.setAttribute('role', 'option');
                it.setAttribute('aria-selected', n === s.selectedIndex ? 'true' : 'false');
                it.setAttribute('data-index', n);
                it.textContent = o.textContent;
                pop.appendChild(it);
            });
            if (!pop.children.length) { pop = null; return; }
            // Garde le focus sur le <select> (et dans la fenêtre modale éventuelle)
            pop.addEventListener('mousedown', function (e) { e.preventDefault(); });
            pop.addEventListener('click', function (e) {
                var it = e.target.closest('.select-pop-item');
                if (it) choose(popItems().indexOf(it));
            });
            pop.addEventListener('mousemove', function (e) {
                var it = e.target.closest('.select-pop-item');
                if (it) { var i = popItems().indexOf(it); if (i !== popIndex) { popItems().forEach(function (x, n) { x.classList.toggle('is-active', n === i); }); popIndex = i; } }
            });
            (s.closest('.modal, dialog') || document.body).appendChild(pop);
            popSelect = s;
            s.setAttribute('aria-expanded', 'true');
            placePop();
            var sel = pop.querySelector('.is-selected');
            highlight(sel ? popItems().indexOf(sel) : 0);
        };
        document.addEventListener('mousedown', function (e) {
            var s = e.target.closest && e.target.closest('select');
            if (usable(s) && e.button === 0) {
                e.preventDefault();
                if (popSelect === s) { closePop(); return; }
                s.focus();
                openPop(s);
            } else if (pop && !pop.contains(e.target)) {
                closePop();
            }
        }, true);
        document.addEventListener('keydown', function (e) {
            var s = e.target;
            if (pop && s === popSelect) {
                var items = popItems();
                if (e.key === 'ArrowDown') { e.preventDefault(); highlight(popIndex + 1); }
                else if (e.key === 'ArrowUp') { e.preventDefault(); highlight(popIndex - 1); }
                else if (e.key === 'Home' || e.key === 'PageUp') { e.preventDefault(); highlight(0); }
                else if (e.key === 'End' || e.key === 'PageDown') { e.preventDefault(); highlight(items.length - 1); }
                else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); choose(popIndex); }
                else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closePop(); }
                else if (e.key === 'Tab') { closePop(); }
                else if (e.key.length === 1) {
                    var k = e.key.toLowerCase();
                    for (var n = 1; n <= items.length; n++) {
                        var j = (popIndex + n) % items.length;
                        if (items[j].textContent.trim().toLowerCase().indexOf(k) === 0) { highlight(j); break; }
                    }
                    e.preventDefault();
                }
            } else if (usable(s) && (e.key === ' ' || e.key === 'Enter' || ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && (e.altKey || /Mac/.test(navigator.platform))))) {
                e.preventDefault();
                openPop(s);
            }
        }, true);
        document.addEventListener('focusout', function (e) { if (e.target === popSelect) closePop(); });
        window.addEventListener('resize', closePop);
        document.addEventListener('scroll', function (e) { if (pop && !pop.contains(e.target)) closePop(); }, true);
    }

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
