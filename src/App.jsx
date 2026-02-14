import { useState } from 'react'
import './App.css'
import Home from './pages/Home.jsx'
import Game from './pages/Game.jsx'

function App() {
  const [currentPage, setCurrentPage] = useState('home')

  return currentPage === 'home' ? (
    <Home onStart={() => setCurrentPage('game')} />
  ) : (
    <Game />
  )
}

export default App
