/**
 * Screen 4 — Home dashboard.
 * Editorial layout: greeting → Today's briefing card → "Evidence that moved" stack.
 * See mobile design brief screen #4 for the visual reference.
 */
import React, { useEffect, useState } from 'react';
import { ScrollView, View, StyleSheet, Pressable, RefreshControl } from 'react-native';
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
} from '../components/Primitives';
import { colors, space, type } from '../theme/tokens';
import { api, TodayBriefing } from '../api/client';

const todayLong = () => {
  const d = new Date();
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
};

export default function HomeScreen({ navigation }: { navigation?: any }) {
  const [data, setData] = useState<TodayBriefing | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setError(null);
      const b = await api.todayBriefing();
      setData(b);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => { load(); }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Top wordmark */}
        <View style={styles.topRow}>
          <H3 style={{ fontFamily: type.serif }}>Health Universe</H3>
          <View style={styles.avatar} />
        </View>

        {/* Greeting */}
        <View style={{ marginTop: space.lg }}>
          <H1>Good morning, Michal</H1>
          <Caption style={{ marginTop: space.xs }}>{todayLong()}</Caption>
        </View>

        {/* Today's briefing — primary card */}
        <View style={{ marginTop: space.xl }}>
          <Card tint="cream">
            <Eyebrow>Today's briefing</Eyebrow>
            <GoldRule />
            <H3 style={{ fontFamily: type.serif, marginBottom: space.sm }}>
              {data?.summary || 'Your health story moves forward.'}
            </H3>

            <View style={styles.pillRow}>
              {(data?.signals || defaultSignals).map((s, i) => (
                <Pill key={i} label={`${s.label} · ${s.count}`} tone={s.tone} />
              ))}
            </View>

            <Pressable
              onPress={() => navigation?.navigate('Briefing')}
              style={{ marginTop: space.lg, alignSelf: 'flex-start' }}
            >
              <Body style={{ color: colors.green, fontFamily: type.sansBold }}>
                Open briefing  →
              </Body>
            </Pressable>
          </Card>
        </View>

        {/* Evidence that moved */}
        <View style={{ marginTop: space.lg }}>
          <H2>Evidence that moved</H2>
          <GoldRule />

          {error && (
            <Card>
              <Body soft>Couldn't load — pull to retry. ({error})</Body>
            </Card>
          )}

          {(data?.evidence_that_moved || defaultEdges).map((edge) => (
            <Pressable
              key={edge.id}
              onPress={() => navigation?.navigate('EdgeDetail', { id: edge.id })}
            >
              <Card>
                <View style={styles.edgeHeader}>
                  <TierChip tier={edge.tier} />
                  <Caption>{edge.date}</Caption>
                </View>
                <H3 style={{ marginTop: space.sm, fontFamily: type.serif }}>
                  {edge.factor}  →  {edge.outcome}
                </H3>
                <Body soft style={{ marginTop: space.xs }}>
                  {edge.why}
                </Body>
                <Body style={{ marginTop: space.sm, color: colors.green, fontFamily: type.sansBold }}>
                  View dossier  →
                </Body>
              </Card>
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

// Placeholder content used until the API resolves — keeps the screen
// looking right in dev / offline.
const defaultSignals: TodayBriefing['signals'] = [
  { label: 'Tier A', tone: 'protective', count: 2 },
  { label: 'Recheck due', tone: 'gold', count: 1 },
  { label: 'Harm flag', tone: 'harmful', count: 1 },
];

const defaultEdges: TodayBriefing['evidence_that_moved'] = [
  {
    id: 'creatine_strength',
    tier: 'A',
    factor: 'Creatine',
    outcome: 'Resistance training',
    why: '63 kg lean-mass and strength gains; safe in healthy adults.',
    date: 'May 16',
  },
  {
    id: 'vitd_mortality',
    tier: 'A',
    factor: 'Vitamin D',
    outcome: 'All-cause mortality',
    why: 'Modest reduction when correcting deficiency.',
    date: 'May 15',
  },
];

const styles = StyleSheet.create({
  scroll: { padding: space.lg, paddingBottom: 120 },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  avatar: {
    width: 32, height: 32,
    borderRadius: 16,
    backgroundColor: colors.goldSoft,
    borderWidth: 1, borderColor: colors.gold,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: space.sm,
    marginTop: space.sm,
  },
  edgeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
});
