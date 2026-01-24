// ===============================================
// SDPT Portal – Scroll Reveal Animation Engine
// Clean • Fast • Mobile-Optimized (2025 Build)
// ===============================================

class ScrollReveal {
    constructor(options = {}) {
        this.settings = Object.assign(
            {
                threshold: 0.12,          // Slightly more sensitive
                once: true,               // Animate only once
                rootMargin: "0px 0px -8% 0px",
                duration: 0.75,           // Global animation time
                easing: "cubic-bezier(.15,.75,.25,1)"
            },
            options
        );

        this.targets = document.querySelectorAll(
            ".reveal, .reveal-left, .reveal-right, .reveal-up, .reveal-zoom"
        );

        this.init();
    }

    init() {
        if (!("IntersectionObserver" in window)) {
            this.showImmediately();
            return;
        }

        const observer = new IntersectionObserver(
            (entries, obs) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.animate(entry.target);
                        if (this.settings.once) obs.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: this.settings.threshold,
                rootMargin: this.settings.rootMargin
            }
        );

        this.targets.forEach(el => {
            this.setInitialState(el);
            observer.observe(el);
        });
    }

    // ===== INITIAL HIDDEN POSITION =====
    setInitialState(el) {
        el.style.opacity = "0";
        el.style.transition = `all ${this.settings.duration}s ${this.settings.easing}`;
        el.style.willChange = "opacity, transform";

        if (el.classList.contains("reveal-left")) {
            el.style.transform = "translateX(-50px)";
        } 
        else if (el.classList.contains("reveal-right")) {
            el.style.transform = "translateX(50px)";
        } 
        else if (el.classList.contains("reveal-up")) {
            el.style.transform = "translateY(45px)";
        } 
        else if (el.classList.contains("reveal-zoom")) {
            el.style.transform = "scale(0.85)";
        } 
        else {
            el.style.transform = "translateY(28px)";
        }
    }

    // ===== SMOOTH REVEAL ANIMATION =====
    animate(el) {
        requestAnimationFrame(() => {
            el.style.opacity = "1";
            el.style.transform = "translateX(0) translateY(0) scale(1)";
        });
    }

    // ===== FALLBACK (OLD BROWSERS) =====
    showImmediately() {
        this.targets.forEach(el => {
            el.style.opacity = "1";
            el.style.transform = "none";
        });
    }
}

// Auto initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => new ScrollReveal());
s