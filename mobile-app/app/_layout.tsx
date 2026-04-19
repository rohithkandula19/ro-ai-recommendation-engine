import { Stack } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StatusBar } from "expo-status-bar";

const qc = new QueryClient();

export default function RootLayout() {
  return (
    <QueryClientProvider client={qc}>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerStyle: { backgroundColor: "#0b0b0b" }, headerTintColor: "#fff" }}>
        <Stack.Screen name="index" options={{ title: "RO" }} />
        <Stack.Screen name="browse/[id]" options={{ title: "Detail" }} />
        <Stack.Screen name="chat" options={{ title: "Ask RO" }} />
      </Stack>
    </QueryClientProvider>
  );
}
