import { useEffect, useMemo, useState } from 'react'
import './PetDisplay.css'

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

const SPRITES = {
  idle: '/assets/defualtsprite.png',
  eating: '/assets/openmouth.png',
  happy: '/assets/aftereat.png',
  sick: '/assets/pet-sick.png',
}

export default function PetDisplay({ health = 100, isEating = false }) {
  const hp = useMemo(() => clamp(Number(health) || 0, 0, 100), [health])
  const [showHappy, setShowHappy] = useState(false)

  // When feeding ends, briefly show a "happy/full" sprite.
  useEffect(() => {
    if (isEating || hp <= 0) {
      setShowHappy(false)
      return
    }

    setShowHappy(true)
    const timer = setTimeout(() => setShowHappy(false), 900)
    return () => clearTimeout(timer)
  }, [isEating, hp])

  let stateLabel = 'CHILLING'
  let sprite = SPRITES.idle
  let animationClass = 'breathe'
  let hpColor = '#94C9A9'

  if (hp <= 0) {
    stateLabel = 'R.I.P.'
    sprite = SPRITES.sick
    animationClass = 'dead'
    hpColor = '#885053'
  } else if (isEating) {
    stateLabel = 'EATING'
    sprite = SPRITES.eating
    animationClass = 'bounce'
    hpColor = '#D5573B'
  } else if (showHappy) {
    stateLabel = 'FULL'
    sprite = SPRITES.happy
    animationClass = 'bounce'
    hpColor = '#94C9A9'
  } else if (hp < 40) {
    stateLabel = 'SICK'
    sprite = SPRITES.sick
    animationClass = 'shake'
    hpColor = '#D5573B'
  } else if (hp < 90) {
    stateLabel = 'STUDYING'
    sprite = SPRITES.idle
    animationClass = 'breathe'
    hpColor = '#777DA7'
  } else {
    stateLabel = 'GENIUS'
    sprite = SPRITES.happy
    animationClass = 'bounce'
    hpColor = '#94C9A9'
  }

  return (
    <div className="pet">
      <div className="pet__status" aria-live="polite">{stateLabel}</div>
      <div className="pet__stage">
        <img className={`pet__sprite ${animationClass}`} src={sprite} alt="Study-Gotchi" />
      </div>

      <div className="pet__hp">
        <div className="pet__hpTrack" aria-hidden="true">
          <div className="pet__hpFill" style={{ width: `${hp}%`, backgroundColor: hpColor }} />
        </div>
        <div className="pet__hpLabel">HP: {hp}%</div>
      </div>
    </div>
  )
}
