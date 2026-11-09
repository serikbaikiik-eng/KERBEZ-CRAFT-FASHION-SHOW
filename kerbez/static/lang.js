(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Тіл ауысқанда бет жұмсақ өшіп, жаңа тілмен жұмсақ шығады; айналдыру орны сақталады
  try {
    var sv = JSON.parse(sessionStorage.getItem('kc_scroll') || 'null');
    sessionStorage.removeItem('kc_scroll');
    if (sv && sv.p === location.pathname) {
      var put = function () {
        var h = document.documentElement.scrollHeight - window.innerHeight;
        window.scrollTo({ top: sv.r * Math.max(h, 0), behavior: 'instant' });
      };
      put();
      window.addEventListener('load', function () { if (window.scrollY < 2) put(); });
    }
  } catch (e) {}

  document.querySelectorAll('.lang a').forEach(function (a) {
    a.addEventListener('click', function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
      e.preventDefault();
      if (a.getAttribute('aria-current') === 'true') return;
      try {
        var h = document.documentElement.scrollHeight - window.innerHeight;
        sessionStorage.setItem('kc_scroll', JSON.stringify({ p: location.pathname, r: h > 0 ? window.scrollY / h : 0 }));
      } catch (err) {}
      document.documentElement.classList.add('leaving');
      setTimeout(function () { location.href = a.href; }, reduce ? 0 : 240);
    });
  });
  // артқа қайтқанда бет мөлдір қалмасын
  window.addEventListener('pageshow', function (e) { if (e.persisted) document.documentElement.classList.remove('leaving'); });
})();
