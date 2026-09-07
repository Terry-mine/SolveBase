import tailwindcssAnimate from "tailwindcss-animate"

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 原始色板（支持 /alpha 透明度修饰符，如 bg-seal/10）
        paper: "hsl(var(--paper) / <alpha-value>)",
        ink: "hsl(var(--ink) / <alpha-value>)",
        rule: "hsl(var(--rule) / <alpha-value>)",
        ledger: "hsl(var(--ledger) / <alpha-value>)",
        seal: "hsl(var(--seal) / <alpha-value>)",
        pine: "hsl(var(--pine) / <alpha-value>)",
        ochre: "hsl(var(--ochre) / <alpha-value>)",
        console: "hsl(var(--console) / <alpha-value>)",

        // 文字专用暗色档（小字号徽章 / 状态文字，保证 WCAG 4.5:1）
        "ledger-ink": "hsl(var(--ledger-ink) / <alpha-value>)",
        "seal-ink": "hsl(var(--seal-ink) / <alpha-value>)",
        "pine-ink": "hsl(var(--pine-ink) / <alpha-value>)",
        "ochre-ink": "hsl(var(--ochre-ink) / <alpha-value>)",
        "neutral-ink": "hsl(var(--neutral-ink) / <alpha-value>)",

        // 装饰渐变色（仅用于 BrandBar / 空状态插画）
        "aurora-start": "hsl(var(--aurora-start) / <alpha-value>)",
        "aurora-mid": "hsl(var(--aurora-mid) / <alpha-value>)",
        "aurora-end": "hsl(var(--aurora-end) / <alpha-value>)",

        // shadcn 语义令牌
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        sans: "var(--font-sans)",
        mono: "var(--font-mono)",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [tailwindcssAnimate],
}
