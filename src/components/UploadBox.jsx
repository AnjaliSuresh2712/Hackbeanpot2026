import './UploadBox.css'

export default function UploadBox({ onUpload }) {
    const handleChange = (event) => {
        if (event.target.files?.length) {
            onUpload?.(event.target.files)
        }
    }

    return (
        <label className="upload-box">
            <input
                className="upload-input"
                type="file"
                multiple
                onChange={handleChange}
            />
            <span className="upload-title">Feed</span>
            <span className="upload-subtext">Upload study files</span>
        </label>
    )
}
