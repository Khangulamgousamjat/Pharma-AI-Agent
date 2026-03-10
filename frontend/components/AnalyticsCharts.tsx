"use client";

/**
 * components/AnalyticsCharts.tsx — Admin analytics charts using Recharts.
 *
 * Phase 3: Visualizes KPI data from the /analytics/* endpoints.
 *
 * Charts included:
 *   - BarChart: Top medicines by order quantity
 *   - LineChart: Daily orders over time
 *   - PieChart: Webhook fulfillment status distribution
 *
 * Accessibility:
 *   - Charts wrapped in figure/figcaption for screen readers
 *   - Color contrast > 4.5:1 on dark background
 *   - Keyboard-focusable legend items
 *
 * @param topMedicines - Top medicines data from /analytics/medicines
 * @param ordersOverTime - Daily orders from /analytics/orders-over-time
 * @param webhookStats - Webhook stats from /analytics/fulfillment
 */

import { useMemo } from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    LineChart,
    Line,
    PieChart,
    Pie,
    Cell,
    Legend,
} from "recharts";
import type { TopMedicine, DailyOrder } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// TopMedicine and DailyOrder are imported from lib/api.ts
export type { TopMedicine, DailyOrder };

export interface WebhookStats {
    total_attempts: number;
    successful: number;
    failed: number;
    success_rate: number;
}

// ---------------------------------------------------------------------------
// Color palette — high contrast, glassmorphism-compatible
// ---------------------------------------------------------------------------
const CHART_COLORS = {
    primary: "#818cf8",   // indigo-400
    secondary: "#34d399", // emerald-400
    danger: "#f87171",    // red-400
    warning: "#fbbf24",   // amber-400
    violet: "#a78bfa",    // violet-400
};

const PIE_COLORS = [CHART_COLORS.secondary, CHART_COLORS.danger];

// ---------------------------------------------------------------------------
// Shared Recharts props
// ---------------------------------------------------------------------------
const AXIS_STYLE = {
    fill: "#94a3b8",   // slate-400
    fontSize: 11,
};
const GRID_STYLE = {
    stroke: "rgba(255,255,255,0.05)",
};
const TOOLTIP_STYLE = {
    backgroundColor: "rgba(15,23,42,0.95)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: "12px",
    color: "#f1f5f9",
    fontSize: "12px",
};

// ---------------------------------------------------------------------------
// Top Medicines Bar Chart
// ---------------------------------------------------------------------------
interface TopMedicinesChartProps {
    data: TopMedicine[];
}

export function TopMedicinesChart({ data }: TopMedicinesChartProps) {
    const chartData = useMemo(
        () =>
            data.slice(0, 8).map((d) => ({
                name: d.medicine_name.split(" ")[0], // First word for brevity
                qty: d.total_quantity,
                revenue: d.total_revenue,
                fullName: d.medicine_name,
            })),
        [data]
    );

    if (!data.length) {
        return (
            <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
                No order data yet
            </div>
        );
    }

    return (
        <figure aria-labelledby="top-meds-caption">
            <figcaption id="top-meds-caption" className="sr-only">
                Bar chart showing top medicines by order quantity
            </figcaption>
            <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" {...GRID_STYLE} />
                    <XAxis dataKey="name" tick={AXIS_STYLE} />
                    <YAxis tick={AXIS_STYLE} />
                    <Tooltip
                        contentStyle={TOOLTIP_STYLE}
                        formatter={(value, name) => [
                            name === "qty" ? `${value} units` : `₹${value}`,
                            name === "qty" ? "Quantity" : "Revenue",
                        ]}
                        labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                    />
                    <Bar dataKey="qty" fill={CHART_COLORS.primary} radius={[4, 4, 0, 0]} name="qty" />
                </BarChart>
            </ResponsiveContainer>
        </figure>
    );
}

// ---------------------------------------------------------------------------
// Orders Over Time Line Chart
// ---------------------------------------------------------------------------
interface OrdersLineChartProps {
    data: DailyOrder[];
}

export function OrdersLineChart({ data }: OrdersLineChartProps) {
    const chartData = useMemo(
        () =>
            data.map((d) => ({
                ...d,
                displayDate: d.date.slice(5), // MM-DD for brevity
            })),
        [data]
    );

    if (!data.length) {
        return (
            <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
                No order history yet
            </div>
        );
    }

    return (
        <figure aria-labelledby="orders-time-caption">
            <figcaption id="orders-time-caption" className="sr-only">
                Line chart showing daily order counts over time
            </figcaption>
            <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" {...GRID_STYLE} />
                    <XAxis dataKey="displayDate" tick={AXIS_STYLE} />
                    <YAxis tick={AXIS_STYLE} />
                    <Tooltip
                        contentStyle={TOOLTIP_STYLE}
                        formatter={(value, name) => [
                            name === "order_count" ? `${value} orders` : `₹${value}`,
                            name === "order_count" ? "Orders" : "Revenue",
                        ]}
                        labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Line
                        type="monotone"
                        dataKey="order_count"
                        stroke={CHART_COLORS.primary}
                        strokeWidth={2}
                        dot={{ fill: CHART_COLORS.primary, r: 3 }}
                        name="order_count"
                        activeDot={{ r: 5 }}
                    />
                    <Line
                        type="monotone"
                        dataKey="revenue"
                        stroke={CHART_COLORS.secondary}
                        strokeWidth={2}
                        dot={false}
                        strokeDasharray="4 2"
                        name="revenue"
                    />
                    <Legend
                        formatter={(value) => (value === "order_count" ? "Orders" : "Revenue (₹)")}
                        wrapperStyle={{ fontSize: 11, color: "#94a3b8" }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </figure>
    );
}

// ---------------------------------------------------------------------------
// Webhook Status Pie Chart
// ---------------------------------------------------------------------------
interface WebhookPieChartProps {
    stats: WebhookStats;
}

export function WebhookPieChart({ stats }: WebhookPieChartProps) {
    const pieData = [
        { name: "Successful", value: stats.successful },
        { name: "Failed", value: stats.failed },
    ].filter((d) => d.value > 0);

    if (stats.total_attempts === 0) {
        return (
            <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
                No webhook events yet
            </div>
        );
    }

    return (
        <figure aria-labelledby="webhook-pie-caption">
            <figcaption id="webhook-pie-caption" className="sr-only">
                Pie chart showing webhook fulfillment success vs failure ratio
            </figcaption>
            <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                    <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="value"
                    >
                        {pieData.map((_, index) => (
                            <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
                </PieChart>
            </ResponsiveContainer>
            <p className="text-center text-slate-600 dark:text-slate-400 text-xs mt-1">
                Success rate: <span className="text-emerald-400 font-bold">{stats.success_rate}%</span>
            </p>
        </figure>
    );
}
