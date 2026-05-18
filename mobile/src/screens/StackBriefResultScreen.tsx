/**
 * Screen 6 — Stack brief result.
 * Sections: Summary card → Conditional harms → Synergies → Evidence cards
 *           → "Before you act" footer (italic, soft).
 * See mobile design brief screen #6 for the visual reference.
 */
import React, { useEffect, useState } from 'react';
import { ScrollView, View, StyleSheet, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Eyebrow,
  H1,
  H2,
  H3,
  Body,
  Caption,
  Card,
  TierChip,
  Pill,
  GoldRule,
  GoldOutlineButton,
} from '../components/Primitives';
import { colors, space, type } from '../theme/tokens';
import { api, StackBriefResult } from '../api/client';

interface Props {
  route?: { params?: { items?: string[] } };
  navigation?: any;
}

export default function StackBriefResultScreen({ route, navigation }: Props) {
  const items = route?.params?.items || [];
  const [data, setData] = useState<StackBriefResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.stackBrief(items);
        setData(r);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
  }, [items.join(',')]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Back + title row */}
        <Pressable onPress={() => navigation?.goBack()} style={{ marginBottom: space.md }}>
          <Body style={{ color: colors.green }}>← Back</Body>
        </Pressable>
        <H1 style={{ fontSize: type.sizes.h2 }}>Your stack brief</H1>

        {/* Summary */}
        <View style={{ marginTop: space.lg }}>
          <Card tint="cream">
            <Eyebrow>Stack summary</Eyebrow>
            <GoldRule />
            <H3 style={{ fontFamily: type.serif, lineHeight: 26 }}>
              {data?.summary || 'Your stack is solid. Two refinements to consider.'}
            </H3>
          </Card>
        </View>

        {/* Conditional harms */}
        {!!(data?.conditional_harms?.length) && (
          <View>
            <H2>Conditional harms</H2>
            <GoldRule />
            {data.conditional_harms.map((h, i) => (
              <Card key={i} leftBorderColor={severityColor(h.severity)}>
                <Pill label={h.severity.toUpperCase()} tone="harmful" />
                <H3 style={{ marginTop: space.sm, fontFamily: type.serif }}>{h.label}</H3>
                <Body style={{ marginTop: space.xs }}>{h.mechanism}</Body>
                <Body soft style={{ marginTop: space.sm, fontStyle: 'italic' }}>
                  {h.context}
                </Body>
                <View style={styles.pillRow}>
                  {h.sources.map((s) => (
                    <View key={s} style={styles.pmidPill}>
                      <Caption style={{ color: colors.inkSoft }}>{s}</Caption>
                    </View>
                  ))}
                </View>
              </Card>
            ))}
          </View>
        )}

        {/* Synergies */}
        {!!(data?.synergies?.length) && (
          <View>
            <H2>Synergies</H2>
            <GoldRule />
            {data.synergies.map((s, i) => (
              <Card key={i} leftBorderColor={colors.protective.fg}>
                <H3 style={{ fontFamily: type.serif }}>{s.label}</H3>
                <Body soft style={{ marginTop: space.xs }}>{s.mechanism}</Body>
              </Card>
            ))}
          </View>
        )}

        {/* Top evidence */}
        {!!(data?.evidence?.length) && (
          <View>
            <H2>Top evidence</H2>
            <GoldRule />
            {data.evidence.map((e) => (
              <Pressable
                key={e.id}
                onPress={() => navigation?.navigate('EdgeDetail', { id: e.id })}
              >
                <Card>
                  <View style={styles.edgeHeader}>
                    <TierChip tier={e.tier} />
                    <Pill label={e.direction} tone={e.direction} />
                  </View>
                  <H3 style={{ marginTop: space.sm, fontFamily: type.serif }}>
                    {e.factor}  →  {e.outcome}
                  </H3>
                  <Body soft style={{ marginTop: space.xs }}>{e.summary}</Body>
                </Card>
              </Pressable>
            ))}
          </View>
        )}

        {error && (
          <Card>
            <Body soft>Couldn't load brief: {error}</Body>
          </Card>
        )}

        {/* Footer disclaimer */}
        <View style={styles.footer}>
          <Body soft style={{ fontStyle: 'italic', textAlign: 'center' }}>
            Before you act: discuss any change with your clinician.{'\n'}
            This is evidence synthesis, not a prescription.
          </Body>
        </View>

        <GoldOutlineButton label="Save brief" onPress={() => {}} />
      </ScrollView>
    </SafeAreaView>
  );
}

const severityColor = (sev: string) => {
  if (sev === 'high') return colors.harmful.fg;
  if (sev === 'moderate') return colors.mixed.fg;
  return colors.protective.fg;
};

const styles = StyleSheet.create({
  scroll: { padding: space.lg, paddingBottom: 120 },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: space.xs,
    marginTop: space.sm,
  },
  pmidPill: {
    backgroundColor: colors.surfaceTint,
    borderRadius: 6,
    paddingHorizontal: space.sm,
    paddingVertical: 2,
  },
  edgeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  footer: {
    backgroundColor: colors.surfaceTint,
    borderRadius: 12,
    padding: space.md,
    marginTop: space.lg,
    marginBottom: space.md,
  },
});
