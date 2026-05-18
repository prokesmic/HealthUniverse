/**
 * Reusable primitives that wrap the design tokens.
 * Compose these instead of styling raw <View>/<Text> in screens.
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ViewStyle,
  TextStyle,
  StyleProp,
} from 'react-native';
import { colors, radius, space, type, tierStyle } from '../theme/tokens';

// ─── Text ──────────────────────────────────────────────────────────

export const Eyebrow = ({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) => (
  <Text style={[styles.eyebrow, style]}>{String(children).toUpperCase()}</Text>
);

export const H1 = ({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) => (
  <Text style={[styles.h1, style]}>{children}</Text>
);

export const H2 = ({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) => (
  <Text style={[styles.h2, style]}>{children}</Text>
);

export const H3 = ({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) => (
  <Text style={[styles.h3, style]}>{children}</Text>
);

export const Body = ({ children, soft, style }: { children: React.ReactNode; soft?: boolean; style?: StyleProp<TextStyle> }) => (
  <Text style={[styles.body, soft && { color: colors.inkSoft }, style]}>{children}</Text>
);

export const Caption = ({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) => (
  <Text style={[styles.caption, style]}>{children}</Text>
);

// ─── Card / Surface ────────────────────────────────────────────────

export const Card = ({
  children,
  style,
  tint,
  leftBorderColor,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  tint?: 'cream' | 'plain';
  leftBorderColor?: string;
}) => (
  <View
    style={[
      styles.card,
      tint === 'cream' && { backgroundColor: colors.surfaceTint },
      leftBorderColor ? { borderLeftWidth: 4, borderLeftColor: leftBorderColor } : null,
      style,
    ]}
  >
    {children}
  </View>
);

// ─── Chips ─────────────────────────────────────────────────────────

export const TierChip = ({ tier }: { tier: string }) => {
  const t = tierStyle(tier);
  return (
    <View style={[styles.chip, { backgroundColor: t.bg }]}>
      <Text style={[styles.chipText, { color: t.fg }]}>{`TIER ${(tier || '').toUpperCase()}`}</Text>
    </View>
  );
};

export const Pill = ({ label, tone = 'neutral' }: { label: string; tone?: 'neutral' | 'protective' | 'harmful' | 'mixed' | 'gold' }) => {
  const tones = {
    neutral:    { bg: colors.surfaceTint, fg: colors.inkSoft },
    protective: colors.protective,
    harmful:    colors.harmful,
    mixed:      colors.mixed,
    gold:       { bg: colors.goldSoft, fg: '#5a3a1e' },
  };
  const t = tones[tone];
  return (
    <View style={[styles.chip, { backgroundColor: t.bg }]}>
      <Text style={[styles.chipText, { color: t.fg }]}>{label}</Text>
    </View>
  );
};

// ─── Buttons ───────────────────────────────────────────────────────

export const PrimaryButton = ({ label, onPress }: { label: string; onPress?: () => void }) => (
  <Pressable
    onPress={onPress}
    style={({ pressed }) => [styles.btnPrimary, pressed && { opacity: 0.85 }]}
  >
    <Text style={styles.btnPrimaryText}>{label}</Text>
  </Pressable>
);

export const GoldOutlineButton = ({ label, onPress }: { label: string; onPress?: () => void }) => (
  <Pressable
    onPress={onPress}
    style={({ pressed }) => [styles.btnGold, pressed && { opacity: 0.85 }]}
  >
    <Text style={styles.btnGoldText}>{label}</Text>
  </Pressable>
);

// ─── Divider ───────────────────────────────────────────────────────

export const GoldRule = ({ width = 28 }: { width?: number }) => (
  <View style={{ width, height: 2, backgroundColor: colors.gold, marginTop: 4, marginBottom: space.md }} />
);

// ─── Styles ────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  eyebrow: {
    fontFamily: type.sansBold,
    fontSize: type.sizes.eyebrow,
    color: colors.gold,
    letterSpacing: type.letterSpacing.eyebrow,
  },
  h1: {
    fontFamily: type.serif,
    fontSize: type.sizes.h1,
    color: colors.ink,
    letterSpacing: type.letterSpacing.tight,
    lineHeight: type.sizes.h1 * 1.15,
  },
  h2: {
    fontFamily: type.serif,
    fontSize: type.sizes.h2,
    color: colors.ink,
    lineHeight: type.sizes.h2 * 1.2,
  },
  h3: {
    fontFamily: type.serifBold,
    fontSize: type.sizes.h3,
    color: colors.ink,
  },
  body: {
    fontFamily: type.sans,
    fontSize: type.sizes.body,
    color: colors.ink,
    lineHeight: type.sizes.body * 1.45,
  },
  caption: {
    fontFamily: type.sans,
    fontSize: type.sizes.caption,
    color: colors.inkSoft,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.line,
    padding: space.lg,
    marginBottom: space.md,
  },
  chip: {
    alignSelf: 'flex-start',
    borderRadius: radius.pill,
    paddingHorizontal: space.sm,
    paddingVertical: 2,
  },
  chipText: {
    fontFamily: type.sansBold,
    fontSize: type.sizes.eyebrow,
    letterSpacing: 0.6,
  },
  btnPrimary: {
    backgroundColor: colors.green,
    borderRadius: radius.md,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: space.md,
  },
  btnPrimaryText: {
    color: '#fff',
    fontFamily: type.sansBold,
    fontSize: type.sizes.bodyLg,
  },
  btnGold: {
    borderRadius: radius.md,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.gold,
    backgroundColor: colors.bg,
    marginTop: space.md,
  },
  btnGoldText: {
    color: '#5a3a1e',
    fontFamily: type.sansBold,
    fontSize: type.sizes.body,
  },
});
