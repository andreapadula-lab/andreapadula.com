(() => {
    const bar = document.getElementById('progressBar');
    if (!bar) return;

    const updateProgress = () => {
        const root = document.documentElement;
        const distance = root.scrollHeight - root.clientHeight;
        const progress = distance > 0 ? (root.scrollTop / distance) * 100 : 0;
        bar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    };

    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
})();
