import { useMemo, useState } from 'react'
import './Game.css'
import QuizCard from '../components/QuizCard.jsx'
import PetDisplay from '../components/PetDisplay.jsx'

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

function Game({ questions, onGoBack }) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [health, setHealth] = useState(70)
  const [isEating, setIsEating] = useState(false)
  const [canFeed, setCanFeed] = useState(false)
  const [showFinishModal, setShowFinishModal] = useState(false)

  // Use backend questions or fallback to empty array
  const questionList = questions || []
  const quiz = useMemo(() => questionList[currentQuestion], [currentQuestion, questionList])
  const isLastQuestion = questionList.length > 0 && currentQuestion === questionList.length - 1

  const handleAnswer = ({ correct }) => {
    // Use health impact from backend question if available, otherwise use defaults
    const delta = correct ? (quiz?.health_impact?.correct || 8) : (quiz?.health_impact?.wrong || -12)
    setHealth((hp) => clamp(hp + delta, 0, 100))
    
    // Only allow feeding if answer was correct
    setCanFeed(correct)
  }

  const handleNext = () => {
    setCanFeed(false)
    if (isLastQuestion) {
      setShowFinishModal(true)
    } else {
      setCurrentQuestion((idx) => idx + 1)
    }
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

  const handleContinue = () => {
    setShowFinishModal(false)
    setCurrentQuestion(0)
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
        <button
          className="game__goback"
          type="button"
          onClick={onGoBack}
          aria-label="Upload a different set of files"
        >
          Go back
        </button>
      </div>

      <div className="game__right">
        <QuizCard quiz={quiz} onAnswer={handleAnswer} onNext={handleNext} />
        <div className="game__meta">
          Question {currentQuestion + 1} of {questionList.length}
        </div>
      </div>

      {showFinishModal && (
        <div className="game__modal" role="dialog" aria-modal="true" aria-labelledby="finish-modal-title">
          <div className="game__modalBackdrop" onClick={() => setShowFinishModal(false)} aria-hidden="true" />
          <div className="game__modalCard">
            <h2 id="finish-modal-title" className="game__modalTitle">You finished this set!</h2>
            <p className="game__modalText">Upload a different file for new questions, or play this set again.</p>
            <div className="game__modalActions">
              <button type="button" className="game__modalBtn game__modalBtn--secondary" onClick={onGoBack}>
                Go back
              </button>
              <button type="button" className="game__modalBtn game__modalBtn--primary" onClick={handleContinue}>
                Continue
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

export default Game
