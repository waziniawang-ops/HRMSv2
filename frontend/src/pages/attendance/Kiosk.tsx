import { useCallback, useEffect, useRef, useState } from 'react'
import * as faceapi from 'face-api.js'
import axios from 'axios'
import { CheckCircle, LogIn, LogOut, AlertCircle, Camera, RefreshCw, Clock } from 'lucide-react'

type KioskState = 'loading_models' | 'starting_camera' | 'scanning' | 'verifying' | 'result' | 'no_match' | 'camera_error' | 'model_error'

interface VerifyResult {
  match: boolean
  employee_name?: string
  employee_number?: string
  action?: 'CHECK_IN' | 'CHECK_OUT' | 'ALREADY_COMPLETE'
  check_in?: string
  check_out?: string
  message?: string
}

const MODELS_URL = '/models'
const RESULT_DISPLAY_MS = 4000
const NO_MATCH_DISPLAY_MS = 2500
const DEBOUNCE_DETECT_MS = 1200  // wait for stable face before calling API

export default function Kiosk() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const detectLoopRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastFaceAtRef = useRef<number>(0)
  const verifyingRef = useRef(false)

  const [kioskState, setKioskState] = useState<KioskState>('loading_models')
  const [result, setResult] = useState<VerifyResult | null>(null)
  const [clock, setClock] = useState(new Date())
  const [faceBox, setFaceBox] = useState<faceapi.Box | null>(null)

  // Live clock
  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    initKiosk()
    return () => teardown()
  }, [])

  async function initKiosk() {
    // Load models
    try {
      await Promise.all([
        faceapi.nets.ssdMobilenetv1.loadFromUri(MODELS_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODELS_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL),
      ])
    } catch {
      setKioskState('model_error')
      return
    }

    // Start camera
    setKioskState('starting_camera')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setKioskState('scanning')
      startDetectionLoop()
    } catch {
      setKioskState('camera_error')
    }
  }

  function teardown() {
    if (detectLoopRef.current) clearInterval(detectLoopRef.current)
    streamRef.current?.getTracks().forEach(t => t.stop())
  }

  function startDetectionLoop() {
    detectLoopRef.current = setInterval(async () => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState < 3 || video.videoWidth === 0 || video.paused || verifyingRef.current) return

      const detection = await faceapi
        .detectSingleFace(video, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.3 }))

      const ctx = canvas.getContext('2d')!
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      if (!detection) {
        lastFaceAtRef.current = 0
        setFaceBox(null)
        return
      }

      // Draw tracking box
      const box = detection.box
      setFaceBox(box)
      faceapi.matchDimensions(canvas, { width: video.videoWidth, height: video.videoHeight })
      const now = Date.now()
      const stable = lastFaceAtRef.current !== 0 && (now - lastFaceAtRef.current) >= DEBOUNCE_DETECT_MS

      // Draw box: green when stable, white when still detecting
      ctx.strokeStyle = stable ? '#22c55e' : '#ffffff'
      ctx.lineWidth = 3
      ctx.shadowColor = ctx.strokeStyle
      ctx.shadowBlur = 8
      ctx.strokeRect(box.x, box.y, box.width, box.height)
      ctx.shadowBlur = 0

      if (lastFaceAtRef.current === 0) lastFaceAtRef.current = now

      if (stable) {
        triggerVerify(video)
      }
    }, 250)
  }

  const triggerVerify = useCallback(async (video: HTMLVideoElement) => {
    if (verifyingRef.current) return
    verifyingRef.current = true
    lastFaceAtRef.current = 0
    setKioskState('verifying')

    try {
      const detection = await faceapi
        .detectSingleFace(video, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.3 }))
        .withFaceLandmarks()
        .withFaceDescriptor()

      if (!detection) {
        verifyingRef.current = false
        setKioskState('scanning')
        return
      }

      const descriptor = Array.from(detection.descriptor)
      const { data } = await axios.post<VerifyResult>('/api/v1/attendance/verify/', { descriptor })

      setResult(data)
      setKioskState(data.match ? 'result' : 'no_match')

      const delay = data.match ? RESULT_DISPLAY_MS : NO_MATCH_DISPLAY_MS
      setTimeout(() => {
        setResult(null)
        setFaceBox(null)
        verifyingRef.current = false
        setKioskState('scanning')
      }, delay)
    } catch {
      verifyingRef.current = false
      setKioskState('scanning')
    }
  }, [])

  const timeStr = clock.toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
  const dateStr = clock.toLocaleDateString('en-MY', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col select-none">
      {/* Header bar */}
      <div className="flex items-center justify-between px-8 py-4 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Camera size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-white leading-none">HRMSv2</p>
            <p className="text-[10px] text-gray-400 mt-0.5">Facial Attendance Kiosk</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-mono font-bold text-white">{timeStr}</p>
          <p className="text-sm text-gray-400">{dateStr}</p>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center gap-6 p-8">

        {/* Loading states */}
        {(kioskState === 'loading_models' || kioskState === 'starting_camera') && (
          <div className="flex flex-col items-center gap-4 text-center">
            <RefreshCw size={48} className="animate-spin text-blue-400" />
            <p className="text-xl font-medium text-gray-300">
              {kioskState === 'loading_models' ? 'Loading face recognition…' : 'Starting camera…'}
            </p>
          </div>
        )}

        {kioskState === 'model_error' && (
          <div className="flex flex-col items-center gap-4 text-center max-w-md">
            <AlertCircle size={48} className="text-red-400" />
            <p className="text-xl font-medium text-red-300">Failed to load face models</p>
            <p className="text-sm text-gray-400">Ensure the /models directory is accessible and reload the page.</p>
          </div>
        )}

        {kioskState === 'camera_error' && (
          <div className="flex flex-col items-center gap-4 text-center max-w-md">
            <AlertCircle size={48} className="text-red-400" />
            <p className="text-xl font-medium text-red-300">Camera unavailable</p>
            <p className="text-sm text-gray-400">Allow camera access and reload the page.</p>
          </div>
        )}

        {/* Camera + overlay */}
        {(kioskState === 'scanning' || kioskState === 'verifying' || kioskState === 'result' || kioskState === 'no_match') && (
          <div className="flex flex-col items-center gap-6 w-full max-w-2xl">
            {/* Video frame */}
            <div className="relative rounded-2xl overflow-hidden bg-gray-900 shadow-2xl border-2 border-gray-700 w-full">
              <video
                ref={videoRef}
                muted
                playsInline
                className="block w-full"
                style={{ maxHeight: '60vh', objectFit: 'cover' }}
              />
              <canvas
                ref={canvasRef}
                className="absolute inset-0 w-full h-full pointer-events-none"
                style={{ objectFit: 'cover' }}
              />

              {/* Verifying spinner overlay */}
              {kioskState === 'verifying' && (
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-3">
                    <RefreshCw size={36} className="animate-spin text-white" />
                    <p className="text-white font-medium">Identifying…</p>
                  </div>
                </div>
              )}
            </div>

            {/* Status message */}
            {kioskState === 'scanning' && (
              <div className="text-center">
                <p className="text-lg text-gray-300">
                  {faceBox ? 'Face detected — hold still…' : 'Position your face in the frame'}
                </p>
                <p className="text-sm text-gray-500 mt-1">Check-in and check-out are recorded automatically</p>
              </div>
            )}

            {/* Result card */}
            {kioskState === 'result' && result?.match && (
              <div className={`w-full rounded-2xl p-6 flex items-center gap-5 shadow-xl ${
                result.action === 'CHECK_IN' ? 'bg-green-900/80 border-2 border-green-500' :
                result.action === 'CHECK_OUT' ? 'bg-blue-900/80 border-2 border-blue-500' :
                'bg-gray-800 border-2 border-gray-600'
              }`}>
                <div className={`flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center ${
                  result.action === 'CHECK_IN' ? 'bg-green-500' :
                  result.action === 'CHECK_OUT' ? 'bg-blue-500' : 'bg-gray-600'
                }`}>
                  {result.action === 'CHECK_IN' ? <LogIn size={32} className="text-white" /> :
                   result.action === 'CHECK_OUT' ? <LogOut size={32} className="text-white" /> :
                   <CheckCircle size={32} className="text-white" />}
                </div>
                <div className="flex-1">
                  <p className="text-3xl font-bold text-white">{result.employee_name}</p>
                  <p className="text-sm text-gray-300 mt-0.5">{result.employee_number}</p>
                  <p className={`text-lg font-semibold mt-2 ${
                    result.action === 'CHECK_IN' ? 'text-green-300' :
                    result.action === 'CHECK_OUT' ? 'text-blue-300' : 'text-gray-300'
                  }`}>
                    {result.action === 'CHECK_IN' && `✓ Checked in at ${result.check_in}`}
                    {result.action === 'CHECK_OUT' && `✓ Checked out at ${result.check_out}`}
                    {result.action === 'ALREADY_COMPLETE' && 'Already checked in and out today'}
                  </p>
                  {result.action === 'CHECK_OUT' && result.check_in && (
                    <p className="text-sm text-blue-200 mt-0.5">Check-in was at {result.check_in}</p>
                  )}
                </div>
              </div>
            )}

            {/* No match card */}
            {kioskState === 'no_match' && (
              <div className="w-full rounded-2xl p-6 flex items-center gap-5 bg-red-900/80 border-2 border-red-500 shadow-xl">
                <div className="flex-shrink-0 w-16 h-16 rounded-full bg-red-500 flex items-center justify-center">
                  <AlertCircle size={32} className="text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">Face Not Recognised</p>
                  <p className="text-sm text-red-200 mt-1">Please see HR to register your face for attendance.</p>
                </div>
              </div>
            )}

            {/* Scan hint with clock icon when stable */}
            {kioskState === 'scanning' && !faceBox && (
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <Clock size={14} />
                <span>Ready to scan</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
