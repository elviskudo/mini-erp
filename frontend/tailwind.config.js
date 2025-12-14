/** @type {import('tailwindcss').Config} */
module.exports = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'Poppins', 'sans-serif'],
                display: ['Outfit', 'sans-serif']
            },
            colors: {
                // Gumroad-inspired pink palette
                primary: {
                    50: '#fdf2f8',
                    100: '#fce7f3',
                    200: '#fbcfe8',
                    300: '#f9a8d4',
                    400: '#f472b6',
                    500: '#ec4899',  // Main pink
                    600: '#db2777',
                    700: '#be185d',
                    800: '#9d174d',
                    900: '#831843',
                    950: '#500724',
                    DEFAULT: '#ec4899'
                },
                // Accent purple
                accent: {
                    50: '#faf5ff',
                    100: '#f3e8ff',
                    200: '#e9d5ff',
                    300: '#d8b4fe',
                    400: '#c084fc',
                    500: '#a855f7',
                    600: '#9333ea',
                    700: '#7e22ce',
                    800: '#6b21a8',
                    900: '#581c87',
                    DEFAULT: '#a855f7'
                },
                // Neutral grays
                neutral: {
                    50: '#fafafa',
                    100: '#f5f5f5',
                    200: '#e5e5e5',
                    300: '#d4d4d4',
                    400: '#a3a3a3',
                    500: '#737373',
                    600: '#525252',
                    700: '#404040',
                    800: '#262626',
                    900: '#171717',
                    DEFAULT: '#737373'
                },
                // Success/Error states
                success: {
                    DEFAULT: '#10b981',
                    light: '#d1fae5'
                },
                error: {
                    DEFAULT: '#ef4444',
                    light: '#fee2e2'
                }
            },
            backgroundImage: {
                'gradient-gumroad': 'linear-gradient(135deg, #fdf2f8 0%, #f3e8ff 100%)',
                'gradient-pink': 'linear-gradient(135deg, #ec4899 0%, #a855f7 100%)',
                'gradient-dark': 'linear-gradient(135deg, #171717 0%, #262626 100%)'
            },
            boxShadow: {
                'gumroad': '0 4px 14px 0 rgba(236, 72, 153, 0.2)',
                'gumroad-lg': '0 10px 40px 0 rgba(236, 72, 153, 0.25)'
            },
            borderRadius: {
                'xl': '1rem',
                '2xl': '1.5rem',
                '3xl': '2rem'
            }
        }
    }
}
