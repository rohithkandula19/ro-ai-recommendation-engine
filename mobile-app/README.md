# RO Mobile — Expo / React Native

Shares `@ro/client` TypeScript SDK with the web app.

```bash
cd mobile-app
npm install
npx expo start         # scan QR with Expo Go on iPhone/Android
npx expo start --ios   # iOS simulator
npx expo start --android
```

Set `apiUrl` in `app.json` → `extra.apiUrl` before building.

## What's here
- `app/_layout.tsx` — Expo Router stack, dark theme, React Query provider
- `app/index.tsx` — home feed with horizontal FlatList of recommendations, FAB → chat
- `app/browse/[id].tsx` (TODO) — detail page
- `app/chat.tsx` (TODO) — streaming chat

Mobile is **scaffolded, not polished.** Add detail + chat screens, bottom-tab nav, push notifications via `expo-notifications`.

## Build

```bash
eas build --platform ios
eas build --platform android
```
