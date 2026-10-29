/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#effcf8",
          100: "#d8f8ec",
          500: "#16a982",
          600: "#0d9472",
          700: "#08775f",
          900: "#123d39"
        },
        ink: {
          800: "#1c2b43",
          900: "#142238",
          950: "#101a2d"
        }
      },
      boxShadow: {
        soft: "0 12px 35px -16px rgba(20, 34, 56, 0.18)"
      }
    }
  },
  plugins: []
};
