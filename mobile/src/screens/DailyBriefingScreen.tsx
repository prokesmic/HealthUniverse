/**
 * Screen 8 — Daily briefing.
 * Six-stat strip → Anomalies → Corpus shifts → Loop closures → Correlations.
 * See mobile design brief screen #8 for the visual reference.
 */
import React, { useEffect, useState } from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Eyebrow,
  H1,
  H2,
  H3,
  Body,
  Caption,
  Card,
  GoldRule,
} from '../components/Primitives';
import { colors, space, type, radius } from '../theme/tokens';
import { api, DailyBriefing } from '../api/client';

export default function DailyBriefingScreen() {
  const [data, setData] = useState<DailyBriefing | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.dailyBriefing();
        setData(r);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
  }, []);

  const d = data || placeholder;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Eyebrow>Daily briefing · {d.date}</Eyebrow>
        <H1 style={{ marginTop: space.sm }}>{d.headline}</H1>

        {/* 6-stat horizontal strip */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: space.lg }}>
          <View style={{ flexDirection: 'row', gap: space.sm }}>
            {d.signals.map((s, i) => (
              <View key={i} style={styles.statCard}>
                <Caption>{s.label}</Caption>
                <H3 style={{ fontFamily: type.serif, marginTop: 2 }}>{s.value}</H3>
                {s.delta && (
                  <Caption style={{ color: deltaColor(s.delta) }}>{s.delta}</Caption>
                )}
              </View>
            ))}
          </View>
        </ScrollView>

        {/* Anomalies */}
        <View style={{ marginTop: space.xl }}>
          <H2>Anomalies</H2>
          <GoldRule />
          {d.anomalies.length === 0 ? (
            <Card><Body soft>Nothing out of range over the last 7 days.</Body></Card>
          ) : (
            d.anomalies.map((a, i) => (
              <Card key={i} leftBorderColor={colors.mixed.fg}>
                <H3 style={{ fontFamily: type.serif }}>{a.metric}</H3>
                <Body soft style={{ marginTop: space.xs }}>{a.description}</Body>
              </Card>
            ))
          )}
        </View>

        {/* Corpus shifts */}
        <View>
          <H2>Corpus shifts</H2>
          <GoldRule />
          {d.corpus_shifts.map((s, i) => (
            <Card key={i}>
              <H3 style={{ fontFamily: type.serif }}>{s.description}</H3>
              {s.count > 0 && (
                <Caption style={{ marginTop: space.xs }}>{s.count} new rows</Caption>
              )}
            </Card>
          ))}
        </View>

        {/* Loop closures */}
        <View>
          <H2>Loop closures</H2>
          <GoldRule />
          {d.loops.map((l, i) => (
            <Card key={i} tint="cream">
              <Body>{l.label}</Body>
              {l.due_days !== undefined && (
                <Caption style={{ marginTop: space.xs, color: colors.gold }}>
                  Due in {l.due_days} {l.due_days === 1 ? 'day' : 'days'}
                </Caption>
              )}
            </Card>
          ))}
        </View>

        {/* Correlations */}
        <View>
          <H2>Correlations</H2>
          <GoldRule />
          {d.correlations.map((c, i) => (
            <Card key={i}>
              <H3 style={{ fontFamily: type.serif }}>{c.pair}</H3>
              <Body soft style={{ marginTop: space.xs }}>
                r = {c.r.toFixed(2)} over {c.window_days} days
              </Body>
              {/* Spark-bar showing strength + sign — replace with a chart lib later. */}
              <View style={styles.sparkTrack}>
                <View
                  style={[
                    styles.sparkFill,
                    {
                      width: `${Math.min(Math.abs(c.r) * 100, 100)}%`,
                      backgroundColor: c.r < 0 ? colors.harmful.fg : colors.protective.fg,
                    },
                  ]}
                />
              </View>
            </Card>
          ))}
        </View>

        {error && <Card><Body soft>{error}</Body></Card>}
      </ScrollView>
    </SafeAreaView>
  );
}

const deltaColor = (delta: string) => {
  if (delta.startsWith('+') || delta.startsWith('↑')) return colors.protective.fg;
  if (delta.startsWith('-') || delta.startsWith('↓')) return colors.harmful.fg;
  return colors.inkSoft;
};

// Placeholder used while the network request resolves — keeps the
// screen looking right offline / in dev.
const placeholder: DailyBriefing = {
  date: 'May 17',
  headline: 'Three things to look at today.',
  signals: [
    { label: 'Sleep',  value: '7h 24m', delta: '↑ +12m' },
    { label: 'HRV',    value: '48',     delta: '↓ -18%' },
    { label: 'Steps',  value: '8,431',  delta: '↑' },
    { label: 'RHR',    value: '56',     delta: '↓ -2' },
    { label: 'Mood',   value: 'Good',   delta: '' },
    { label: 'Stress', value: 'Low',    delta: '' },
  ],
  anomalies: [
    {
      metric: 'HRV out of range',
      description: 'HRV down 18% vs your 60-day baseline (z = -2.1).',
    },
  ],
  corpus_shifts: [
    { description: '2 new Tier-A edges touch your stack.', count: 2 },
  ],
  loops: [
    { label: 'Recheck LDL — last drawn 78 days ago', due_days: 12 },
    { label: 'Sleep protocol week 3 — log how it\'s going', due_days: 0 },
  ],
  correlations: [
    { pair: 'Alcohol days vs HRV', r: -0.42, window_days: 90 },
  ],
};

const styles = StyleSheet.create({
  scroll: { padding: space.lg, paddingBottom: 120 },
  statCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    minWidth: 96,
  },
  sparkTrack: {
    marginTop: space.sm,
    height: 4,
    backgroundColor: colors.surfaceTint,
    borderRadius: 2,
    overflow: 'hidden',
  },
  sparkFill: {
    height: 4,
    borderRadius: 2,
  },
});
