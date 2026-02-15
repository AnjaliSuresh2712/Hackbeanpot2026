import './UploadBox.css'
import { useState } from 'react'

export default function UploadBox({ onUpload, onLoading }) {
    const [isLoading, setIsLoading] = useState(false)

    const handleChange = async (event) => {
        if (event.target.files?.length) {
            const file = event.target.files[0]
            
            if (!file.name.endsWith('.pdf')) {
                alert('Please upload a PDF file')
                return
            }

            setIsLoading(true)
            onLoading?.(true)

            try {
                const formData = new FormData()
                formData.append('file', file)

                const response = await fetch('http://localhost:8000/upload-and-generate', {
                    method: 'POST',
                    body: formData
                })

                if (!response.ok) {
                    throw new Error('Failed to process PDF')
                }

                const data = await response.json()
                onUpload?.(data.questions)
            } catch (error) {
                console.error('Error uploading PDF:', error)
                alert('Error processing PDF. Make sure the backend is running on http://localhost:8000')
                onLoading?.(false)
                setIsLoading(false)
            }
        }
    }

    return (
        <label className="upload-box">
            <input
                className="upload-input"
                type="file"
                accept=".pdf"
                onChange={handleChange}
                disabled={isLoading}
            />
            <span className="upload-title">{isLoading ? 'Feeding...' : 'Feed!'}</span>
            <span className="upload-subtext">{isLoading ? 'Processing...' : 'Upload study files here'}</span>
        </label>
    )
}
