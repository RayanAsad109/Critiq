/* Critiq landing: the motion layer.
   GSAP 3.12.5 + ScrollTrigger and Lenis 1.1.13 (vendor/), with effects in the spirit of React Bits
   (BlurText / SplitText, Magnet, SpotlightCard, CountUp, TiltedCard, ShinyText) rewritten in plain GSAP.
   Every effect is skipped under prefers-reduced-motion, and nothing is hidden until GSAP runs, so the
   page reads complete without this file. */
(() => {
  const gsap = window.gsap, ScrollTrigger = window.ScrollTrigger;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- Spin the reel: the app's weighted spin (app.py spin_dialog) ---------- */
  const reel = $('[data-reel]');
  if (reel) {
    const picks = [
      ['Arrival', 'arrival.jpg', '2016 · 92% match · IMDb 7.9', 92], ['The Prestige', 'prestige.jpg', '2006 · 90% match · IMDb 8.5', 90],
      ['Dark', 'dark.jpg', '2017 · 89% match · IMDb 8.7', 89], ['Shutter Island', 'shutter.jpg', '2010 · 86% match · IMDb 8.2', 86],
      ['Gone Girl', 'gonegirl.jpg', '2014 · 84% match · IMDb 8.1', 84], ['Parasite', 'parasite.jpg', '2019 · 83% match · IMDb 8.5', 83],
      ['Prisoners', 'prisoners.jpg', '2013 · 82% match · IMDb 8.2', 82], ['Zodiac', 'zodiac.jpg', '2007 · 79% match · IMDb 7.7', 79]];
    const strip = $('[data-reel-strip]', reel), btn = $('[data-reel-spin]', reel);
    const title = $('[data-reel-title]', reel), meta = $('[data-reel-meta]', reel), win = $('.reel__window', reel);
    const laps = 5;
    for (let l = 0; l <= laps; l++) for (const p of picks) {
      const i = new Image(); i.src = 'img/' + p[1]; i.width = 168; i.height = 252; i.decoding = 'async';
      i.alt = l === 0 && p === picks[0] ? 'Poster for ' + p[0] : ''; strip.append(i);
    }
    const cell = () => strip.firstElementChild.getBoundingClientRect().height;
    const choose = () => {
      const w = picks.map(p => (p[3] / 100) ** 6), sum = w.reduce((a, b) => a + b, 0);
      let r = Math.random() * sum;
      for (let i = 0; i < w.length; i++) { r -= w[i]; if (r <= 0) return i; }
      return 0;
    };
    let busy = false;
    btn.addEventListener('click', () => {
      if (busy) return; busy = true;
      const k = choose(), stop = laps * picks.length + k;
      const land = () => {
        strip.style.transform = `translateY(${-k * cell()}px)`;
        title.textContent = picks[k][0]; meta.textContent = picks[k][2];
        busy = false; reel.classList.remove('is-spinning');
      };
      if (reduce || !gsap) { land(); return; }
      reel.classList.add('is-spinning');
      gsap.timeline({ onComplete: () => {
        land();
        gsap.fromTo(win, { boxShadow: '0 0 0 6px #241320, 0 0 0 8px #45293a, 0 0 90px rgba(217,169,86,.85)' },
          { boxShadow: '0 0 0 6px #241320, 0 0 0 8px #45293a, 0 0 30px rgba(217,169,86,.3)', duration: 1.4, ease: 'power2.out' });
        gsap.from([title, meta], { y: 14, opacity: 0, duration: 0.6, stagger: 0.08, ease: 'power3.out' });
      } })
        .set(strip, { y: 0, clearProps: 'transform' })
        .to(btn, { scale: 0.94, duration: 0.1, yoyo: true, repeat: 1 }, 0)
        .to(strip, { y: -stop * cell(), duration: 3.4, ease: 'expo.out' }, 0);
    });
  }

  if (!gsap || !ScrollTrigger || reduce) return;
  gsap.registerPlugin(ScrollTrigger);
  document.documentElement.classList.add('cx');

  /* ---------- Lenis smooth scroll, driven by GSAP's ticker ---------- */
  let lenis = null;
  if (window.Lenis) {
    lenis = new window.Lenis({ duration: 1.15, easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)), smoothWheel: true });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(t => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
    $$('a[href^="#"]:not(.skip-link)').forEach(a => a.addEventListener('click', e => {
      const id = a.getAttribute('href'); if (id.length < 2) return;
      const t = $(id); if (!t) return;
      e.preventDefault(); lenis.scrollTo(id === '#top' ? 0 : t, { offset: -72, duration: 1.4 });
    }));
  }

  /* ---------- SplitText / BlurText: words rise out of a mask, sharpening as they come ---------- */
  const split = el => {
    if (!el.dataset.cxSplit) {
      el.dataset.cxSplit = '1';
      el.setAttribute('aria-label', el.textContent.replace(/\s+/g, ' ').trim());
      const walk = node => [...node.childNodes].forEach(n => {
        if (n.nodeType === 3) {
          const frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(p => {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.append(' '); return; }
            const o = document.createElement('span'); o.className = 'cx-w'; o.setAttribute('aria-hidden', 'true');
            const i = document.createElement('span'); i.textContent = p; o.append(i); frag.append(o);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1) walk(n);
      });
      walk(el);
    }
    return $$('.cx-w > span', el);
  };

  /* ---------- the hero: projector beam, entrance, scroll-out ---------- */
  const hero = $('.hero');
  if (hero) {
    const beam = document.createElement('div'); beam.className = 'cx-beam'; beam.setAttribute('aria-hidden', 'true');
    hero.prepend(beam);
    gsap.to(beam, { opacity: 0.75, duration: 0.12, repeat: -1, yoyo: true, repeatDelay: 2.6, ease: 'steps(2)' });
    gsap.to(beam, { rotate: 2.5, duration: 9, repeat: -1, yoyo: true, ease: 'sine.inOut' });

    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    tl.from(beam, { opacity: 0, duration: 1.6, ease: 'power1.out' }, 0)
      .from('.hero__kicker', { y: 12, opacity: 0, duration: 0.6 }, 0.1)
      .from(split($('#hero-h')), { yPercent: 115, opacity: 0, filter: 'blur(10px)', duration: 1.1, stagger: 0.07 }, 0.15)
      .from('.hero__lead', { y: 24, opacity: 0, duration: 0.8 }, 0.55)
      .from('.hero .btn-row .btn', { y: 20, opacity: 0, duration: 0.7, stagger: 0.1 }, 0.7)
      .from('.hero__media', { y: 70, rotateX: 10, scale: 0.95, opacity: 0, transformPerspective: 1400, transformOrigin: '50% 100%', duration: 1.5, ease: 'expo.out' }, 0.25)
      .from('.home__feature', { y: 24, opacity: 0, duration: 0.9 }, 0.75)
      .from('.home__moods span', { y: 10, opacity: 0, stagger: 0.05, duration: 0.5 }, 0.95)
      .from('.home__strip img', { y: 40, rotate: -4, opacity: 0, stagger: 0.07, duration: 0.8 }, 1.05);

    gsap.to('.home__feature img', { scale: 1.1, xPercent: -3, duration: 16, ease: 'sine.inOut', repeat: -1, yoyo: true });

    const out = { trigger: hero, start: 'top top', end: 'bottom top', scrub: true };
    gsap.to('.hero__media', { yPercent: -10, ease: 'none', scrollTrigger: out });
    gsap.to('.hero__text', { y: -70, opacity: 0.15, ease: 'none', scrollTrigger: out });
    gsap.to(beam, { yPercent: 25, ease: 'none', scrollTrigger: out });
  }

  /* ---------- section headings and the words under them ---------- */
  $$('main section:not(.hero) h2').forEach(h => {
    gsap.from(split(h), { yPercent: 115, opacity: 0, filter: 'blur(8px)', duration: 1, stagger: 0.05, ease: 'power3.out',
      scrollTrigger: { trigger: h, start: 'top 86%' } });
  });
  ['#how .span-6 > *', '#reviews .span-5 > :not(h2)', '#reel .span-5 > :not(h2)', '#movie-night .span-6 > *', '#faq .span-5 > :not(h2)']
    .forEach(sel => {
      const els = $$(sel); if (!els.length) return;
      gsap.from(els, { y: 26, opacity: 0, duration: 0.9, stagger: 0.09, ease: 'power3.out', scrollTrigger: { trigger: els[0], start: 'top 88%' } });
    });

  /* ---------- CountUp ---------- */
  const countUp = (el, trigger) => {
    const m = el.textContent.match(/^(\D*)(\d+)(.*)$/s); if (!m) return;
    const o = { v: 0 };
    gsap.to(o, { v: +m[2], duration: 1.6, ease: 'power2.out', scrollTrigger: { trigger: trigger || el, start: 'top 80%' },
      onUpdate: () => { el.textContent = m[1] + Math.round(o.v) + m[3]; } });
  };

  /* ---------- the app window: rises and opens, rows slide in, matches count up ---------- */
  const app = $('.app');
  if (app) {
    gsap.from(app, { y: 110, scale: 0.92, rotateX: 12, opacity: 0.2, transformPerspective: 1600, transformOrigin: '50% 0%', ease: 'none',
      scrollTrigger: { trigger: app, start: 'top 100%', end: 'top 40%', scrub: 1 } });
    gsap.from($$('.ui-win__row', app), { x: -24, opacity: 0, duration: 0.7, stagger: 0.05, ease: 'power3.out', scrollTrigger: { trigger: app, start: 'top 65%' } });
    gsap.from($$('.det__why li, .det__watch li', app), { x: 24, opacity: 0, duration: 0.7, stagger: 0.08, ease: 'power3.out', scrollTrigger: { trigger: app, start: 'top 55%' } });
    gsap.from('.det__hero img', { scale: 1.25, duration: 2.2, ease: 'power2.out', scrollTrigger: { trigger: app, start: 'top 70%' } });
    $$('.ui-win__st, .det__chips .is-match', app).forEach(el => countUp(el, app));
  }

  /* ---------- the review frame opens like an iris; the page drifts on it ---------- */
  const rv = $('#reviews .frame');
  if (rv) {
    gsap.fromTo(rv, { clipPath: 'inset(14% 10% 14% 10% round 28px)' }, { clipPath: 'inset(0% 0% 0% 0% round 20px)', ease: 'none',
      scrollTrigger: { trigger: rv, start: 'top 95%', end: 'top 35%', scrub: 1 } });
    gsap.fromTo('#reviews .ui-doc', { y: 60 }, { y: -30, ease: 'none', scrollTrigger: { trigger: rv, start: 'top bottom', end: 'bottom top', scrub: true } });
  }

  /* ---------- the reel machine drops in ---------- */
  if (reel) gsap.from('.reel__machine', { y: 60, scale: 0.9, opacity: 0, duration: 1.2, ease: 'expo.out', scrollTrigger: { trigger: reel, start: 'top 80%' } });

  /* ---------- cards: staggered rise + SpotlightCard glow under the pointer ---------- */
  ['#features .card', '#import .card'].forEach(sel => {
    $$(sel).forEach((c, i) => gsap.from(c, { y: 80, opacity: 0, duration: 1.1, delay: (i % 3) * 0.12, ease: 'power3.out',
      scrollTrigger: { trigger: c, start: 'top 90%' } }));
  });
  if (fine) $$('#features .panel, #import .panel, .reel').forEach(p => {
    const s = document.createElement('span'); s.className = 'cx-spot'; s.setAttribute('aria-hidden', 'true'); p.append(s);
    p.addEventListener('pointermove', e => {
      const r = p.getBoundingClientRect();
      p.style.setProperty('--mx', `${e.clientX - r.left}px`); p.style.setProperty('--my', `${e.clientY - r.top}px`);
    });
  });

  /* ---------- movie night: the two bars fill, the shared match pops, the losers dim ---------- */
  const mn = $('.mn');
  if (mn) {
    const t = gsap.timeline({ scrollTrigger: { trigger: mn, start: 'top 75%' } });
    t.from(mn, { y: 60, opacity: 0, duration: 1, ease: 'expo.out' })
      .from($$('.mn__list li', mn), { x: -20, opacity: 0, duration: 0.6, stagger: 0.07, ease: 'power3.out' }, 0.2)
      .from($$('.mn__bar i', mn), { width: 0, duration: 1.1, stagger: 0.05, ease: 'power2.inOut' }, 0.4)
      .from($$('.mn__both', mn), { scale: 0, opacity: 0, duration: 0.5, stagger: 0.08, ease: 'back.out(2.4)' }, 1.2)
      .to($$('.mn__list li.is-low', mn), { opacity: 0.5, duration: 0.6 }, 1.8);
    $$('.mn__both', mn).forEach(el => countUp(el, mn));
  }

  /* ---------- FAQ and the footer ---------- */
  gsap.from('.faq__item', { y: 30, opacity: 0, duration: 0.8, stagger: 0.07, ease: 'power3.out', scrollTrigger: { trigger: '.faq', start: 'top 80%' } });
  gsap.from('.faq-marks .ic-tile', { scale: 0.4, opacity: 0, duration: 0.6, stagger: 0.06, ease: 'back.out(2)', scrollTrigger: { trigger: '.faq-marks', start: 'top 90%' } });
  const close = $('.closing__cta');
  if (close) {
    gsap.from('.closing__cta .btn--xl', { scaleX: 0.6, opacity: 0, duration: 1.2, ease: 'expo.out', transformOrigin: '0% 50%', scrollTrigger: { trigger: close, start: 'top 70%' } });
    const mark = $('.footer__mark');
    if (mark) gsap.from(split(mark), { yPercent: 110, opacity: 0, duration: 1, ease: 'power3.out', scrollTrigger: { trigger: mark, start: 'top 95%' } });
  }

  /* ---------- Magnet: primary buttons lean toward the pointer ---------- */
  if (fine) $$('.btn--primary').forEach(b => {
    const k = b.classList.contains('btn--xl') ? 0.12 : 0.32;
    const xTo = gsap.quickTo(b, 'x', { duration: 0.5, ease: 'power3.out' }), yTo = gsap.quickTo(b, 'y', { duration: 0.5, ease: 'power3.out' });
    b.addEventListener('pointermove', e => {
      const r = b.getBoundingClientRect();
      xTo((e.clientX - r.left - r.width / 2) * k); yTo((e.clientY - r.top - r.height / 2) * k);
    });
    b.addEventListener('pointerleave', () => { gsap.to(b, { x: 0, y: 0, duration: 0.9, ease: 'elastic.out(1, 0.4)' }); });
  });

  /* ---------- TiltedCard: the hero's posters lean toward the pointer ---------- */
  if (fine) $$('.home__strip img, .reel__window').forEach(el => {
    el.addEventListener('pointermove', e => {
      const r = el.getBoundingClientRect(), px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
      gsap.to(el, { rotateY: px * 18, rotateX: -py * 18, scale: 1.06, transformPerspective: 600, duration: 0.4, ease: 'power2.out' });
    });
    el.addEventListener('pointerleave', () => gsap.to(el, { rotateY: 0, rotateX: 0, scale: 1, duration: 0.7, ease: 'power3.out' }));
  });

  /* fonts and images change heights: measure again once they are in */
  document.fonts && document.fonts.ready.then(() => ScrollTrigger.refresh());
  addEventListener('load', () => ScrollTrigger.refresh());
})();
