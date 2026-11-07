// Accueil v2 : orbite mise en pause hors écran, barre d'action mobile affichée après le héro.
(function () {
    var hero = document.getElementById('hero-premium');
    var orbit = document.querySelector('[data-orbit]');
    var cta = document.querySelector('[data-mobile-cta]');
    if (!hero || !('IntersectionObserver' in window)) return;

    new IntersectionObserver(function (entries) {
        var visible = entries[0].isIntersecting;
        // L'orbite ne tourne que lorsqu'on la voit (économie de batterie)
        if (orbit) orbit.classList.toggle('is-paused', !visible);
        // Sur mobile, le bouton « Diagnostic gratuit » reste accessible une fois le héro passé
        if (cta) {
            cta.hidden = visible;
            document.body.classList.toggle('v2-cta-visible', !visible);
        }
    }, { threshold: 0.05 }).observe(hero);
})();
