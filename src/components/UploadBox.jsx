import './UploadBox.css'

export default function UploadBox() {
	return (
		<label className="upload-box">
			<input
				className="upload-input"
				type="file"
				multiple
			/>
			<span className="upload-title">Feed</span>
			<span className="upload-subtext">Upload study files</span>
		</label>
	)
}
