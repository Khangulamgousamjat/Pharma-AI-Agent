/**
 * lib/auth.ts — Firebase Auth and user session management
 *
 * Wraps Firebase Auth to provide simple get/set functions,
 * and maintains backward compatibility with the existing React components.
 */

import { auth } from "./firebase";
import { onAuthStateChanged, User as FirebaseUser, signOut } from "firebase/auth";

/** User data interface updated for Firebase (string IDs) */
export interface User {
  id: string; // Firebase UID
  name: string;
  email: string;
  role: "user" | "admin" | "pharmacist";
}

let currentUser: User | null = null;
let currentToken: string | null = null;

// The backend will still manage the `role` and `name` in the Firestore `users` collection.
// When the user logs in, we should ideally fetch their profile. For simplicity in this local module,
// we parse it from the localStorage fallback or wait for components to fetch from `/auth/me`.
const USER_KEY = "pharmaagent_user";

if (typeof window !== "undefined") {
    // Basic persistent role storage to avoid UI flashing before Firebase init
    const raw = localStorage.getItem(USER_KEY);
    if (raw) {
        try { currentUser = JSON.parse(raw); } catch { }
    }
}

/**
 * Save user data to localStorage (useful for roles).
 */
export function saveUserLocal(user: User): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    currentUser = user;
  }
}

/**
 * Retrieve the stored JWT token synchronously.
 * Note: Firebase tokens expire after 1 hour, so we rely on the observer
 * to keep it fresh, but for sync API calls we return the last known token.
 */
export function getToken(): string | null {
  return currentToken;
}

/**
 * Retrieve the stored user object.
 */
export function getUser(): User | null {
  return currentUser;
}

/**
 * Check if the user is currently authenticated.
 */
export function isAuthenticated(): boolean {
  return !!currentUser || !!currentToken;
}

/**
 * Check if the current user has admin role.
 */
export function isAdmin(): boolean {
  return currentUser?.role === "admin";
}

/**
 * Clear auth manually
 */
export async function clearAuth(): Promise<void> {
  await signOut(auth);
  currentUser = null;
  currentToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem(USER_KEY);
  }
}

/**
 * Build Authorization header object for API requests.
 */
export function authHeader(): Record<string, string> {
  if (!currentToken) return {};
  return { Authorization: `Bearer ${currentToken}` };
}

// ---------------------------------------------------------------------------
// Firebase Auth Observer Setup
// ---------------------------------------------------------------------------
if (typeof window !== "undefined") {
    onAuthStateChanged(auth, async (user: FirebaseUser | null) => {
        if (user) {
            currentToken = await user.getIdToken();
            if (!currentUser || currentUser.id !== user.uid) {
                // Set basic info until profile is fetched
                currentUser = {
                    id: user.uid,
                    name: user.displayName || user.email?.split('@')[0] || "User",
                    email: user.email || "",
                    role: currentUser?.role || "user"
                };
            }
        } else {
            currentToken = null;
            currentUser = null;
            localStorage.removeItem(USER_KEY);
        }
    });
}
