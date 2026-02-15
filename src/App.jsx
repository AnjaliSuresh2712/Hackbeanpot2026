import { useState } from 'react'
import './App.css'
import Home from './pages/Home.jsx'
import Game from './pages/Game.jsx'

function App() {
  const [currentPage, setCurrentPage] = useState('home')
  const [questions, setQuestions] = useState(null)

  const handleStart = (uploadedQuestions) => {
    setQuestions(uploadedQuestions)
    setCurrentPage('game')
  }

  return currentPage === 'home' ? (
    <Home onStart={handleStart} />
  ) : (
    <Game questions={questions} />
  )
}

export default App
