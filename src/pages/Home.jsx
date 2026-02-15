import { useEffect, useRef, useState } from 'react'
import UploadBox from '../components/UploadBox.jsx'

export default function Home({ onStart }) {
    const [isEating, setIsEating] = useState(false)
    const [isGrowing, setIsGrowing] = useState(false)
    const [questions, setQuestions] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const eatTimeoutRef = useRef(null)
    const growTimeoutRef = useRef(null)

    useEffect(() => {
        return () => {
            clearTimeout(eatTimeoutRef.current)
            clearTimeout(growTimeoutRef.current)
        }
    }, [])

    const handleUpload = (uploadedQuestions) => {
        setQuestions(uploadedQuestions)
        setIsLoading(false)
        setIsEating(true)
        clearTimeout(eatTimeoutRef.current)

        // Eating animation for 2.5 seconds
        eatTimeoutRef.current = setTimeout(() => {
            setIsEating(false)
            setIsGrowing(true)

            // Growth animation for 0.8 seconds, then switch pages
            growTimeoutRef.current = setTimeout(() => {
                onStart?.(uploadedQuestions)
            }, 800)
        }, 1900)
    }

    return (
        <main className={`home-page${isGrowing ? ' home-page--growing' : ''}`}>
            <div className="home-container">
                <img
                    src={isEating ? '/openmouth.png' : '/fixedefault.png'}
                    alt="Tamagotchi"
                    className={`home-image${isEating ? ' home-image--eating' : ''}${isGrowing ? ' home-image--growing' : ''}`}
                />
                {!isGrowing && (
                    <div className="home-actions">
                        <UploadBox onUpload={handleUpload} onLoading={setIsLoading} />
                    </div>
                )}
            </div>
        </main>
    )
}