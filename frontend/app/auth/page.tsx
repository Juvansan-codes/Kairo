"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowRight,
  Eye,
  EyeOff,
  Mail,
  Lock,
  User,
  AlertCircle,
  CheckCircle2,
  Database,
  Info,
  ShieldCheck,
  Layers,
  Compass,
  Sparkles,
  Check,
  ArrowLeft,
  Building2,
  Cpu,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

type AuthMode = "login" | "signup" | "forgot";

function AuthForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";

  const {
    signInWithEmail,
    signUpWithEmail,
    signInWithGoogle,
    signInWithGithub,
    resetPassword,
    demoLogin,
    isConfigured,
  } = useAuth();

  const [mode, setMode] = useState<AuthMode>("login");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<"google" | "github" | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);

  // Feedback state
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Password strength calculation
  const hasMinLength = password.length >= 8;
  const hasNumberOrSymbol = /[0-9!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password);
  const hasUppercase = /[A-Z]/.test(password);
  const strengthScore = [hasMinLength, hasNumberOrSymbol, hasUppercase].filter(Boolean).length;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const { error } = await signInWithEmail(email, password);
        if (error) {
          setErrorMsg(error.message || "Failed to log in. Please check your credentials.");
          setLoading(false);
          return;
        }
        router.push(redirectTo);
      } else if (mode === "signup") {
        if (!hasMinLength) {
          setErrorMsg("Password must be at least 8 characters long.");
          setLoading(false);
          return;
        }

        const { error, needsEmailConfirmation } = await signUpWithEmail(
          email,
          password,
          name
        );
        if (error) {
          setErrorMsg(error.message || "Failed to sign up. Please try again.");
          setLoading(false);
          return;
        }

        if (needsEmailConfirmation) {
          setSuccessMsg(
            "Account created! Please check your inbox to confirm your email before signing in."
          );
          setLoading(false);
          return;
        }

        router.push(redirectTo);
      } else if (mode === "forgot") {
        const { error } = await resetPassword(email);
        if (error) {
          setErrorMsg(error.message || "Failed to send reset email.");
          setLoading(false);
          return;
        }
        setSuccessMsg(
          `Password reset instructions have been dispatched to ${email}.`
        );
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred.";
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: "google" | "github") => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setOauthLoading(provider);
    try {
      const { error } =
        provider === "google" ? await signInWithGoogle() : await signInWithGithub();

      if (error) {
        setErrorMsg(error.message || `${provider} authentication failed.`);
        setOauthLoading(null);
        return;
      }

      if (!isConfigured) {
        // In preview/demo mode, route immediately
        router.push(redirectTo);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Authentication error.";
      setErrorMsg(message);
      setOauthLoading(null);
    }
  };

  const handleQuickDemo = (role: string, demoEmail: string) => {
    demoLogin(demoEmail, role);
    router.push(redirectTo);
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex bg-white">
      {/* ── Left Branding & Architectural Visual Canvas ── */}
      <div className="hidden lg:flex lg:w-1/2 bg-kairo-black relative overflow-hidden flex-col justify-between p-12 text-white">
        {/* Dynamic Architectural Grid Background */}
        <div
          className="absolute inset-0 opacity-[0.06] pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)
            `,
            backgroundSize: "32px 32px",
          }}
        />

        {/* Diagonal Blueprint Glow Effect */}
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-kairo-orange/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 right-0 w-80 h-80 bg-kairo-orange/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header */}
        <div className="relative z-10">
          <Link href="/" className="inline-flex items-center gap-2 group mb-12">
            <span className="w-3 h-3 rounded-sm bg-kairo-orange transition-transform group-hover:scale-110" />
            <span className="text-xl font-bold tracking-tight text-white">
              KAIRO
            </span>
            <span className="ml-2 text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border border-kairo-gray-800 text-kairo-gray-400 uppercase">
              v2.4 Core
            </span>
          </Link>

          <div className="space-y-4 max-w-lg">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-kairo-orange/10 border border-kairo-orange/20 text-kairo-orange text-xs font-mono tracking-wide">
              <Compass className="w-3.5 h-3.5" />
              <span>METRIC-AWARE SPATIAL ENGINE</span>
            </div>

            <h2 className="text-4xl xl:text-5xl font-bold tracking-tight leading-[1.15] text-white">
              From 2D blueprints to <br />
              <span className="text-kairo-orange">living spatial models.</span>
            </h2>

            <p className="text-kairo-gray-400 text-sm leading-relaxed max-w-md pt-2">
              Kairo parses architectural plans, preserves metric wall thickness, and generates
              interactive, collision-ready 3D web environments with Sub-millimeter precision.
            </p>
          </div>
        </div>

        {/* Mid Preview Card: Live Spatial Metadata */}
        <div className="relative z-10 my-8">
          <div className="border border-kairo-gray-800 bg-kairo-gray-900/60 backdrop-blur-md rounded-kairo p-5 space-y-4 shadow-2xl">
            {/* Header with blueprint coordinates */}
            <div className="flex items-center justify-between text-xs pb-3 border-b border-kairo-gray-800/80">
              <div className="flex items-center gap-2 text-kairo-gray-300 font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>PIPELINE STATUS: READY</span>
              </div>
              <span className="font-mono text-kairo-gray-500 text-[11px]">
                COORD: 37°46&apos;N 122°25&apos;W
              </span>
            </div>

            {/* Interactive Blueprint Vector Mock */}
            <div className="relative h-28 w-full bg-black/40 rounded border border-kairo-gray-800/60 p-3 overflow-hidden">
              <svg
                viewBox="0 0 340 90"
                className="w-full h-full text-kairo-orange/60"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Structural Walls */}
                <rect x="15" y="10" width="310" height="70" stroke="currentColor" strokeWidth="1.5" />
                <line x1="120" y1="10" x2="120" y2="80" stroke="currentColor" strokeWidth="1.2" />
                <line x1="120" y1="45" x2="230" y2="45" stroke="currentColor" strokeWidth="1.2" />
                <line x1="230" y1="10" x2="230" y2="80" stroke="currentColor" strokeWidth="1.2" />

                {/* Door Swing Arcs */}
                <path d="M 120 25 A 20 20 0 0 1 140 45" stroke="#F15A24" strokeWidth="1" strokeDasharray="2 2" />
                <path d="M 230 65 A 18 18 0 0 0 212 80" stroke="#F15A24" strokeWidth="1" strokeDasharray="2 2" />

                {/* Dimension Ticks & Callouts */}
                <text x="50" y="32" fill="#888888" fontSize="8" fontFamily="monospace">LIVING (6.2m × 4.8m)</text>
                <text x="145" y="28" fill="#888888" fontSize="8" fontFamily="monospace">MASTER BED</text>
                <text x="145" y="65" fill="#888888" fontSize="8" fontFamily="monospace">BATH / UTILITY</text>
                <text x="250" y="48" fill="#F15A24" fontSize="8" fontFamily="monospace">STUDIO 3D</text>

                {/* Corner measurement crosshairs */}
                <circle cx="15" cy="10" r="2.5" fill="#F15A24" />
                <circle cx="325" cy="10" r="2.5" fill="#F15A24" />
                <circle cx="325" cy="80" r="2.5" fill="#F15A24" />
                <circle cx="15" cy="80" r="2.5" fill="#F15A24" />
              </svg>

              {/* Floating precision tag */}
              <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-kairo-orange/20 border border-kairo-orange/30 text-[9px] font-mono text-kairo-orange">
                SCALE: 25.4 mm/px
              </div>
            </div>

            {/* Feature Pills */}
            <div className="grid grid-cols-3 gap-2 pt-1 text-[11px] text-kairo-gray-400 font-mono">
              <div className="flex items-center gap-1.5 p-2 rounded bg-kairo-gray-900/40 border border-kairo-gray-800">
                <Layers className="w-3.5 h-3.5 text-kairo-orange" />
                <span>Multi-Floor GLB</span>
              </div>
              <div className="flex items-center gap-1.5 p-2 rounded bg-kairo-gray-900/40 border border-kairo-gray-800">
                <Cpu className="w-3.5 h-3.5 text-kairo-orange" />
                <span>GPU Raycast</span>
              </div>
              <div className="flex items-center gap-1.5 p-2 rounded bg-kairo-gray-900/40 border border-kairo-gray-800">
                <ShieldCheck className="w-3.5 h-3.5 text-kairo-orange" />
                <span>RLS Protected</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Trust & Security Assurance */}
        <div className="relative z-10 flex items-center justify-between text-xs text-kairo-gray-500 pt-4 border-t border-kairo-gray-800/80">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-kairo-orange" />
            <span>Supabase Auth & PostgreSQL Row-Level Security</span>
          </div>
          <span className="font-mono text-[11px]">256-BIT ENCRYPTION</span>
        </div>
      </div>

      {/* ── Right Form Container ── */}
      <div className="flex-1 flex items-center justify-center px-6 sm:px-12 py-12 lg:py-16">
        <div className="w-full max-w-md">
          {/* Mobile Top Brand Bar */}
          <div className="lg:hidden flex items-center justify-between mb-8 pb-4 border-b border-kairo-gray-200">
            <Link href="/" className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm bg-kairo-orange" />
              <span className="text-lg font-bold tracking-tight text-kairo-black">
                KAIRO
              </span>
            </Link>
            <span className="text-xs text-kairo-gray-500 font-mono uppercase">
              Authentication
            </span>
          </div>

          {/* Supabase Status Banner (Demo Mode Alert) */}
          {!isConfigured && (
            <div className="mb-6 p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-kairo flex items-start gap-2.5 text-xs text-amber-900">
              <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <span>Demo Mode Active</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-200/60 font-mono">
                    Instant Access
                  </span>
                </div>
                <p className="text-amber-800/90 leading-relaxed text-[11px]">
                  Local demo credentials detected in <code className="bg-amber-100 px-1 py-0.5 rounded text-amber-900 font-mono">.env.local</code>.
                  You can use one-click demo login or enter any credentials to explore!
                </p>
              </div>
            </div>
          )}

          {/* Mode Switcher Tabs */}
          {mode !== "forgot" ? (
            <div className="flex items-center p-1 bg-kairo-offwhite rounded-kairo mb-6 border border-kairo-gray-200">
              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setErrorMsg(null);
                  setSuccessMsg(null);
                }}
                className={`flex-1 py-2 text-xs font-semibold uppercase tracking-wider rounded-[6px] transition-all duration-200 ${
                  mode === "login"
                    ? "bg-white text-kairo-black shadow-sm"
                    : "text-kairo-gray-500 hover:text-kairo-black"
                }`}
              >
                Log In
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("signup");
                  setErrorMsg(null);
                  setSuccessMsg(null);
                }}
                className={`flex-1 py-2 text-xs font-semibold uppercase tracking-wider rounded-[6px] transition-all duration-200 ${
                  mode === "signup"
                    ? "bg-white text-kairo-black shadow-sm"
                    : "text-kairo-gray-500 hover:text-kairo-black"
                }`}
              >
                Sign Up
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => {
                setMode("login");
                setErrorMsg(null);
                setSuccessMsg(null);
              }}
              className="inline-flex items-center gap-1.5 text-xs text-kairo-gray-500 hover:text-kairo-black font-medium mb-6 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Log In</span>
            </button>
          )}

          {/* Form Header */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-kairo-black tracking-tight">
              {mode === "login" && "Welcome back"}
              {mode === "signup" && "Create your Kairo workspace"}
              {mode === "forgot" && "Reset your password"}
            </h1>
            <p className="text-xs text-kairo-gray-500 mt-1.5 leading-relaxed">
              {mode === "login" &&
                "Access your saved reconstructions, custom scene shaders, and export pipelines."}
              {mode === "signup" &&
                "Start reconstructing 2D architectural drawings into metric-accurate 3D assets."}
              {mode === "forgot" &&
                "Enter your registered account email and we'll send a secure password recovery link."}
            </p>
          </div>

          {/* Feedback Alerts */}
          {errorMsg && (
            <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-kairo flex items-start gap-2.5 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium">{errorMsg}</div>
            </div>
          )}

          {successMsg && (
            <div className="mb-5 p-3.5 bg-emerald-50 border border-emerald-200 rounded-kairo flex items-start gap-2.5 text-xs text-emerald-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium">{successMsg}</div>
            </div>
          )}

          {/* Main Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name Field (Sign Up Only) */}
            {mode === "signup" && (
              <div>
                <label
                  htmlFor="auth-name"
                  className="block text-[11px] font-semibold text-kairo-gray-600 uppercase tracking-wider mb-1.5"
                >
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-kairo-gray-400" />
                  <input
                    id="auth-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Maya Lin"
                    required
                    autoComplete="name"
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-kairo-gray-200 rounded-kairo text-sm text-kairo-black placeholder:text-kairo-gray-400 focus:outline-none focus:border-kairo-orange focus:ring-1 focus:ring-kairo-orange/20 transition-all"
                  />
                </div>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label
                htmlFor="auth-email"
                className="block text-[11px] font-semibold text-kairo-gray-600 uppercase tracking-wider mb-1.5"
              >
                Work Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-kairo-gray-400" />
                <input
                  id="auth-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="architect@studio.design"
                  required
                  autoComplete="email"
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-kairo-gray-200 rounded-kairo text-sm text-kairo-black placeholder:text-kairo-gray-400 focus:outline-none focus:border-kairo-orange focus:ring-1 focus:ring-kairo-orange/20 transition-all"
                />
              </div>
            </div>

            {/* Password Field (Not required for forgot mode) */}
            {mode !== "forgot" && (
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="auth-password"
                    className="block text-[11px] font-semibold text-kairo-gray-600 uppercase tracking-wider"
                  >
                    Password
                  </label>
                  {mode === "login" && (
                    <button
                      type="button"
                      onClick={() => {
                        setMode("forgot");
                        setErrorMsg(null);
                        setSuccessMsg(null);
                      }}
                      className="text-[11px] text-kairo-orange hover:underline font-medium transition-colors"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-kairo-gray-400" />
                  <input
                    id="auth-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={
                      mode === "login" ? "Enter your password" : "At least 8 characters"
                    }
                    required
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    minLength={6}
                    className="w-full pl-10 pr-11 py-2.5 bg-white border border-kairo-gray-200 rounded-kairo text-sm text-kairo-black placeholder:text-kairo-gray-400 focus:outline-none focus:border-kairo-orange focus:ring-1 focus:ring-kairo-orange/20 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-kairo-gray-400 hover:text-kairo-black transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>

                {/* Password Strength Checklist (Sign Up Only) */}
                {mode === "signup" && password.length > 0 && (
                  <div className="mt-2.5 p-2.5 bg-kairo-offwhite rounded-kairo border border-kairo-gray-200 space-y-1.5">
                    {/* Visual bar */}
                    <div className="flex gap-1 h-1 w-full bg-kairo-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          strengthScore === 1
                            ? "w-1/3 bg-amber-500"
                            : strengthScore === 2
                            ? "w-2/3 bg-blue-500"
                            : strengthScore === 3
                            ? "w-full bg-emerald-500"
                            : "w-0"
                        }`}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-[11px] text-kairo-gray-500 pt-1">
                      <div className="flex items-center gap-1.5">
                        {hasMinLength ? (
                          <Check className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <span className="w-3 h-3 rounded-full border border-kairo-gray-300 inline-block" />
                        )}
                        <span className={hasMinLength ? "text-emerald-700 font-medium" : ""}>
                          8+ characters
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {hasNumberOrSymbol ? (
                          <Check className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <span className="w-3 h-3 rounded-full border border-kairo-gray-300 inline-block" />
                        )}
                        <span className={hasNumberOrSymbol ? "text-emerald-700 font-medium" : ""}>
                          Number or symbol
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Remember Me Checkbox (Login mode) */}
            {mode === "login" && (
              <div className="flex items-center justify-between text-xs text-kairo-gray-500">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-3.5 h-3.5 rounded border-kairo-gray-300 text-kairo-orange focus:ring-kairo-orange/30 accent-kairo-orange"
                  />
                  <span>Remember this device</span>
                </label>
                <span className="text-[11px] text-kairo-gray-400">30-day session</span>
              </div>
            )}

            {/* Primary Action Button */}
            <button
              type="submit"
              disabled={loading || Boolean(oauthLoading)}
              className="btn-primary w-full text-xs font-semibold uppercase tracking-wider py-3 mt-3 flex items-center justify-center gap-2 shadow-sm"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>
                    {mode === "login"
                      ? "Verifying…"
                      : mode === "signup"
                      ? "Creating Account…"
                      : "Sending link…"}
                  </span>
                </div>
              ) : (
                <>
                  <span>
                    {mode === "login" && "Sign In to Workspace"}
                    {mode === "signup" && "Create Free Account"}
                    {mode === "forgot" && "Send Reset Link"}
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Social OAuth and Fast Demo Options */}
          {mode !== "forgot" && (
            <>
              {/* Divider */}
              <div className="flex items-center gap-4 my-6">
                <div className="flex-1 h-px bg-kairo-gray-200" />
                <span className="text-[11px] uppercase tracking-wider text-kairo-gray-400 font-medium">
                  or continue with
                </span>
                <div className="flex-1 h-px bg-kairo-gray-200" />
              </div>

              {/* OAuth Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleOAuth("google")}
                  disabled={loading || Boolean(oauthLoading)}
                  className="btn-outline w-full text-xs py-2.5 px-3 flex items-center justify-center gap-2 bg-white hover:bg-kairo-offwhite transition-colors"
                >
                  {oauthLoading === "google" ? (
                    <div className="w-3.5 h-3.5 border-2 border-kairo-gray-400 border-t-kairo-black rounded-full animate-spin" />
                  ) : (
                    <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                      <path
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                        fill="#4285F4"
                      />
                      <path
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        fill="#34A853"
                      />
                      <path
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        fill="#FBBC05"
                      />
                      <path
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        fill="#EA4335"
                      />
                    </svg>
                  )}
                  <span className="truncate">Google</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleOAuth("github")}
                  disabled={loading || Boolean(oauthLoading)}
                  className="btn-outline w-full text-xs py-2.5 px-3 flex items-center justify-center gap-2 bg-white hover:bg-kairo-offwhite transition-colors"
                >
                  {oauthLoading === "github" ? (
                    <div className="w-3.5 h-3.5 border-2 border-kairo-gray-400 border-t-kairo-black rounded-full animate-spin" />
                  ) : (
                    <svg className="w-4 h-4 shrink-0 fill-current" viewBox="0 0 24 24">
                      <path
                        fillRule="evenodd"
                        clipRule="evenodd"
                        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                      />
                    </svg>
                  )}
                  <span className="truncate">GitHub</span>
                </button>
              </div>

              {/* Instant One-Click Demo Mode Presets */}
              <div className="mt-6 pt-5 border-t border-kairo-gray-100">
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-kairo-gray-500">
                    Quick Access / Sandbox
                  </span>
                  <span className="inline-flex items-center gap-1 text-[10px] text-kairo-orange font-medium">
                    <Sparkles className="w-3 h-3" />
                    No signup needed
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleQuickDemo("Lead Architect", "architect@kairo.space")}
                    className="p-2.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 hover:border-kairo-orange/40 hover:bg-orange-50/20 text-left transition-all group"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-kairo-black group-hover:text-kairo-orange">
                      <Building2 className="w-3.5 h-3.5" />
                      <span>Lead Architect</span>
                    </div>
                    <p className="text-[10px] text-kairo-gray-400 mt-0.5">
                      Full workspace permissions
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleQuickDemo("Spatial Reviewer", "reviewer@kairo.space")}
                    className="p-2.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 hover:border-kairo-orange/40 hover:bg-orange-50/20 text-left transition-all group"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-kairo-black group-hover:text-kairo-orange">
                      <Layers className="w-3.5 h-3.5" />
                      <span>Spatial Reviewer</span>
                    </div>
                    <p className="text-[10px] text-kairo-gray-400 mt-0.5">
                      3D inspection & export
                    </p>
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Footer Terms & Privacy */}
          <p className="text-[11px] text-kairo-gray-400 text-center mt-8 leading-relaxed">
            By signing in, you agree to Kairo&apos;s{" "}
            <Link href="/" className="underline hover:text-kairo-black">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/" className="underline hover:text-kairo-black">
              Privacy Policy
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
          <div className="flex items-center gap-3 text-sm text-kairo-gray-500 font-mono">
            <div className="w-4 h-4 border-2 border-kairo-orange border-t-transparent rounded-full animate-spin" />
            <span>Loading Kairo Auth…</span>
          </div>
        </div>
      }
    >
      <AuthForm />
    </Suspense>
  );
}
