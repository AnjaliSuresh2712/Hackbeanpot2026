import { useMemo, useState } from 'react'
import './Game.css'
import QuizCard from '../components/QuizCard.jsx'
import PetDisplay from '../components/PetDisplay.jsx'

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

function Game({ questions }) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [health, setHealth] = useState(70)
  const [isEating, setIsEating] = useState(false)
  const [canFeed, setCanFeed] = useState(false)

  // Use backend questions or fallback to empty array
  const questionList = questions || []
  const quiz = useMemo(() => questionList[currentQuestion], [currentQuestion, questionList])

  const handleAnswer = ({ correct }) => {
    // Use health impact from backend question if available, otherwise use defaults
    const delta = correct ? (quiz?.health_impact?.correct || 8) : (quiz?.health_impact?.wrong || -12)
    setHealth((hp) => clamp(hp + delta, 0, 100))
    
    // Only allow feeding if answer was correct
    setCanFeed(correct)
  }

  const handleNext = () => {
    setCurrentQuestion((idx) => (idx + 1) % (questionList.length || 1))
    setCanFeed(false) // Reset feed button for new question
  }

  const handleFeed = () => {
    setIsEating(true)
    setHealth((hp) => clamp(hp + 6, 0, 100))
    setCanFeed(false) // Disable feed button after feeding
    setTimeout(() => setIsEating(false), 600)
  }

  if (!questionList.length) {
    return (
      <main className="game">
        <div className="game__left">
          <PetDisplay health={health} isEating={isEating} />
        </div>
        <div className="game__right">
          <p>Loading questions...</p>
        </div>
      </main>
    )
  }

  return (
    <main className="game">
      <div className="game__left">
        <PetDisplay health={health} isEating={isEating} />
        {canFeed && (
          <button className="game__feed" type="button" onClick={handleFeed}>
            Feed
          </button>
        )}
      </div>

      <div className="game__right">
        <QuizCard quiz={quiz} onAnswer={handleAnswer} onNext={handleNext} />
        <div className="game__meta">
          Question {currentQuestion + 1} of {questionList.length}
        </div>
      </div>
    </main>
  )
}

export default Game
