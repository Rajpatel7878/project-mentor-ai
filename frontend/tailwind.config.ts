module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        cyan: { glow: '#00f0ff' },
        mentor: {
          dark: '#0a0e17',
          panel: 'rgba(10, 20, 40, 0.7)',
          border: 'rgba(0, 240, 255, 0.3)',
        },
      },
      fontFamily: {
        display: ['Orbitron', 'sans-serif'],
        body: ['Rajdhani', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
