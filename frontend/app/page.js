"use client"

import { useState } from "react"

export default function CsvUploader() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")

  const handleFileChange = (event) => {
    const file = event.target.files[0]
    if (file) {
      if (file.type === "text/csv" || file.name.toLowerCase().endsWith(".csv")) {
        setSelectedFile(file)
        setError("")
        setSuccessMessage("")
      } else {
        setError(" Please select a valid CSV file (.csv).")
        setSelectedFile(null)
      }
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!selectedFile) {
      setError("Please select a CSV file first.")
      return
    }

    setIsLoading(true)
    setError("")
    setSuccessMessage("")

    try {
      const formData = new FormData()
      formData.append("file", selectedFile)

      const response = await fetch("https://pezesha-data.onrender.com/upload", {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`)
      }

      setSuccessMessage(` ${data.message}`)
    } catch (err) {
      setError(err.message || "An error occurred while uploading the file.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>CSV Uploader</h1>
      </header>

      <main className="main">
        <div className="container">
          <form onSubmit={handleSubmit} className="upload-form">
            <div className="file-input-wrapper">
              <input
                type="file"
                id="csvFile"
                accept=".csv"
                onChange={handleFileChange}
                className="file-input"
              />
              <label htmlFor="csvFile" className="file-input-label">
                {selectedFile ? selectedFile.name : "Choose CSV File"}
              </label>
            </div>

            <button type="submit" disabled={!selectedFile || isLoading} className="submit-button">
              {isLoading ? "Uploading..." : "Upload & Insert"}
            </button>
          </form>

          {isLoading && (
            <div className="loading">
              <p>Processing your CSV file...</p>
            </div>
          )}

          {error && (
            <div className="error">
              <p>{error}</p>
            </div>
          )}

          {successMessage && (
            <div className="success">
              <p>{successMessage}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
