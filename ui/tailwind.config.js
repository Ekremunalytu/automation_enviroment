/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvasDeep: "#0b0e10",
        canvas: "#101416",
        panel: "#151b1f",
        panelAlt: "#1a2126",
        surface: "#232c34",
        surfaceRaised: "#2a3540",
        lineSoft: "#20282f",
        line: "#2b3640",
        lineStrong: "#3b4a56",
        ink: "#f4f0e8",
        inkSoft: "#d9d2c5",
        mute: "#a19a8b",
        accent: "#9ec6b3",
        accentStrong: "#b6dbc8",
        accentSoft: "#e1f0e8",
        success: "#7bc47f",
        warning: "#d3a35f",
        danger: "#d9776b",
        cyan: "#9ec6b3",
        lime: "#7bc47f",
        amber: "#d3a35f",
        rose: "#d9776b",
      },
      fontFamily: {
        display: ["Manrope", "sans-serif"],
        body: ["Manrope", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        soft: "0 18px 44px rgba(2, 8, 20, 0.28)",
        inset: "inset 0 1px 0 rgba(255, 255, 255, 0.05)",
        focus: "0 0 0 4px rgba(103, 164, 255, 0.18)",
      },
      letterSpacing: {
        data: "0.18em",
      },
    },
  },
  plugins: [],
};
