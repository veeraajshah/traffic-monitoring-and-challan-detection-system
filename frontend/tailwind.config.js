export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Sora", "Segoe UI", "sans-serif"],
        body: ["Space Grotesk", "Segoe UI", "sans-serif"],
      },
      colors: {
        ink: "#07111f",
        steel: "#0e1c32",
        neon: "#67e8f9",
        coral: "#ff8f70",
        moss: "#7dd3a7",
        mist: "#e8f3ff",
      },
      boxShadow: {
        panel: "0 22px 70px rgba(7, 17, 31, 0.34)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
