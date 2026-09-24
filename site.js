(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const GLYPHS = 'abcdefghijklmnopqrstuvwxyz0123456789#$%&*+=?';
  const FRAME = 60;
  const FRAMES = 6;
  const scrambles = /[a-z0-9]/i;

  document.querySelectorAll('a').forEach(a => {
    if (a.children.length) return;
    const text = [...a.textContent];
    let timer = 0;

    a.addEventListener('pointerenter', e => {
      if (e.pointerType !== 'mouse') return;
      clearTimeout(timer);
      let f = 0;
      const tick = () => {
        f++;
        const settled = Math.floor(text.length * f / FRAMES);
        a.textContent = text.map((ch, i) =>
          i < settled || !scrambles.test(ch)
            ? ch
            : GLYPHS[Math.random() * GLYPHS.length | 0]
        ).join('');
        if (f < FRAMES) timer = setTimeout(tick, FRAME);
      };
      tick();
    });
  });
})();
