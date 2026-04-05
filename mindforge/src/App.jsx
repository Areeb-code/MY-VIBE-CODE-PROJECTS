import { useState, useRef, useEffect } from 'react'
import { Brain, Trash2, Play, Plus, Info, RefreshCw } from 'lucide-react'
import { neuralNetwork } from './NeuralNetwork'
import './index.css'

function App() {
  const [label, setLabel] = useState('')
  const [dataset, setDataset] = useState([])
  const [isTraining, setIsTraining] = useState(false)
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [isDrawing, setIsDrawing] = useState(false)

  const canvasRef = useRef(null)
  const ctxRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    canvas.width = 280
    canvas.height = 280

    const ctx = canvas.getContext('2d')
    ctx.lineCap = 'round'
    ctx.lineWidth = 15
    ctx.strokeStyle = 'white'
    ctxRef.current = ctx

    // Fill background with black
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
  }, [])

  const startDrawing = (e) => {
    setIsDrawing(true)
    draw(e)
  }

  const stopDrawing = () => {
    setIsDrawing(false)
    ctxRef.current.beginPath()

    // Auto-predict after drawing if trained
    if (neuralNetwork.model) {
      predict()
    }
  }

  const draw = (e) => {
    if (!isDrawing) return

    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX || e.touches[0].clientX) - rect.left
    const y = (e.clientY || e.touches[0].clientY) - rect.top

    ctxRef.current.lineTo(x, y)
    ctxRef.current.stroke()
    ctxRef.current.beginPath()
    ctxRef.current.moveTo(x, y)
  }

  const clearCanvas = () => {
    const canvas = canvasRef.current
    const ctx = ctxRef.current
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    setPrediction(null)
  }

  const addToDataset = () => {
    if (!label.trim()) {
      alert('Please enter a label for this drawing!')
      return
    }

    const canvas = canvasRef.current
    const dataUrl = canvas.toDataURL()

    // Create an offline canvas copy to store as data
    const offscreen = document.createElement('canvas')
    offscreen.width = 280
    offscreen.height = 280
    offscreen.getContext('2d').drawImage(canvas, 0, 0)

    setDataset([...dataset, { label, canvas: offscreen, preview: dataUrl }])
    clearCanvas()
  }

  const trainModel = async () => {
    if (dataset.length < 2) {
      alert('Add at least 2 different labels/drawings to start training!')
      return
    }

    setIsTraining(true)
    setTrainingStatus('Initializing MindForge...')

    await neuralNetwork.train(dataset, (epoch, logs) => {
      setTrainingStatus(`Training Epoch ${epoch + 1}: Loss ${logs.loss.toFixed(4)}`)
    })

    setIsTraining(false)
    setTrainingStatus('Training Complete! Try drawing something.')
  }

  const predict = () => {
    const res = neuralNetwork.predict(canvasRef.current)
    setPrediction(res)
  }

  return (
    <div className="mindforge-app">
      <header className="header">
        <h1>MindForge</h1>
        <p>The Ultimate Trainable AI System</p>
      </header>

      <main className="main-container">
        {/* Left Side: Training Zone */}
        <section className="panel">
          <h2 className="panel-title"><Brain /> Drawing Forge</h2>

          <div className="canvas-container">
            <canvas
              ref={canvasRef}
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              onTouchStart={startDrawing}
              onTouchMove={draw}
              onTouchEnd={stopDrawing}
            />

            <div className="controls">
              <input
                type="text"
                placeholder="Label (e.g., 'Circle', 'A', 'Fish')"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
              />
              <button onClick={addToDataset}>
                <Plus size={18} /> Add to Library
              </button>
              <button className="secondary" onClick={clearCanvas}>
                <Trash2 size={18} /> Clear
              </button>
            </div>

            {prediction && (
              <div className="prediction-result">
                <div className="prediction-confidence">
                  AI Perception: {(prediction.confidence * 100).toFixed(1)}% match
                </div>
                <div className="prediction-label">{prediction.label}</div>
              </div>
            )}
          </div>
        </section>

        {/* Right Side: intelligence & Control */}
        <section className="panel">
          <h2 className="panel-title"><Info /> Intelligence Hub</h2>

          <div className="controls" style={{ marginBottom: '2rem' }}>
            <button
              onClick={trainModel}
              disabled={isTraining || dataset.length < 2}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {isTraining ? <RefreshCw className="animate-spin" /> : <Play />}
              {isTraining ? 'Training Neural Core...' : 'Evolve Intelligence'}
            </button>
          </div>

          {trainingStatus && (
            <div className="training-status">
              <div>{trainingStatus}</div>
              {isTraining && (
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: '100%', animation: 'pulse 1.5s infinite' }}></div>
                </div>
              )}
            </div>
          )}

          <h3 style={{ marginTop: '2rem', color: '#4facfe' }}>Training Library ({dataset.length})</h3>
          <div className="dataset-preview">
            {dataset.map((item, idx) => (
              <div key={idx} className="dataset-item">
                <img src={item.preview} alt={item.label} />
                <span className="label-badge">{item.label}</span>
              </div>
            ))}
            {dataset.length === 0 && (
              <p style={{ color: '#444', fontStyle: 'italic', gridColumn: '1 / -1' }}>
                Your library is empty. Draw and add some patterns!
              </p>
            )}
          </div>
        </section>
      </main>

      <footer style={{ marginTop: '3rem', color: '#444', fontSize: '0.9rem' }}>
        Built with TensorFlow.js • Optimized for Real-time Learning
      </footer>
    </div>
  )
}

export default App
