"use client";

import Link from "next/link";
import { 
  Bot, 
  Camera, 
  Mic, 
  Stethoscope, 
  TrendingUp, 
  ShieldCheck, 
  ArrowRight,
  Github,
  CheckCircle2
} from "lucide-react";

/** 
 * Root Landing Page — PharmaAgent AI
 * 
 * A high-conversion landing page featuring:
 * - Stunning hero section with glassmorphism
 * - Interactive feature grid
 * - Integrated CTA for login/register
 */
export default function LandingPage() {
  return (
    <div className="min-h-screen text-[var(--text-color)] selection:bg-indigo-500/30">
      
      {/* --- Sticky Navigation --- */}
      <nav className="navbar sticky top-0 z-[100] border-b border-white/5 bg-[#0f0c29]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg shadow-lg shadow-indigo-500/20">
              💉
            </div>
            <span className="font-bold text-xl gradient-text tracking-tight">
              PharmaAgent AI
            </span>
          </div>
          
          <div className="flex items-center gap-6">
            <Link href="https://github.com" className="text-slate-400 hover:text-white transition-colors">
              <Github size={20} />
            </Link>
            <Link href="/login" className="btn-primary text-sm py-2 px-5 rounded-full">
              Sign In
            </Link>
          </div>
        </div>
      </nav>

      <main>
        {/* --- Hero Section --- */}
        <section className="relative pt-24 pb-20 overflow-hidden">
          {/* Background Glows */}
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-indigo-600/20 blur-[120px] rounded-full pointer-events-none" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-violet-600/20 blur-[100px] rounded-full pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold mb-8 animate-fade-in">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
              </span>
              NEXT-GEN PHARMACY SOLUTIONS
            </div>
            
            <h1 className="text-5xl md:text-7xl font-black mb-8 leading-tight tracking-tight">
              Your <span className="gradient-text">AI-Powered</span> <br />
              Pharmacy Assistant
            </h1>
            
            <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed font-medium">
              Revolutionizing healthcare with intelligent medication management, 
              vision-powered prescription scanning, and hands-free voice interactions.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register" className="btn-primary flex items-center gap-2 group text-lg px-8 py-4 w-full sm:w-auto">
                Get Started Free
                <ArrowRight className="transition-transform group-hover:translate-x-1" size={20} />
              </Link>
              <Link href="/login" className="btn-secondary text-lg px-8 py-4 w-full sm:w-auto">
                View Demo
              </Link>
            </div>

          </div>
        </section>

        {/* --- Features Grid --- */}
        <section className="py-24 bg-white/[0.02]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">The Future of Pharmacy Tech</h2>
              <p className="text-slate-400">Everything you need to manage medications, safely and efficiently.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="glass-card p-8 group">
                <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 mb-6 group-hover:scale-110 transition-transform">
                  <Bot size={28} />
                </div>
                <h3 className="text-xl font-bold mb-3">AI Pharmacist Chat</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Interative multilingual agent that answers medication queries, checks contraindications, and creates smart orders.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="glass-card p-8 group">
                <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center text-violet-400 mb-6 group-hover:scale-110 transition-transform">
                  <Camera size={28} />
                </div>
                <h3 className="text-xl font-bold mb-3">Vision Prescription Scan</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Advanced vision AI that extracts medicine names, dosages, and quantities directly from handwritten or digital prescriptions.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="glass-card p-8 group">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 mb-6 group-hover:scale-110 transition-transform">
                  <Mic size={28} />
                </div>
                <h3 className="text-xl font-bold mb-3">Voice-First Interaction</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Order medicines or check status using natural voice commands. Perfect for accessibility and quick interactions.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="glass-card p-8 group">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-400 mb-6 group-hover:scale-110 transition-transform">
                  <Stethoscope size={28} />
                </div>
                <h3 className="text-xl font-bold mb-3">Smart Symptom Triage</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Multi-step MCQ symptom checker powered by AI to provide safety-first triage and OTC medication recommendations.
                </p>
              </div>

              {/* Feature 5 */}
              <div className="glass-card p-8 group">
                <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400 mb-6 group-hover:scale-110 transition-transform">
                  <TrendingUp size={28} />
                </div>
                <h3 className="text-xl font-bold mb-3">Real-time Analytics</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Comprehensive dashboard for pharmacists and admins to track orders, inventory, and fulfillment metrics.
                </p>
              </div>

              {/* Feature 6 */}
              <div className="glass-card p-8 group">
                <div className="w-12 h-12 rounded-xl bg-rose-500/20 flex items-center justify-center text-rose-400 mb-6 group-hover:scale-110 transition-transform">
                  <ShieldCheck size={28} />
                </div>
                <h3 className="text-xl font-bold mb-3">Pharmacy Safety First</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Automated checks for prescription-only medicines and built-in emergency escalations for red-flag symptoms.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* --- Stats Section --- */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-4xl font-black gradient-text mb-2">99%</div>
                <div className="text-slate-500 text-sm uppercase tracking-widest font-bold">Accuracy</div>
              </div>
              <div>
                <div className="text-4xl font-black gradient-text mb-2">3+</div>
                <div className="text-slate-500 text-sm uppercase tracking-widest font-bold">Languages</div>
              </div>
              <div>
                <div className="text-4xl font-black gradient-text mb-2">0ms</div>
                <div className="text-slate-500 text-sm uppercase tracking-widest font-bold">Latency Triage</div>
              </div>
              <div>
                <div className="text-4xl font-black gradient-text mb-2">Secure</div>
                <div className="text-slate-500 text-sm uppercase tracking-widest font-bold">Compliance</div>
              </div>
            </div>
          </div>
        </section>

        {/* --- CTA Section --- */}
        <section className="py-24 relative overflow-hidden">
          <div className="absolute inset-0 bg-indigo-600/10 blur-[150px] pointer-events-none" />
          <div className="max-w-4xl mx-auto px-6 text-center">
            <h2 className="text-4xl font-bold mb-6">Ready to upgrade your pharmacy experience?</h2>
            <p className="text-slate-400 mb-10 text-lg">Join thousands of users who trust PharmaAgent AI for their health management.</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register" className="btn-primary px-10 py-4 text-lg w-full sm:w-auto">
                Create Account
              </Link>
              <Link href="/login" className="btn-secondary px-10 py-4 text-lg w-full sm:w-auto">
                Sign In
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* --- Footer --- */}
      <footer className="py-20 border-t border-white/5 bg-black/40 backdrop-blur-md relative overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-indigo-600/5 blur-[120px] rounded-full pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
            
            {/* Branding Column */}
            <div className="space-y-6">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg">
                  💉
                </div>
                <span className="font-bold text-xl text-white">
                  PharmaAgent AI
                </span>
              </div>
              <p className="text-slate-500 text-sm leading-relaxed max-w-xs">
                The next generation of pharmaceutical management, powered by advanced vision, voice, and chat AI agents.
              </p>
              <div className="flex items-center gap-4">
                <Link href="https://github.com/Khangulamgousamjat" className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition-all border border-white/10">
                  <Github size={18} />
                </Link>
                <Link href="#" className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-400 hover:bg-white/10 hover:text-indigo-400 transition-all border border-white/10">
                  <span className="font-bold text-xs">in</span>
                </Link>
              </div>
            </div>

            {/* Platform Column */}
            <div>
              <h4 className="text-white font-bold mb-6 text-sm uppercase tracking-widest">Platform</h4>
              <ul className="space-y-4 text-sm text-slate-500">
                <li><Link href="/chat" className="hover:text-indigo-400 transition-colors">AI Chatbot</Link></li>
                <li><Link href="/vision" className="hover:text-indigo-400 transition-colors">Vision Agency</Link></li>
                <li><Link href="/voice" className="hover:text-indigo-400 transition-colors">Voice Orders</Link></li>
                <li><Link href="/dashboard" className="hover:text-indigo-400 transition-colors">Dashboard</Link></li>
              </ul>
            </div>

            {/* Resources Column */}
            <div>
              <h4 className="text-white font-bold mb-6 text-sm uppercase tracking-widest">Resources</h4>
              <ul className="space-y-4 text-sm text-slate-500">
                <li><Link href="/symptom" className="hover:text-indigo-400 transition-colors">Symptom Triage</Link></li>
                <li><Link href="/refill-alerts" className="hover:text-indigo-400 transition-colors">Refill Alerts</Link></li>
                <li><Link href="#" className="hover:text-indigo-400 transition-colors">API Documentation</Link></li>
                <li><Link href="#" className="hover:text-indigo-400 transition-colors">Community</Link></li>
              </ul>
            </div>

            {/* Legal Column */}
            <div>
              <h4 className="text-white font-bold mb-6 text-sm uppercase tracking-widest">Organization</h4>
              <ul className="space-y-4 text-sm text-slate-500">
                <li><Link href="#" className="hover:text-indigo-400 transition-colors">About Gous Khan</Link></li>
                <li><Link href="#" className="hover:text-indigo-400 transition-colors">Privacy Policy</Link></li>
                <li><Link href="#" className="hover:text-indigo-400 transition-colors">Terms of Service</Link></li>
                <li><Link href="#" className="hover:text-indigo-400 transition-colors">Contact Support</Link></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="text-slate-500 text-sm font-medium">
              © {new Date().getFullYear()} <span className="text-white">PharmaAgent AI</span>. All rights reserved.
            </div>
            
            <div className="flex items-center gap-2 text-slate-400 text-sm font-semibold">
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                Made by <span className="text-indigo-400">Gous Khan</span>
              </span>
            </div>

            <div className="text-slate-500 text-xs flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Built with precision in India
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
