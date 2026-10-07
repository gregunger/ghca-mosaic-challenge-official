// SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
// Keep report navigation, theme and contextual help available without network access.
(() => {
  'use strict';
  const sidebar = document.querySelector('.sidebar');
  const opener = document.querySelector('.open-nav');
  const scrim = document.querySelector('.nav-scrim');
  const mobile = window.matchMedia('(max-width: 780px)');
  const setNavigation = (open, restore = true) => {
    sidebar.classList.toggle('is-open', open);
    opener.setAttribute('aria-expanded', String(open));
    scrim.hidden = !open;
    document.body.style.overflow = open && mobile.matches ? 'hidden' : '';
    document.querySelector('.report-shell').inert = open && mobile.matches;
    if (open) sidebar.querySelector('a').focus();
    else if (restore) opener.focus();
  };
  opener.addEventListener('click', () => setNavigation(true));
  document.querySelector('.close-nav').addEventListener('click', () => setNavigation(false));
  scrim.addEventListener('click', () => setNavigation(false));
  sidebar.addEventListener('click', (event) => {
    if (event.target.closest('a') && mobile.matches) setNavigation(false, false);
  });
  mobile.addEventListener('change', () => setNavigation(false, false));
  const themeControl = document.querySelector('#theme');
  const preferredDark = window.matchMedia('(prefers-color-scheme: dark)');
  const applyTheme = (value) => {
    const dark = value === 'dark' || (value === 'system' && preferredDark.matches);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  };
  try {
    themeControl.value = localStorage.getItem('mosaic-report-theme') || 'light';
  } catch {}
  applyTheme(themeControl.value);
  themeControl.addEventListener('change', () => {
    applyTheme(themeControl.value);
    try {
      localStorage.setItem('mosaic-report-theme', themeControl.value);
    } catch {}
  });
  preferredDark.addEventListener('change', () => applyTheme(themeControl.value));

  const tooltip = document.querySelector('#report-tooltip');
  let active = null;
  let keyboardMode = true;
  const closeTooltip = () => {
    if (active) active.removeAttribute('aria-describedby');
    active = null;
    tooltip.hidden = true;
  };
  const showTooltip = (target) => {
    closeTooltip();
    active = target;
    tooltip.textContent = target.dataset.definition;
    target.setAttribute('aria-describedby', tooltip.id);
    tooltip.hidden = false;
    const bounds = target.getBoundingClientRect();
    const box = tooltip.getBoundingClientRect();
    const left = Math.max(14, Math.min(bounds.left, innerWidth - box.width - 14));
    const below = bounds.bottom + 10;
    const top =
      below + box.height < innerHeight - 14 ? below : Math.max(14, bounds.top - box.height - 10);
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  };
  document.addEventListener('pointerdown', () => {
    keyboardMode = false;
  });
  document.addEventListener('keydown', (event) => {
    keyboardMode = true;
    if (event.key === 'Escape') {
      closeTooltip();
      if (sidebar.classList.contains('is-open')) setNavigation(false);
    }
    if (event.key === 'Tab' && mobile.matches && sidebar.classList.contains('is-open')) {
      const controls = Array.from(sidebar.querySelectorAll('a,button,input,select')).filter(
        (element) => !element.hidden && element.getClientRects().length,
      );
      const first = controls[0];
      const last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    if (['Enter', ' '].includes(event.key) && event.target.matches('abbr[data-definition]')) {
      event.preventDefault();
      if (active === event.target) closeTooltip();
      else showTooltip(event.target);
    }
  });
  document.addEventListener('pointerover', (event) => {
    const target = event.target.closest('[data-definition]');
    if (target && event.pointerType === 'mouse') showTooltip(target);
  });
  document.addEventListener('pointerout', (event) => {
    if (
      active &&
      active !== document.activeElement &&
      active.contains(event.target) &&
      !active.contains(event.relatedTarget)
    )
      closeTooltip();
  });
  document.addEventListener('focusin', (event) => {
    const target = event.target.closest('[data-definition]');
    if (target && keyboardMode) showTooltip(target);
  });
  document.addEventListener('focusout', (event) => {
    if (event.target === active) closeTooltip();
  });
  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-definition]');
    if (!target) {
      closeTooltip();
      return;
    }
    if (active === target && !event.detail) closeTooltip();
    else showTooltip(target);
  });
  window.addEventListener(
    'scroll',
    () => {
      if (active && active === document.activeElement) showTooltip(active);
      else closeTooltip();
    },
    { passive: true },
  );
  window.addEventListener('resize', () => {
    if (active && active === document.activeElement) showTooltip(active);
    else closeTooltip();
  });
  document.querySelectorAll('.document-content table').forEach((table) => {
    table.querySelectorAll('thead th').forEach((cell) => (cell.scope = 'col'));
  });
  const scrollRegions = document.querySelectorAll('.document-content table, .table-scroll');
  function updateScrollRegions() {
    scrollRegions.forEach((region) => {
      if (region.scrollWidth > region.clientWidth + 1) region.tabIndex = 0;
      else region.removeAttribute('tabindex');
      const heading = region.closest('section')?.getAttribute('aria-labelledby');
      if (heading) region.setAttribute('aria-labelledby', heading);
      if (!region.matches('table')) region.setAttribute('role', 'region');
    });
  }
  updateScrollRegions();
  window.addEventListener('resize', updateScrollRegions);
  const outline = document.querySelector('.page-outline');
  if (outline && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          outline
            .querySelectorAll('a')
            .forEach((link) =>
              link.classList.toggle('active', link.hash === `#${entry.target.id}`),
            );
        });
      },
      { rootMargin: '-90px 0px -65% 0px' },
    );
    document.querySelectorAll('h2[id]').forEach((heading) => observer.observe(heading));
  }
})();
