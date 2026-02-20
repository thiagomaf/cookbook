import { ref, readonly } from 'vue'

/**
 * Module-level ref — shared across all useTheme() calls.
 * Tracks whether dark mode is currently active.
 */
const _isDark = ref(false)

const STORAGE_KEY = 'cookbook-theme'

export function useTheme() {
  function applyTheme(dark: boolean) {
    document.documentElement.classList.toggle('dark', dark)
    _isDark.value = dark
    localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light')
  }

  function toggleTheme() {
    applyTheme(!_isDark.value)
  }

  /**
   * Call once at app startup (main.ts, before mount).
   * Reads saved preference; falls back to OS preference.
   */
  function initTheme() {
    const saved = localStorage.getItem(STORAGE_KEY)
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme(saved === 'dark' || (!saved && prefersDark))
  }

  return {
    isDark: readonly(_isDark),
    toggleTheme,
    initTheme,
  }
}
