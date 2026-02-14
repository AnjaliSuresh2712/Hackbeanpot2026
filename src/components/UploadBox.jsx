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
            <span className="upload-title">Feed the Tomodachi!!!</span>
            <span className="upload-subtext">Upload your study files here</span>
        </label>
    )
}
