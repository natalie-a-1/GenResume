import React, { useState } from 'react';
import axios from 'axios';

function ResumeEditor() {
  const [jobDescription, setJobDescription] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [updatedContent, setUpdatedContent] = useState([]);

  const handleOptimize = async () => {
    const response = await axios.post('http://localhost:5000/optimize_resume', {
      job_description: jobDescription,
      document_id: documentId
    });
    setUpdatedContent(response.data.updated_content);
  };

  const handleExport = async () => {
    await axios.post('http://localhost:5000/export_pdf', {
      document_id: documentId
    });
  };

  return (
    <div>
      <h1>Resume Optimizer</h1>
      <textarea
        placeholder="Paste job description here"
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
      />
      <input
        type="text"
        placeholder="Google Docs Document ID"
        value={documentId}
        onChange={(e) => setDocumentId(e.target.value)}
      />
      <button onClick={handleOptimize}>Optimize Resume</button>
      <div>
        <h2>Resume Content</h2>
        {updatedContent.map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
      <button onClick={handleExport}>Export as PDF</button>
    </div>
  );
}

export default ResumeEditor;