(() => {
    const bar = document.getElementById('progressBar');
    if (!bar) return;

    let scheduled = false;

    const updateProgress = () => {
        const root = document.documentElement;
        const distance = root.scrollHeight - root.clientHeight;
        const progress = distance > 0 ? (root.scrollTop / distance) * 100 : 0;
        bar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
        scheduled = false;
    };

    const requestUpdate = () => {
        if (scheduled) return;
        scheduled = true;
        window.requestAnimationFrame(updateProgress);
    };

    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', requestUpdate, { passive: true });
    updateProgress();
})();
