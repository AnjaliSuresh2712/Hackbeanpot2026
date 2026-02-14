import { useMemo, useState } from 'react'
import './QuizCard.css'

const normalizeQuiz = (quiz) => {
  const safeQuiz = quiz && typeof quiz === 'object' ? quiz : {}
  const id = safeQuiz.id ?? safeQuiz.quizId ?? safeQuiz.questionId ?? 'quiz'
  const question = safeQuiz.question ?? safeQuiz.prompt ?? '...'

  const rawOptions =
    safeQuiz.options ??
    safeQuiz.choices ??
    safeQuiz.answers ??
    safeQuiz.responses ??
    []

  const options = Array.isArray(rawOptions) ? rawOptions.map(String) : []
  const correctIndexRaw =
    safeQuiz.correctIndex ??
    safeQuiz.correct_option_index ??
    safeQuiz.correctChoiceIndex ??
    safeQuiz.answerIndex ??
    safeQuiz.answer_index

  const correctIndex = Number.isFinite(Number(correctIndexRaw)) ? Number(correctIndexRaw) : -1
  const explanation = safeQuiz.explanation ?? safeQuiz.rationale ?? ''

  return { id, question, options, correctIndex, explanation }
}

export default function QuizCard({
  quiz,
  disabled = false,
  onAnswer,
  onNext,
  revealAnswer = true,
}) {
  const { id, question, options, correctIndex, explanation } = useMemo(
    () => normalizeQuiz(quiz),
    [quiz],
  )

  const [selectedIndex, setSelectedIndex] = useState(null)
  const [isLocked, setIsLocked] = useState(false)

  const canGrade = correctIndex >= 0 && correctIndex < options.length
  const isCorrect = selectedIndex != null && canGrade && selectedIndex === correctIndex

  const choose = (index) => {
    if (disabled || isLocked) return
    setSelectedIndex(index)
    setIsLocked(true)
    onAnswer?.({
      quizId: id,
      choiceIndex: index,
      correct: canGrade ? index === correctIndex : null,
    })
  }

  const next = () => {
    setSelectedIndex(null)
    setIsLocked(false)
    onNext?.()
  }

  return (
    <section className={`quiz ${disabled ? 'is-disabled' : ''}`} aria-labelledby={`quiz-${id}`}>
      <div className="quiz__header">
        <div className="quiz__title" id={`quiz-${id}`}>Pop Quiz</div>
        <div className="quiz__meta">{canGrade ? '1 question' : 'ungraded'}</div>
      </div>

      <div className="quiz__question">{question}</div>

      <div className="quiz__options" role="list">
        {options.map((opt, idx) => {
          const isChosen = selectedIndex === idx
          const isRight = canGrade && idx === correctIndex
          const isWrong = canGrade && selectedIndex != null && isChosen && !isCorrect
          const shouldReveal = revealAnswer && isLocked

          const className = [
            'quiz__option',
            isChosen ? 'is-chosen' : '',
            shouldReveal && isRight ? 'is-correct' : '',
            shouldReveal && isWrong ? 'is-wrong' : '',
          ]
            .filter(Boolean)
            .join(' ')

          return (
            <button
              key={`${id}-${idx}`}
              className={className}
              type="button"
              onClick={() => choose(idx)}
              disabled={disabled || isLocked}
            >
              <span className="quiz__badge" aria-hidden="true">
                {String.fromCharCode(65 + idx)}
              </span>
              <span className="quiz__text">{opt}</span>
            </button>
          )
        })}
      </div>

      <div className="quiz__footer">
        <div className="quiz__result" aria-live="polite">
          {selectedIndex == null
            ? 'Choose an answer.'
            : canGrade
              ? (isCorrect ? 'Correct! Pet gets healthier.' : 'Wrong... Pet gets sick.')
              : 'Answer recorded.'}
        </div>

        {isLocked && (
          <button className="quiz__next" type="button" onClick={next} disabled={disabled}>
            Next
          </button>
        )}
      </div>

      {isLocked && revealAnswer && explanation ? (
        <div className="quiz__explain">
          <div className="quiz__explainTitle">Why</div>
          <div className="quiz__explainBody">{explanation}</div>
        </div>
      ) : null}
    </section>
  )
}
