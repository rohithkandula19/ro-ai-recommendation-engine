# @ro/client

TypeScript SDK for the RO AI Recommendation Engine. Works in Node, Deno, Bun, browsers, edge runtimes.

## Install

```bash
npm install @ro/client
```

## Quick start

```typescript
import { RoClient } from "@ro/client";

const ro = new RoClient({ baseUrl: "https://api.ro-rec.com" });
await ro.login("user@example.com", "password");

const home = await ro.recommendations("home");
console.log(home.items.slice(0, 3).map(i => i.title));

// Streaming chat
await ro.chat.send("what should I watch tonight?", (token) => {
  process.stdout.write(token);
});

// Taste DNA
const dna = await ro.tasteDna();
console.log(dna); // { dna: { pace, emotion, ... }, samples }

// Mixer — overlap zone with a friend
const picks = await ro.mixer(friendUserId);
```

## License

MIT
