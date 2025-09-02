module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // scan all your components/pages
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
