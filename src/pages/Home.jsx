import { useState } from 'react'
import UploadBox from '../components/UploadBox.jsx'

export default function Home() {
    const [isMouthOpen, setIsMouthOpen] = useState(false)

    return (
        <main className="home-page">
            <div className="home-container">
                <img
                    src={isMouthOpen ? '/openmouth.png' : '/fixedefault.png'}
                    alt="Tamagotchi"
                    className="home-image"
                />
                <div className="home-actions">
                    <UploadBox
                        onOpen={() => setIsMouthOpen(true)}
                        onClose={() => setIsMouthOpen(false)}
                    />
                </div>
            </div>
        </main>
    )
}