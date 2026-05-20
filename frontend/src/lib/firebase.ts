/**
 * lib/firebase.ts — Firebase Client SDK initialization
 */

import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";

const getEnvVar = (key: string): string | undefined => {
  if (typeof process !== "undefined" && process.env && process.env[key]) {
    return process.env[key];
  }
  if (import.meta.env && import.meta.env[key]) {
    return import.meta.env[key];
  }
  const viteKey = key.replace("NEXT_PUBLIC_", "VITE_");
  if (import.meta.env && import.meta.env[viteKey]) {
    return import.meta.env[viteKey];
  }
  return undefined;
};

const firebaseConfig = {
  apiKey: getEnvVar("NEXT_PUBLIC_FIREBASE_API_KEY") || "AIzaSyB-qChNyf7Y1IUSA8FPgJy_gH9zlPi_BeA",
  authDomain: getEnvVar("NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN") || "pharma-ai-agent-dfe40.firebaseapp.com",
  projectId: getEnvVar("NEXT_PUBLIC_FIREBASE_PROJECT_ID") || "pharma-ai-agent-dfe40",
  storageBucket: getEnvVar("NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET") || "pharma-ai-agent-dfe40.firebasestorage.app",
  messagingSenderId: getEnvVar("NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID") || "214315947649",
  appId: getEnvVar("NEXT_PUBLIC_FIREBASE_APP_ID") || "1:214315947649:web:cb27717b7e0f21f4071f80",
  measurementId: getEnvVar("NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID") || "G-BEB0GGJ78E",
};

// Initialize Firebase only if it hasn't been initialized yet
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

export const auth = getAuth(app);
export default app;
