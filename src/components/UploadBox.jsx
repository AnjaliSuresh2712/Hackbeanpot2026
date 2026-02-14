import './UploadBox.css'

export default function UploadBox({ onOpen, onClose }) {
    return (
        <label className="upload-box">
            <input
                className="upload-input"
                type="file"
                multiple
                onClick={onOpen}
                onFocus={onOpen}
                onChange={onClose}
                onBlur={onClose}
            />
            <span className="upload-title">Feed</span>
            <span className="upload-subtext">Upload study files</span>
        </label>
    )
}
