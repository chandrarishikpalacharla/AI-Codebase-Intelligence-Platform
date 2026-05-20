// =============================================================
// AiHomePage.jsx
// =============================================================

import React, { useRef, useState } from 'react'
import './AiHomePage.css'
import { uploadZip } from '../Services/Api';
import AddIcon from '@mui/icons-material/Add';
import SendIcon from '@mui/icons-material/Send';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';

const AiHomePage = () => {

  const [search, setSearch] = useState('');
  const [files, setFiles] = useState([]);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const fileRef = useRef();

  const handleClick = () => fileRef.current.click()

  const handleChange = (e) => {
    setSearch(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    if (files.length + newFiles.length > 3) {
      alert("Max 3 files allowed");
      return;
    }
    setFiles((prev) => [...prev, ...newFiles])
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }

  const handleSend = async () => {

    if (!search.trim() || files.length === 0) {
      alert("Please add a zip file and a question");
      return;
    }

    try {
      setLoading(true);
      setAnswer('');
      setStatus('');

      // step 1 - upload zip → get session_id
      setStatus('Uploading zip...')
      const session_id = await uploadZip(files[0]);
      console.log("session_id:", session_id);

      // step 2 - connect websocket with session_id
      setStatus('Connecting...')
      const ws = new WebSocket(`ws://localhost:8080/api/ws/chat/${session_id}`);

      ws.onopen = () => {
        ws.send(search);  // send question to server
      }

      ws.onmessage = (event) => {
        const token = event.data;

        // show status messages
        if (token.startsWith('🔍') || token.startsWith('💡') || token.startsWith('📁')) {
          setStatus(token);
          return;
        }

        // append streaming answer word by word
        setAnswer(prev => prev + token);
      }

      ws.onclose = () => {
        setLoading(false);
        setStatus('');
      }

      ws.onerror = (error) => {
        console.error(error);
        setLoading(false);
        setStatus('Something went wrong');
      }

    } catch (error) {
      console.error(error);
      setLoading(false);
      setStatus('');
    }
  }

  return (
    <div className='background'>

      <div className='hero-section'>
        <h1 className='appname'>Smart Notes Q&A</h1>
        <p className='welcome'>Upload your codebase zip and ask anything instantly</p>
      </div>

      <div className='chat-container'>

        {/* status line */}
        {status && <p className='status'>{status}</p>}

        {/* streaming answer box */}
        {answer && (
          <div className='answer-box'>
            <p>{answer}</p>
          </div>
        )}

        {/* file chips */}
        {files.length > 0 && (
          <div className='file-list'>
            {files.map((file, index) => (
              <div className='file-name' key={index}>
                <PictureAsPdfIcon className='pdf-icon' />
                <span>{file.name}</span>
                <span className='remove-file' onClick={() => removeFile(index)}>✕</span>
              </div>
            ))}
          </div>
        )}

        <div className='input-box'>
          <button className='icon-btn' onClick={handleClick}>
            <AddIcon />
          </button>
          <input
            type='file'
            hidden
            accept='.zip'
            ref={fileRef}
            onChange={handleFileChange}
          />
          <textarea
            className='input-text'
            value={search}
            placeholder='Ask anything about your codebase...'
            onChange={handleChange}
            rows={1}
          />
          <button className='send-btn' onClick={handleSend} disabled={loading}>
            <SendIcon />
          </button>
        </div>

      </div>

    </div>
  )
}

export default AiHomePage