# PharmaAgent AI — Frontend README

## Overview
Next.js 15 frontend with TypeScript + TailwindCSS using a glassmorphism dark UI design.

## Tech Stack
- **Next.js 15** — App Router
- **TypeScript**
- **TailwindCSS** — Utility-first CSS
- **Custom glassmorphism CSS** — Glass panels, blur, gradients

## Setup

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment
```bash
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run development server
```bash
npm run dev
```
Visit http://localhost:3000

## Pages

| Route | Description |
|-------|-------------|
| /login | Email/password login |
| /register | Create new account |
| /dashboard | Order overview and stats |
| /chat | AI pharmacy chat interface |
| /admin | Admin inventory + orders (admin only) |

## Key Components
- `GlassCard` — Reusable frosted glass panel
- `Navbar` — Top navigation with auth state
- `ChatInterface` — Full AI chat with typing indicator and payment

## Design System
Glassmorphism variables defined in `app/globals.css`:
- `.glass-card` — Backdrop blur + transparent bg
- `.input-glass` — Styled form inputs
- `.btn-primary` — Gradient purple button
- `.chat-bubble-user/agent` — Chat message bubbles
- `.badge-success/warning/error` — Status badges
