(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 1. Томирис сызбасы қолмен салынғандай пайда болады (егер бетте болса)
  var svg = document.querySelector('.arch svg');
  if (svg && !reduce) {
    var els = svg.querySelectorAll('path,ellipse,circle');
    svg.classList.add('drawing');
    els.forEach(function (el, i) {
      var len = el.getTotalLength ? el.getTotalLength() : 0;
      if (!len) return;
      el.style.strokeDasharray = len;
      el.style.strokeDashoffset = len;
      el.style.transition = 'stroke-dashoffset 1.6s ease ' + Math.min(i * 0.03, 1.2) + 's, fill-opacity 1s ease';
    });
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        els.forEach(function (el) { el.style.strokeDashoffset = 0; });
      });
    });
    setTimeout(function () { svg.classList.remove('drawing'); }, 2000);
    setTimeout(function () {
      els.forEach(function (el) { el.style.strokeDasharray = ''; el.style.strokeDashoffset = ''; el.style.transition = ''; });
    }, 3400);
  }

  // 2. Айналдырғанда блоктар біртіндеп шығады
  if (!reduce && 'IntersectionObserver' in window) {
    var sel = 'section h2, section .lead, #about p, #theme p, blockquote, .goals li, .perks article, .stage, .deadline, .facts div, .croquis, .two > div, .cta p, .cta .btn';
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.15 });
    document.querySelectorAll(sel).forEach(function (el) {
      var idx = Array.prototype.indexOf.call(el.parentNode.children, el);
      el.style.transitionDelay = (idx % 6) * 90 + 'ms';
      el.classList.add('reveal');
      io.observe(el);
    });
  }

  // 3. Телефонда төменгі «Өтінім» батырмасы: hero өткенде шығады, соңғы блокта жасырылады
  var fab = document.getElementById('fab'), hero = document.querySelector('.hero'), cta = document.querySelector('.cta');
  if (fab && hero && 'IntersectionObserver' in window) {
    var vis = { hero: true, cta: false };
    var upd = function () { fab.classList.toggle('show', !vis.hero && !vis.cta); };
    new IntersectionObserver(function (e) { vis.hero = e[0].isIntersecting; upd(); }).observe(hero);
    if (cta) new IntersectionObserver(function (e) { vis.cta = e[0].isIntersecting; upd(); }).observe(cta);
  }

  // 4. Компьютер: скролл сызығы және афишаның тінтуірге жауабы
  var hdr = document.documentElement;
  var prog = function () {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    hdr.style.setProperty('--p', h > 0 ? Math.min(window.scrollY / h, 1).toFixed(4) : 0);
  };
  window.addEventListener('scroll', prog, { passive: true }); prog();
  var pw = document.querySelector('.poster-wrap'), heroEl = document.querySelector('.hero');
  if (pw && heroEl && !reduce && window.matchMedia('(min-width:761px) and (pointer:fine)').matches) {
    heroEl.addEventListener('mousemove', function (e) {
      var r = heroEl.getBoundingClientRect();
      pw.style.setProperty('--px', ((e.clientX - r.left) / r.width - .5) * -18 + 'px');
      pw.style.setProperty('--py', ((e.clientY - r.top) / r.height - .5) * -12 + 'px');
    });
  }

  // 5. Афишаны үлкейтіп көру
  var lb = document.getElementById('lightbox'), po = document.querySelector('.poster');
  if (lb && po && typeof lb.showModal === 'function') {
    po.addEventListener('click', function () { lb.showModal(); });
    lb.addEventListener('click', function () { lb.close(); });
  }

  // 5b. Эскиздер слайдері: сырғыту, батырмалар, нүктелер, автоматты ауысу
  var sl = document.querySelector('.slider');
  if (sl) {
    var track = sl.querySelector('.slides'), n = track.children.length, cur = 0, timer = null;
    var dots = document.querySelectorAll('.croquis .dots button');
    var mark = function () { dots.forEach(function (d, i) { d.setAttribute('aria-current', i === cur ? 'true' : 'false'); }); };
    var go = function (i, smooth) {
      cur = (i + n) % n; mark();
      track.scrollTo({ left: cur * track.clientWidth, behavior: (smooth === false || reduce) ? 'auto' : 'smooth' });
    };
    track.addEventListener('scroll', function () {
      var i = Math.round(track.scrollLeft / track.clientWidth);
      if (i !== cur && i >= 0 && i < n) { cur = i; mark(); }
    }, { passive: true });
    sl.querySelector('.prev').addEventListener('click', function () { stop(); go(cur - 1); });
    sl.querySelector('.next').addEventListener('click', function () { stop(); go(cur + 1); });
    dots.forEach(function (d, i) { d.addEventListener('click', function () { stop(); go(i); }); });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); stop(); go(cur + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); stop(); go(cur - 1); }
    });
    window.addEventListener('resize', function () { go(cur, false); });
    var start = function () { if (!reduce && !timer && onScreen) timer = setInterval(function () { go(cur + 1); }, 5200); };
    var stop = function () { clearInterval(timer); timer = null; };
    var onScreen = false;
    sl.addEventListener('pointerdown', stop);
    sl.addEventListener('focusin', stop);
    sl.addEventListener('mouseenter', stop);
    sl.addEventListener('mouseleave', start);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) { onScreen = en[0].isIntersecting; onScreen ? start() : stop(); }, { threshold: 0.4 }).observe(sl);
    }
  }

  // 5c. Қозғалысты азайту қосулы болса, фондағы видео жүктелмейді
  var hv = document.querySelector('.hero-video');
  if (hv && reduce) hv.remove();

  // 6. Дедлайнға дейінгі күндер санағышы
  var box = document.getElementById('days');
  if (box) {
    var left = Math.ceil((new Date(box.dataset.target + 'T23:59:59') - new Date()) / 86400000);
    var wrap = box.parentNode;
    if (left <= 0) { wrap.textContent = box.dataset.expired || ''; return; }
    var run = function () {
      if (reduce) { box.textContent = left; return; }
      var t0 = null;
      (function step(t) {
        if (!t0) t0 = t;
        var p = Math.min((t - t0) / 1400, 1);
        box.textContent = Math.round(left * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      })(performance.now());
    };
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en, ob) {
        if (en[0].isIntersecting) { run(); ob.disconnect(); }
      }).observe(box);
    } else { run(); }
  }
})();
