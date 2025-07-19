// App.jsx
import React from 'react'
import './App.css'
import TranslateApp from './pages/Translate'

const App = () => {
    return(
        <div style={styles.page}>
            <TranslateApp />
        </div>
    )
}

const styles = {
    page: {
        backgroundColor: '#1a1a1a', // ChatGPT-like background color
        minHeight: '100vh', // Ensures it covers the full viewport height
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
    },
    gradientText: {
        background: 'linear-gradient(90deg, #0033cc, #007bff, #66ccff, #ffffff)', // Bold blue to light blue to white gradient
        WebkitBackgroundClip: 'text',
        color: 'transparent',
        fontWeight: 'bold',
    },
    
};

export default App
