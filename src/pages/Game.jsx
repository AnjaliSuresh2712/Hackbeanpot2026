import { useState } from 'react'
import './Game.css'
import QuizCard from '../components/QuizCard.jsx'
import PetDisplay from '../components/PetDisplay.jsx'

function Game() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [score, setScore] = useState(0)

  // Sample quiz questions
  const questions = [
    {
      question: "What is the capital of France?",
      options: ["London", "Paris", "Berlin", "Madrid"],
      correct: 1
    },
    {
      question: "What is 2 + 2?",
      options: ["3", "4", "5", "6"],
      correct: 1
    },
    {
      question: "What is the largest planet in our solar system?",
      options: ["Saturn", "Jupiter", "Neptune", "Earth"],
      correct: 1
    }
  ]

  const handleAnswer = (selectedIndex) => {
    if (selectedIndex === questions[currentQuestion].correct) {
      setScore(score + 1)
    }

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    } else {
      alert(`Quiz Complete! Your score: ${score + 1}/${questions.length}`)
      setCurrentQuestion(0)
      setScore(0)
    }
  }

  return (
    <div className="game-container">
      <PetDisplay />
      <QuizCard 
        question={questions[currentQuestion].question}
        options={questions[currentQuestion].options}
        onAnswer={handleAnswer}
      />
      <div className="score">Question {currentQuestion + 1} of {questions.length}</div>
    </div>
  )
}

export default Game