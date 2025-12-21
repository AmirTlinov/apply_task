/** @type {import('tailwindcss').Config} */
import { fontFamily } from "tailwindcss/defaultTheme"

const withAlpha = (variable) => `hsl(var(${variable}) / <alpha-value>)`

export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      transitionTimingFunction: {
        sidebar: "cubic-bezier(0.32,0.72,0,1)",
      },
      colors: {
        border: withAlpha("--border"),
        input: withAlpha("--input"),
        ring: withAlpha("--ring"),
        background: {
          DEFAULT: withAlpha("--background"),
          subtle: withAlpha("--background-subtle"),
          muted: withAlpha("--background-muted"),
          hover: withAlpha("--background-hover"),
        },
        foreground: {
          DEFAULT: withAlpha("--foreground"),
          muted: withAlpha("--foreground-muted"),
          subtle: withAlpha("--foreground-subtle"),
        },
        primary: {
          DEFAULT: withAlpha("--primary"),
          foreground: withAlpha("--primary-foreground"),
          hover: "hsl(var(--primary) / 0.9)",
          subtle: "hsl(var(--primary) / 0.1)",
        },
        secondary: {
          DEFAULT: withAlpha("--secondary"),
          foreground: withAlpha("--secondary-foreground"),
        },
        destructive: {
          DEFAULT: withAlpha("--destructive"),
          foreground: withAlpha("--destructive-foreground"),
        },
        muted: {
          DEFAULT: withAlpha("--muted"),
          foreground: withAlpha("--muted-foreground"),
        },
        accent: {
          DEFAULT: withAlpha("--accent"),
          foreground: withAlpha("--accent-foreground"),
        },
        popover: {
          DEFAULT: withAlpha("--popover"),
          foreground: withAlpha("--popover-foreground"),
        },
        card: {
          DEFAULT: withAlpha("--card"),
          foreground: withAlpha("--card-foreground"),
        },
        status: {
          todo: {
            DEFAULT: withAlpha("--status-todo"),
            foreground: withAlpha("--foreground"),
          },
          active: {
            DEFAULT: withAlpha("--status-active"),
            foreground: withAlpha("--primary-foreground"),
          },
          done: {
            DEFAULT: withAlpha("--status-done"),
            foreground: "white",
          },
          ok: {
            DEFAULT: withAlpha("--status-ok"),
            foreground: "white",
          },
          warn: {
            DEFAULT: withAlpha("--status-warn"),
            foreground: "white",
          },
          fail: {
            DEFAULT: withAlpha("--status-fail"),
            foreground: "white",
          },
        }
      },
      borderRadius: {
        lg: `var(--radius)`,
        md: `calc(var(--radius) - 2px)`,
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", ...fontFamily.sans],
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
