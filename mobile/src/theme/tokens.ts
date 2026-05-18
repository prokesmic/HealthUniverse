/**
 * Design tokens — single source of truth for color, type, spacing.
 * Mirrors the visual language locked in via ChatGPT Images 2 mockups.
 * Keep in sync with web/static/* if you ever extract a shared package.
 */

export const colors = {
  // Surfaces
  bg: '#fdf6e3',          // app background (cream)
  surface: '#ffffff',     // card surface
  surfaceTint: '#faf4dd', // softer cream for nested cards / inputs
  line: '#e8e2d0',        // hairline borders

  // Ink
  ink: '#1f1f1f',
  inkSoft: '#5a5a5a',
  inkMuted: '#8a8a8a',

  // Brand
  green: '#1f3a2e',       // primary actions, headings accent
  greenSoft: '#2d5440',
  gold: '#c9a961',        // eyebrows, dividers, secondary accent
  goldSoft: '#e6d4a3',

  // Tier chips
  tierA: { bg: '#e7f5ec', fg: '#1b5e20' },
  tierB: { bg: '#fff7e0', fg: '#7a5c00' },
  tierC: { bg: '#fdecea', fg: '#9b1c1c' },
  tierX: { bg: '#ece6f3', fg: '#3b2a5e' },
  tierD: { bg: '#efe6dc', fg: '#5a3a1e' },

  // Direction / status
  protective: { bg: '#e7f5ec', fg: '#1b5e20' },
  harmful:    { bg: '#fdecea', fg: '#9b1c1c' },
  mixed:      { bg: '#fff7e0', fg: '#7a5c00' },

  // Severity (safety blocks, conditional harms)
  highBg: '#fdecea',
  highLine: '#f3b3ad',
  highFg: '#9b1c1c',

  // Disclaimer strip
  noteBg: '#fffbe7',
  noteLine: '#f0d68a',
  noteFg: '#7a5c00',
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 14,
  pill: 999,
} as const;

export const space = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const type = {
  // Use expo-google-fonts/fraunces + inter — load in App.tsx before render.
  serif: 'Fraunces_500Medium',
  serifBold: 'Fraunces_600SemiBold',
  sans: 'Inter_400Regular',
  sansMed: 'Inter_500Medium',
  sansBold: 'Inter_600SemiBold',

  sizes: {
    eyebrow: 11,    // uppercase, letter-spaced
    caption: 12,
    body: 15,
    bodyLg: 17,
    h3: 20,
    h2: 26,
    h1: 32,
    display: 48,
  },

  letterSpacing: {
    eyebrow: 1.4,
    tight: -0.2,
  },
} as const;

export const tierStyle = (tier: string) => {
  const t = (tier || '').toUpperCase();
  if (t === 'A') return colors.tierA;
  if (t === 'B') return colors.tierB;
  if (t === 'C') return colors.tierC;
  if (t === 'X') return colors.tierX;
  if (t === 'D') return colors.tierD;
  return colors.tierB;
};
