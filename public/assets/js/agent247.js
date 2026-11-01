// Page de vente Agent IA 24/7 : apparitions, conversation jouée, compteurs, halo et inclinaison.
// Sans ce script la page reste complète (agent247.css ne masque rien sans la classe html.js).
(function () {
  var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;

  function countUp(el) {
    var end = +el.dataset.count, start = performance.now();
    (function frame(now) {
      var t = Math.min((now - start) / 1400, 1);
      el.textContent = Math.round(end * (1 - Math.pow(1 - t, 3)));
      if (t < 1) requestAnimationFrame(frame);
    })(start);
  }

  var seen = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in');
      if (!still) entry.target.querySelectorAll('[data-count]').forEach(countUp);
      seen.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.rv, [data-steps]').forEach(function (el) { seen.observe(el); });

  // Conversation : chaque message s'affiche à son tour, puis les trois confirmations, puis on rejoue.
  var stage = document.querySelector('.stage');
  if (stage && !still) {
    var messages = Array.prototype.slice.call(stage.querySelectorAll('.msg'));
    var toasts = Array.prototype.slice.call(stage.querySelectorAll('.toast'));
    var typing = stage.querySelector('.typing');
    var clock = stage.querySelector('.clock');
    var timer, step = 0, visible = true;

    var show = function (el) { el.classList.add('on'); };
    var wait = function (fn, ms) { timer = setTimeout(fn, ms); };

    function reset() {
      messages.concat(toasts).forEach(function (el) { el.classList.remove('on'); });
      clock.textContent = '23:14';
      step = 0;
    }

    function next() {
      if (!visible) return;
      if (step === messages.length) {
        clock.textContent = '23:15';
        typing.classList.remove('on');
        toasts.forEach(function (toast, i) { setTimeout(show, 500 + i * 700, toast); });
        step = 0;
        return wait(function () { reset(); next(); }, 6500);
      }
      var msg = messages[step++];
      if (msg.classList.contains('out')) {
        typing.classList.add('on');
        return wait(function () {
          typing.classList.remove('on');
          show(msg);
          wait(next, 1500);
        }, 1400);
      }
      show(msg);
      wait(next, 1300);
    }

    stage.classList.add('playing');
    stage.querySelector('.phone').classList.add('playing');
    reset();
    // La boucle s'arrête quand le téléphone sort de l'écran.
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting;
      clearTimeout(timer);
      if (visible) { reset(); next(); }
    }, { threshold: 0.2 }).observe(stage);
  }

  if (still || !finePointer) return;

  // Halo sous le pointeur sur les cartes.
  document.addEventListener('pointermove', function (e) {
    var card = e.target.closest && e.target.closest('.spot');
    if (!card) return;
    var box = card.getBoundingClientRect();
    card.style.setProperty('--mx', (e.clientX - box.left) + 'px');
    card.style.setProperty('--my', (e.clientY - box.top) + 'px');
  }, { passive: true });

  // Le téléphone s'incline légèrement vers le pointeur.
  var tilt = document.querySelector('[data-tilt]');
  if (tilt) {
    var phone = tilt.querySelector('.phone');
    document.querySelector('.hero').addEventListener('pointermove', function (e) {
      var box = tilt.getBoundingClientRect();
      var x = (e.clientX - box.left - box.width / 2) / innerWidth;
      var y = (e.clientY - box.top - box.height / 2) / innerHeight;
      phone.style.setProperty('--ry', (x * 16).toFixed(2) + 'deg');
      phone.style.setProperty('--rx', (-y * 12).toFixed(2) + 'deg');
    }, { passive: true });
  }
})();
