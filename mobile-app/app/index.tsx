import { FlatList, Image, Pressable, Text, View } from "react-native";
import { Link } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { RoClient } from "@ro/client";
import * as SecureStore from "expo-secure-store";
import Constants from "expo-constants";

const API = (Constants.expoConfig?.extra as any)?.apiUrl ?? "http://localhost:8000";
const ro = new RoClient({ baseUrl: API });

export default function Home() {
  const { data } = useQuery({
    queryKey: ["home"],
    queryFn: async () => {
      const tok = await SecureStore.getItemAsync("ro-token");
      if (tok) ro.setToken(tok);
      return ro.recommendations("home", 20);
    },
  });

  return (
    <View style={{ flex: 1, backgroundColor: "#0b0b0b" }}>
      <Text style={{ color: "#E50914", fontSize: 32, fontWeight: "900", padding: 16 }}>RO</Text>
      <Text style={{ color: "#fff", fontSize: 24, fontWeight: "700", paddingHorizontal: 16, marginBottom: 8 }}>
        Recommended for you
      </Text>
      <FlatList
        horizontal
        data={data?.items ?? []}
        keyExtractor={(it) => it.id}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 12 }}
        renderItem={({ item }) => (
          <Link href={`/browse/${item.id}`} asChild>
            <Pressable style={{ width: 140 }}>
              {item.thumbnail_url && (
                <Image
                  source={{ uri: item.thumbnail_url }}
                  style={{ width: 140, height: 210, borderRadius: 8, backgroundColor: "#222" }}
                />
              )}
              <Text numberOfLines={1} style={{ color: "#fff", marginTop: 6, fontSize: 13, fontWeight: "600" }}>
                {item.title}
              </Text>
              <Text style={{ color: "#10b981", fontSize: 11 }}>{Math.round(item.match_score * 100)}% match</Text>
            </Pressable>
          </Link>
        )}
      />
      <Link href="/chat" asChild>
        <Pressable style={{ position: "absolute", bottom: 30, right: 20, backgroundColor: "#E50914",
          width: 56, height: 56, borderRadius: 28, justifyContent: "center", alignItems: "center" }}>
          <Text style={{ fontSize: 24 }}>💬</Text>
        </Pressable>
      </Link>
    </View>
  );
}
