/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
 
    // Or if using `src` directory:
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'pink-custom': '#d93f87',
        'purple-custom-saturated':'#5323ab',
        'grey-custom' : '#aab3b6',
        'grey-custom-dark' : '#2d3437',
        'grey-custom-light' : '#171e21',
        'grey-custom-green' : '#101619',
        'grey-custom-darkgreen' : '#071013',
        'blue-custom' : '#202f36',
        'blue-custom-light' : '#3c879c',
        'blue-custom-highlight' : '#5ff5ff',
        'black-custom-text' : '#161e21',
        'black-custom' : '#121212',
        'white-custom' : '#E5ECF4',
        'purple-custom-light' : '#8265a7',
        'red-custom' : '#a52f31',
        'red-custom-highlight' : '#ff6969',
        'green-custom-light' : '#1bb194',
        
      },
      
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}

