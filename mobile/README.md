# Health Universe — Mobile (Expo + React Native)

Production scaffold for the iOS/Android app, backed by the existing FastAPI on `healthuniverse.vercel.app`.

## Quickstart

```bash
npx create-expo-app@latest health-universe-mobile -t expo-template-blank-typescript
cd health-universe-mobile
# Copy this `src/` folder into the new project root
npx expo install \
  react-native-safe-area-context \
  expo-secure-store \
  @expo-google-fonts/fraunces \
  @expo-google-fonts/inter \
  expo-font \
  @react-navigation/native \
  @react-navigation/bottom-tabs \
  @react-navigation/native-stack
```

Add to `.env`:

```
EXPO_PUBLIC_API_BASE=https://healthuniverse.vercel.app
```

## What's in `src/`

| Path                                  | Role                                                            |
| ------------------------------------- | --------------------------------------------------------------- |
| `theme/tokens.ts`                     | Color, type, spacing — single source of truth                   |
| `components/Primitives.tsx`           | Eyebrow, H1/H2/H3, Body, Card, TierChip, Pill, buttons          |
| `api/client.ts`                       | Typed fetch helpers against the FastAPI backend                 |
| `screens/HomeScreen.tsx`              | Screen 4 — Home dashboard                                       |
| `screens/StackBriefResultScreen.tsx`  | Screen 6 — Stack brief result                                   |
| `screens/DailyBriefingScreen.tsx`     | Screen 8 — Daily briefing                                       |

## Loading fonts (do this before render in `App.tsx`)

```tsx
import { useFonts, Fraunces_500Medium, Fraunces_600SemiBold } from '@expo-google-fonts/fraunces';
import { Inter_400Regular, Inter_500Medium, Inter_600SemiBold } from '@expo-google-fonts/inter';

const [ready] = useFonts({
  Fraunces_500Medium, Fraunces_600SemiBold,
  Inter_400Regular, Inter_500Medium, Inter_600SemiBold,
});
if (!ready) return null;
```

## API endpoints used by the three scaffolded screens

| Screen           | Method | Path                            |
| ---------------- | ------ | ------------------------------- |
| Home             | GET    | `/api/me/briefing`              |
| Stack brief      | GET    | `/api/me/stack?items=…`         |
| Daily briefing   | GET    | `/api/me/briefing`              |

Other endpoints are wired in `api/client.ts` and ready to use for the remaining 14 screens.

## Auth

Magic-link flow returns a Supabase JWT. Persist it in `expo-secure-store` under key `hu_jwt`; `api/client.ts` attaches it automatically as `Authorization: Bearer …`.

## Next screens to build (priority order)

1. Stack brief input (screen 5) — feeds into `StackBriefResultScreen`
2. Edge detail dossier (screen 10) — wire from the "View dossier" links
3. Onboarding cards 1-3 (screens 1-3)
4. Your data hub (screen 7)
5. Claim checker input + result (screens 15-16)
6. Risk projection (screen 14)
7. Challenge mode input + result + safety-block (screens 11-13)
8. Pre-visit prep (screen 9)
9. Account & settings (screen 17)
