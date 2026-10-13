(() => {
    const header = document.querySelector('.site-header');
    const toggle = document.querySelector('.nav-toggle');
    const drawer = document.getElementById('site-menu');

    if (!header || !toggle || !drawer) return;

    const setOpen = (open, returnFocus = false) => {
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
        drawer.dataset.open = String(open);
        drawer.hidden = !open;
        if (returnFocus) toggle.focus();
    };

    setOpen(false);

    toggle.addEventListener('click', () => {
        setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    drawer.addEventListener('click', (event) => {
        if (event.target.closest('a')) setOpen(false);
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
            setOpen(false, true);
        }
    });

    document.addEventListener('pointerdown', (event) => {
        if (toggle.getAttribute('aria-expanded') === 'true' && !header.contains(event.target)) {
            setOpen(false);
        }
    });

    const wideViewport = window.matchMedia('(min-width: 861px)');
    const closeAtWideViewport = (event) => {
        if (event.matches) setOpen(false);
    };

    if (wideViewport.addEventListener) wideViewport.addEventListener('change', closeAtWideViewport);
    else wideViewport.addListener(closeAtWideViewport);
})();
