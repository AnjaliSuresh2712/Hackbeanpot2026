import { useEffect, useRef, useState } from 'react'
import UploadBox from '../components/UploadBox.jsx'

export default function Home() {
    const [isEating, setIsEating] = useState(false)
    const eatTimeoutRef = useRef(null)

    useEffect(() => () => clearTimeout(eatTimeoutRef.current), [])

    const handleUpload = () => {
        setIsEating(true)
        clearTimeout(eatTimeoutRef.current)
        eatTimeoutRef.current = setTimeout(() => {
            setIsEating(false)
        }, 2500)
    }

    return (
        <main className="home-page">
            <div className="home-container">
                <img
                    src={isEating ? '/openmouth.png' : '/fixedefault.png'}
                    alt="Tamagotchi"
                    className={`home-image${isEating ? ' home-image--eating' : ''}`}
                />
                <div className="home-actions">
                    <UploadBox onUpload={handleUpload} />
                </div>
            </div>
        </main>
    )
}