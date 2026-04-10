/**
 * lib/auth.ts — JWT token and user session management
 *
 * Handles storing, retrieving, and clearing the authentication token
 * from localStorage. Also provides helpers to decode the token payload.
 *
 * @module auth
 */

/** User data stored in JWT payload and localStorage */
export interface User {
  id: number;
  name: string;
  email: string;
  role: "user" | "admin" | "pharmacist"; // Phase 2: added pharmacist role
}

const TOKEN_KEY = "pharmaagent_token";
const USER_KEY = "pharmaagent_user";

/**
 * Save authentication token and user data to localStorage.
 * Called after successful login or registration.
 *
 * @param token - JWT access token string
 * @param user - User object to persist
 */
export function saveAuth(token: string, user: User): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * Retrieve the stored JWT token.
 *
 * @returns JWT string or null if not logged in
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Retrieve the stored user object.
 *
 * @returns User object or null if not logged in
 */
export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

/**
 * Check if the user is currently authenticated.
 *
 * @returns true if a token exists in localStorage
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * Check if the current user has admin role.
 *
 * @returns true if logged-in user is an admin
 */
export function isAdmin(): boolean {
  const user = getUser();
  return user?.role === "admin";
}

/**
 * Clear all auth data from localStorage (logout).
 */
export function clearAuth(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

/**
 * Build Authorization header object for API requests.
 *
 * @returns Header object with Bearer token, or empty object if not logged in
 */
export function authHeader(): Record<string, string> {
  const token = getToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
