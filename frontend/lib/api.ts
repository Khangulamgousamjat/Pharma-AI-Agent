/**
 * lib/api.ts — Centralized API client for PharmaAgent AI backend
 *
 * All backend API calls are made through this module.
 * This keeps API logic in one place and makes it easy to:
 *   - Change the base URL
 *   - Add global error handling
 *   - Add request interceptors
 *
 * Base URL: NEXT_PUBLIC_API_URL (defaults to http://localhost:8000)
 *
 * @module api
 */

import { authHeader } from "./auth";

/** Base URL loaded from environment variable */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Generic fetch wrapper
// ---------------------------------------------------------------------------

/**
 * Extract a human-readable error message from FastAPI error response.
 * Handles: string detail, array of validation errors, or unknown shapes.
 */
function extractErrorMessage(detail: unknown, fallback: string): string {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0];
        if (typeof first === "object" && first !== null && "msg" in first) {
            return String((first as { msg?: string }).msg) || "Validation error";
        }
    }
    if (typeof detail === "object" && detail !== null) {
        try {
            const str = JSON.stringify(detail);
            if (str && str !== "{}") return str;
        } catch {
            // ignore
        }
    }
    return fallback;
}

/**
 * Generic fetch helper with JSON parsing and error handling.
 *
 * @param path - API path (e.g. '/auth/login')
 * @param options - fetch RequestInit options
 * @returns Parsed JSON response
 * @throws Error with backend error message on non-2xx responses
 */
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${path}`;
    // Merge headers: Content-Type must always be set for JSON body; options can add Authorization etc.
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };
    const res = await fetch(url, {
        ...options,
        headers,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Request failed" }));
        const message = extractErrorMessage(err.detail, `Request failed (HTTP ${res.status})`);
        throw new Error(message);
    }

    return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Authentication API
// ---------------------------------------------------------------------------

export interface RegisterData {
    name: string;
    email: string;
    password: string;
}

export interface LoginData {
    email: string;
    password: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: {
        id: number;
        name: string;
        email: string;
        role: string;
        created_at: string;
    };
}

/**
 * Register a new user account.
 * Automatically logs the user in (returns JWT).
 *
 * @param data - Registration info (name, email, password)
 * @returns Auth response with JWT token and user object
 */
export async function registerUser(data: RegisterData): Promise<AuthResponse> {
    return apiFetch<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

/**
 * Log in an existing user.
 *
 * @param data - Login credentials (email, password)
 * @returns Auth response with JWT token and user object
 */
export async function loginUser(data: LoginData): Promise<AuthResponse> {
    return apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

// ---------------------------------------------------------------------------
// Medicine API
// ---------------------------------------------------------------------------

export interface Medicine {
    id: number;
    name: string;
    stock: number;
    unit: string;
    price: number;
    prescription_required: boolean;
    expiry_date: string | null;
    description: string | null;
}

/**
 * Fetch all medicines from inventory.
 *
 * @returns Array of all medicine records
 */
export async function getMedicines(): Promise<Medicine[]> {
    return apiFetch<Medicine[]>("/medicines");
}

/**
 * Search medicines by name.
 *
 * @param query - Search term
 * @returns Matching medicines
 */
export async function searchMedicines(query: string): Promise<Medicine[]> {
    return apiFetch<Medicine[]>(`/medicines/search?q=${encodeURIComponent(query)}`);
}

/**
 * Get a single medicine by ID.
 *
 * @param id - Medicine primary key
 * @returns Medicine record
 */
export async function getMedicineById(id: number): Promise<Medicine> {
    return apiFetch<Medicine>(`/medicines/${id}`);
}

// ---------------------------------------------------------------------------
// Orders API
// ---------------------------------------------------------------------------

export interface Order {
    id: number;
    user_id: number;
    medicine_id: number;
    quantity: number;
    total_price: number;
    status: string;
    created_at: string;
    medicine: Medicine | null;
}

/**
 * Create a new medicine order (direct, not through agent).
 *
 * @param medicine_id - Medicine to order
 * @param quantity - Number of units
 * @returns Created order record
 */
export async function createOrder(medicine_id: number, quantity: number): Promise<Order> {
    return apiFetch<Order>("/orders/create", {
        method: "POST",
        headers: authHeader(),
        body: JSON.stringify({ medicine_id, quantity }),
    });
}

/**
 * Get all orders for a specific user.
 *
 * @param userId - User ID
 * @returns List of orders
 */
export async function getUserOrders(userId: number): Promise<Order[]> {
    return apiFetch<Order[]>(`/orders/user/${userId}`, {
        headers: authHeader(),
    });
}

/**
 * Get all orders in the system (admin only).
 *
 * @returns All orders
 */
export async function getAllOrders(): Promise<Order[]> {
    return apiFetch<Order[]>("/orders/all", {
        headers: authHeader(),
    });
}

// ---------------------------------------------------------------------------
// Agent API
// ---------------------------------------------------------------------------

export interface AgentChatResponse {
    response: string;
    action: string | null;
    order_id: number | null;
    trace_url: string | null;
}

/**
 * Send a message to the pharmacy AI agent.
 *
 * The agent will parse the message, check medicines, enforce prescription
 * safety rules, and create orders for OTC medicines.
 *
 * @param userId - Authenticated user's ID
 * @param message - Natural language pharmacy request
 * @returns Agent response with action type and optional order ID
 */
export async function sendAgentMessage(
    userId: number,
    message: string
): Promise<AgentChatResponse> {
    const body = {
        user_id: Number(userId),
        message: String(message ?? ""),
    };
    return apiFetch<AgentChatResponse>("/agent/chat", {
        method: "POST",
        headers: authHeader(),
        body: JSON.stringify(body),
    });
}

// ---------------------------------------------------------------------------
// Payment API
// ---------------------------------------------------------------------------

export interface PaymentResponse {
    status: string;
    transaction_id: string;
    message: string;
    order_id: number;
}

/**
 * Process payment for an order (dummy — always succeeds in Phase 1).
 *
 * @param orderId - Order to pay for
 * @param amount - Payment amount in INR
 * @param paymentMethod - Payment method (card/upi/cash)
 * @returns Payment result with transaction ID
 */
export async function processPayment(
    orderId: number,
    amount: number,
    paymentMethod: string = "card"
): Promise<PaymentResponse> {
    return apiFetch<PaymentResponse>("/payment/process", {
        method: "POST",
        body: JSON.stringify({
            order_id: orderId,
            amount,
            payment_method: paymentMethod,
        }),
    });
}

/**
 * Health check — verify backend is running.
 *
 * @returns Health status response
 */
export async function checkHealth(): Promise<{ status: string }> {
    return apiFetch<{ status: string }>("/health");
}

// ===========================================================================
// Phase 3 — Voice, Symptom Checker, Analytics, Webhooks, Settings
// ===========================================================================

// ---------------------------------------------------------------------------
// Voice
// ---------------------------------------------------------------------------

/** Response from POST /agent/voice-message */
export interface VoiceMessageResponse {
    response_text: string;
    action: string | null;
    order_id: number | null;
    tts_url: string | null;
    language: string;
    input_mode: string;
}

/**
 * Send a voice transcript to the pharmacy agent.
 *
 * @param userId - Authenticated user ID
 * @param transcript - STT transcript text
 * @param language - ISO language code (en/hi/mr)
 */
export async function sendVoiceMessage(
    userId: number,
    transcript: string,
    language: string = "en"
): Promise<VoiceMessageResponse> {
    return apiFetch<VoiceMessageResponse>("/agent/voice-message", {
        method: "POST",
        headers: authHeader() as Record<string, string>,
        body: JSON.stringify({ user_id: userId, message: transcript, language }),
    });
}

// ---------------------------------------------------------------------------
// Symptom Checker
// ---------------------------------------------------------------------------

/** A medicine suggested by the symptom agent */
export interface SuggestedMedicine {
    id: number;
    name: string;
    unit: string;
    price: number;
    description?: string;
}

/** Unified response from /symptom/check and /symptom/continue */
export interface SymptomCheckResponse {
    session_id: string;
    level: "ongoing" | "otc" | "doctor" | "emergency";
    question: string | null;
    question_number: number;
    max_questions: number;
    message: string | null;
    disclaimer: string;
    suggested_medicines: SuggestedMedicine[];
    self_care_tips: string[];
    is_complete: boolean;
    error?: string;
}

/**
 * Start a new symptom check session.
 *
 * @param userId - User ID
 * @param symptom - Initial symptom description
 * @param language - ISO language code
 */
export async function startSymptomCheck(
    userId: number,
    symptom: string,
    language: string = "en"
): Promise<SymptomCheckResponse> {
    return apiFetch<SymptomCheckResponse>("/symptom/check", {
        method: "POST",
        body: JSON.stringify({ user_id: userId, initial_symptom: symptom, language }),
    });
}

/**
 * Submit an answer to the current MCQ question.
 *
 * @param sessionId - UUID from startSymptomCheck response
 * @param answer - User's answer text
 */
export async function continueSymptomCheck(
    sessionId: string,
    answer: string
): Promise<SymptomCheckResponse> {
    return apiFetch<SymptomCheckResponse>("/symptom/continue", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, answer }),
    });
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export interface AnalyticsOverview {
    total_orders: number;
    total_revenue: number;
    total_users: number;
    total_medicines: number;
    pending_orders: number;
    fulfilled_orders: number;
    failed_orders: number;
    total_prescriptions: number;
    pending_prescriptions: number;
}

export interface WebhookEvent {
    id: number;
    order_id: number;
    attempt_number: number;
    status: string;
    http_status_code: number | null;
    response_body: string | null;
    created_at: string | null;
}

/** GET /analytics/overview — top-level KPIs */
export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return apiFetch<AnalyticsOverview>("/analytics/overview");
}

/** Top medicine entry from /analytics/medicines */
export interface TopMedicine {
    medicine_id: number;
    medicine_name: string;
    total_quantity: number;
    total_orders: number;
    total_revenue: number;
}

/** Daily order entry from /analytics/orders-over-time */
export interface DailyOrder {
    date: string;
    order_count: number;
    revenue: number;
}


/** GET /analytics/medicines — top N medicines */
export async function getTopMedicines(n: number = 10): Promise<{ medicines: TopMedicine[] }> {
    return apiFetch<{ medicines: TopMedicine[] }>(`/analytics/medicines?n=${n}`);
}

/** GET /analytics/orders-over-time — daily orders */
export async function getOrdersOverTime(days: number = 30): Promise<{ data: DailyOrder[] }> {
    return apiFetch<{ data: DailyOrder[] }>(`/analytics/orders-over-time?days=${days}`);
}

/** GET /analytics/fulfillment — webhook success rate + recent events */
export async function getAnalyticsFulfillment(): Promise<{
    total_attempts: number;
    successful: number;
    failed: number;
    success_rate: number;
    recent_events: WebhookEvent[];
}> {
    return apiFetch("/analytics/fulfillment");
}

// ---------------------------------------------------------------------------
// Webhook
// ---------------------------------------------------------------------------

/**
 * Admin: manually retry a failed fulfillment webhook.
 *
 * @param orderId - Order ID to retry
 */
export async function retriggerWebhook(orderId: number): Promise<{ success: boolean; message: string }> {
    return apiFetch<{ success: boolean; message: string }>(`/webhook/retrigger/${orderId}`, {
        method: "POST",
        headers: authHeader() as Record<string, string>,
    });
}

// ---------------------------------------------------------------------------
// Settings / Preferences
// ---------------------------------------------------------------------------

export interface UserPreferences {
    ui_theme: "dark" | "light";
    preferred_language: string;
}

/**
 * Update user UI preferences (theme + language) in the database.
 *
 * @param userId - Authenticated user ID
 * @param preferences - New preference values
 */
export async function updatePreferences(
    userId: number,
    preferences: UserPreferences
): Promise<UserPreferences> {
    return apiFetch<UserPreferences>(
        `/settings/preferences?user_id=${userId}`,
        {
            method: "PUT",
            headers: authHeader() as Record<string, string>,
            body: JSON.stringify(preferences),
        }
    );
}

/**
 * Fetch current user preferences from database.
 *
 * @param userId - User ID
 */
export async function getPreferences(userId: number): Promise<UserPreferences> {
    return apiFetch<UserPreferences>(`/settings/preferences?user_id=${userId}`);
}


// ---------------------------------------------------------------------------
// Phase 2: Prescription API
// ---------------------------------------------------------------------------

export interface ExtractedMedicine {
    medicine_name: string | null;
    dosage: string | null;
    quantity: number | null;
    raw_text: string | null;
    confidence: string | null;
}

export interface Prescription {
    id: number;
    user_id: number;
    image_url: string;
    extracted_text: string | null;
    extracted_medicine: string | null; // JSON string
    verified: boolean;
    verified_by: number | null;
    created_at: string | null;
}

export interface PrescriptionUploadResponse {
    prescription_id: number;
    message: string;
    extracted: ExtractedMedicine;
    verified: boolean;
}

/**
 * Upload a prescription image for Vision Agent processing.
 *
 * Uses multipart/form-data to send the image file and user_id.
 * Returns vision-extracted medicine data + prescription ID.
 *
 * @param userId - User uploading the prescription
 * @param file - Image file (jpg/png/webp)
 * @returns Upload response with extracted medicine info
 */
export async function uploadPrescription(
    userId: number,
    file: File
): Promise<PrescriptionUploadResponse> {
    const formData = new FormData();
    formData.append("user_id", String(userId));
    formData.append("file", file);

    const url = `${BASE_URL}/prescriptions/upload`;
    const res = await fetch(url, {
        method: "POST",
        // Do NOT set Content-Type — browser sets it with boundary for multipart
        headers: authHeader(),
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

/**
 * Get all prescriptions for a user.
 *
 * @param userId - User ID
 * @returns Array of prescription records
 */
export async function getUserPrescriptions(userId: number): Promise<Prescription[]> {
    return apiFetch<Prescription[]>(`/prescriptions/user/${userId}`, {
        headers: authHeader(),
    });
}

/**
 * Get all pending (unverified) prescriptions — pharmacist queue.
 *
 * @returns Unverified prescriptions, oldest first
 */
export async function getPendingPrescriptions(): Promise<Prescription[]> {
    return apiFetch<Prescription[]>("/prescriptions/pending", {
        headers: authHeader(),
    });
}

/**
 * Verify a prescription (pharmacist action).
 * Requires pharmacist/admin JWT.
 *
 * @param prescriptionId - ID of prescription to verify
 * @param token - Pharmacist JWT token
 * @returns Updated prescription record
 */
export async function verifyPrescription(
    prescriptionId: number,
    token: string
): Promise<Prescription> {
    return apiFetch<Prescription>(`/pharmacist/prescriptions/${prescriptionId}/verify`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
    });
}

// ---------------------------------------------------------------------------
// Phase 2: Refill Alerts API
// ---------------------------------------------------------------------------

export interface RefillAlert {
    id: number;
    user_id: number;
    medicine_id: number;
    predicted_refill_date: string | null;
    days_supply: number;
    status: string;
    created_at: string | null;
    medicine_name: string | null;
    medicine_unit: string | null;
}

export interface RefillPredictionResponse {
    user_id: number;
    alerts_created: number;
    alerts_updated: number;
    message: string;
}

/**
 * Get all refill alerts for a user.
 *
 * @param userId - User ID
 * @returns Array of refill alerts (soonest first)
 */
export async function getRefillAlerts(userId: number): Promise<RefillAlert[]> {
    return apiFetch<RefillAlert[]>(`/refill-alerts/user/${userId}`, {
        headers: authHeader(),
    });
}

/**
 * Trigger refill prediction for a user.
 * Analyzes their order history and creates alerts for medicines due soon.
 *
 * @param userId - User to run prediction for
 * @returns Summary of alerts created/updated
 */
export async function runRefillPrediction(userId: number): Promise<RefillPredictionResponse> {
    return apiFetch<RefillPredictionResponse>("/refill-alerts/run-prediction", {
        method: "POST",
        headers: authHeader(),
        body: JSON.stringify({ user_id: userId }),
    });
}
