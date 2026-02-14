import UploadBox from '../components/UploadBox.jsx'

export default function Home() {
    return (
        <main className="home-page">
            <div className="home-container">
                <img
                    src="/fixedefault.png"
                    alt="Tamagotchi default"
                    className="home-image"
                />
                <div className="home-actions">
                    <UploadBox />
                </div>
            </div>
        </main>
    )
}