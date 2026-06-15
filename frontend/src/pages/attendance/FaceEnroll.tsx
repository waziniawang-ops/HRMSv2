import { useEffect, useRef, useState } from 'react'
import * as faceapi from 'face-api.js'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Camera, UserCheck, Trash2, RefreshCw } from 'lucide-react'
import api from '@/lib/api'

interface Employee { id: string; employee_number: string; full_name: string }
interface FaceRecord { id: string; employee: string; employee_name: string; employee_number: string; enrolled_at: string }
interface ApiList<T> { count: number; results: T[] }

type Phase = 'idle' | 'loading_models' | 'starting_camera' | 'ready' | 'capturing' | 'processing' | 'done' | 'error'

const SAMPLES_NEEDED = 5
const MODELS_URL = '/models'

export default function FaceEnroll() {
  const qc = useQueryClient()

  // Refs — video & canvas are ALWAYS mounted in the DOM so refs are never null
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isDetectingRef = useRef(false)

  const [phase, setPhase] = useState<Phase>('idle')
  const [selectedEmployee, setSelectedEmployee] = useState('')
  const [capturedDescriptors, setCapturedDescriptors] = useState<number[][]>([])
  const [modelsLoaded, setModelsLoaded] = useState(false)
  const [faceDetected, setFaceDetected] = useState(false)

  const { data: employees } = useQuery<ApiList<Employee>>({
    queryKey: ['employees-all'],
    queryFn: () => api.get('/core/employees/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: enrolled, isLoading: enrolledLoading } = useQuery<ApiList<FaceRecord>>({
    queryKey: ['face-descriptors'],
    queryFn: () => api.get('/attendance/faces/').then(r => r.data),
  })

  const enroll = useMutation({
    mutationFn: (body: { employee: string; descriptor: number[] }) => api.post('/attendance/faces/', body),
    onSuccess: () => {
      toast.success('Face enrolled successfully')
      qc.invalidateQueries({ queryKey: ['face-descriptors'] })
      stopCamera()
      setPhase('done')
      setCapturedDescriptors([])
      setSelectedEmployee('')
    },
    onError: () => toast.error('Failed to save face data'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/attendance/faces/${id}/`),
    onSuccess: () => { toast.success('Face removed'); qc.invalidateQueries({ queryKey: ['face-descriptors'] }) },
    onError: () => toast.error('Failed to remove face'),
  })

  useEffect(() => {
    loadModels()
    return () => stopCamera()
  }, [])

  async function loadModels() {
    if (modelsLoaded) return
    setPhase('loading_models')
    try {
      await Promise.all([
        faceapi.nets.ssdMobilenetv1.loadFromUri(MODELS_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODELS_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL),
      ])
      setModelsLoaded(true)
      setPhase('idle')
    } catch {
      toast.error('Failed to load face detection models')
      setPhase('error')
    }
  }

  async function startCamera() {
    if (!selectedEmployee) { toast.error('Select an employee first'); return }
    setPhase('starting_camera')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      })
      streamRef.current = stream

      // videoRef is always mounted — safe to set srcObject immediately
      const video = videoRef.current!
      video.srcObject = stream
      await video.play()

      setCapturedDescriptors([])
      setFaceDetected(false)
      setPhase('ready')
      startDetectionLoop()
    } catch {
      toast.error('Camera access denied or unavailable.')
      setPhase('idle')
    }
  }

  function stopCamera() {
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null }
    isDetectingRef.current = false
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
    if (videoRef.current) { videoRef.current.srcObject = null }
    clearCanvas()
    setFaceDetected(false)
  }

  function clearCanvas() {
    const c = canvasRef.current
    if (c) c.getContext('2d')?.clearRect(0, 0, c.width, c.height)
  }

  function startDetectionLoop() {
    intervalRef.current = setInterval(async () => {
      if (isDetectingRef.current) return
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState < 3 || video.videoWidth === 0 || video.paused) return

      isDetectingRef.current = true
      try {
        const det = await faceapi.detectSingleFace(
          video,
          new faceapi.SsdMobilenetv1Options({ minConfidence: 0.3 })
        )

        if (!det) { setFaceDetected(false); clearCanvas(); return }

        setFaceDetected(true)
        const size = { width: video.videoWidth, height: video.videoHeight }
        faceapi.matchDimensions(canvas, size)
        const ctx = canvas.getContext('2d')!
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.strokeStyle = '#22c55e'
        ctx.lineWidth = 3
        ctx.strokeRect(det.box.x, det.box.y, det.box.width, det.box.height)
        ctx.fillStyle = 'rgba(34,197,94,0.12)'
        ctx.fillRect(det.box.x, det.box.y, det.box.width, det.box.height)
      } finally {
        isDetectingRef.current = false
      }
    }, 300)
  }

  async function captureFrame(): Promise<number[] | null> {
    const video = videoRef.current
    if (!video || video.videoWidth === 0) return null
    const det = await faceapi
      .detectSingleFace(video, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.3 }))
      .withFaceLandmarks()
      .withFaceDescriptor()
    return det ? Array.from(det.descriptor) : null
  }

  async function handleCapture() {
    setPhase('capturing')
    const samples: number[][] = []

    for (let i = 0; i < SAMPLES_NEEDED; i++) {
      await new Promise(r => setTimeout(r, 700))
      const descriptor = await captureFrame()
      if (descriptor) { samples.push(descriptor); setCapturedDescriptors(prev => [...prev, descriptor]) }
    }

    if (samples.length < 3) {
      toast.error('Could not capture enough samples. Ensure good lighting and face the camera directly.')
      setPhase('ready')
      return
    }

    setPhase('processing')
    const averaged = Array.from({ length: 128 }, (_, i) =>
      samples.reduce((sum, s) => sum + s[i], 0) / samples.length
    )
    enroll.mutate({ employee: selectedEmployee, descriptor: averaged })
  }

  function handleReset() {
    stopCamera()
    setPhase('idle')
    setCapturedDescriptors([])
    setSelectedEmployee('')
  }

  function fmtDate(dt: string) {
    return new Date(dt).toLocaleString('en-MY', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const cameraActive = phase === 'ready' || phase === 'capturing' || phase === 'processing'

  return (
    <AppLayout title="Face Enrolment">
      <div className="space-y-6">
        <Card>
          <CardHeader><CardTitle>Enrol Employee Face</CardTitle></CardHeader>
          <CardContent className="p-6 space-y-5">

            {phase === 'loading_models' && (
              <div className="flex items-center gap-3 text-blue-600 text-sm">
                <RefreshCw size={16} className="animate-spin" />
                Loading face recognition models — first load may take ~10 seconds…
              </div>
            )}

            {phase === 'error' && (
              <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">
                Failed to load face detection models. Ensure the <code>/models</code> directory is accessible and reload.
              </div>
            )}

            {phase === 'done' && (
              <div className="flex items-center gap-3 p-4 bg-green-50 rounded-xl text-green-700">
                <UserCheck size={20} />
                <div>
                  <p className="font-semibold">Enrolment complete</p>
                  <p className="text-sm">Face saved — employee can now check in at the kiosk.</p>
                </div>
                <Button variant="secondary" onClick={() => setPhase('idle')} className="ml-auto">Enrol Another</Button>
              </div>
            )}

            {phase !== 'loading_models' && phase !== 'error' && phase !== 'done' && (
              <>
                {/* Employee selector + action button */}
                <div className="flex items-end gap-4">
                  <div className="flex-1">
                    <Select
                      label="Select Employee"
                      value={selectedEmployee}
                      onChange={e => setSelectedEmployee(e.target.value)}
                      disabled={cameraActive}
                    >
                      <option value="">— Choose Employee —</option>
                      {employees?.results.map(e => (
                        <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>
                      ))}
                    </Select>
                  </div>
                  {!cameraActive ? (
                    <Button onClick={startCamera} disabled={!selectedEmployee || !modelsLoaded}>
                      <Camera size={16} /> Start Camera
                    </Button>
                  ) : (
                    <Button variant="secondary" onClick={handleReset}>Cancel</Button>
                  )}
                </div>

                {/* Video — ALWAYS in the DOM so videoRef is never null.
                    Visibility toggled via CSS only. */}
                <div className={cameraActive ? 'block space-y-4' : 'hidden'}>
                  <div className="relative rounded-xl overflow-hidden bg-gray-900 border border-gray-200 w-fit">
                    <video
                      ref={videoRef}
                      muted
                      playsInline
                      className="block"
                      style={{ width: 480, height: 360 }}
                    />
                    {/* Canvas overlay — dimensions updated by matchDimensions on every frame */}
                    <canvas
                      ref={canvasRef}
                      className="absolute inset-0 pointer-events-none"
                      style={{ width: 480, height: 360 }}
                    />
                  </div>

                  {/* Status row */}
                  <div className="flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full transition-colors ${faceDetected ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <span className="text-sm text-gray-600">
                        {faceDetected ? 'Face detected — ready to capture' : 'Looking for face…'}
                      </span>
                    </div>
                    {phase === 'capturing' && (
                      <span className="text-sm text-blue-600 font-medium">
                        Capturing {capturedDescriptors.length}/{SAMPLES_NEEDED}…
                      </span>
                    )}
                    {phase === 'processing' && (
                      <span className="text-sm text-orange-600 font-medium">Processing…</span>
                    )}
                  </div>

                  {/* Progress bar during capture */}
                  {phase === 'capturing' && (
                    <div className="flex gap-2">
                      {Array.from({ length: SAMPLES_NEEDED }).map((_, i) => (
                        <div
                          key={i}
                          className={`h-2 flex-1 rounded-full transition-colors ${i < capturedDescriptors.length ? 'bg-green-500' : 'bg-gray-200'}`}
                        />
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-3">
                    <Button
                      onClick={handleCapture}
                      disabled={phase !== 'ready' || !faceDetected}
                      loading={phase === 'capturing' || phase === 'processing' || enroll.isPending}
                    >
                      <UserCheck size={16} /> Capture &amp; Enrol
                    </Button>
                    <p className="text-xs text-gray-500">
                      Face the camera directly. {SAMPLES_NEEDED} samples are taken automatically.
                    </p>
                  </div>
                </div>

                {phase === 'starting_camera' && (
                  <div className="flex items-center gap-3 text-gray-500 text-sm">
                    <RefreshCw size={15} className="animate-spin" />
                    Starting camera…
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Enrolled Faces Table */}
        <Card>
          <CardHeader><CardTitle>Enrolled Faces</CardTitle></CardHeader>
          {enrolledLoading ? <PageSpinner /> : !enrolled?.results?.length ? (
            <EmptyState icon={Camera} title="No faces enrolled" description="Enrol employees above to enable facial check-in." />
          ) : (
            <Table>
              <Thead>
                <tr><Th>Employee</Th><Th>Number</Th><Th>Enrolled At</Th><Th>Status</Th><Th></Th></tr>
              </Thead>
              <Tbody>
                {enrolled.results.map(f => (
                  <Tr key={f.id}>
                    <Td className="font-medium text-gray-900">{f.employee_name}</Td>
                    <Td><span className="font-mono text-xs text-gray-600">{f.employee_number}</span></Td>
                    <Td className="text-sm text-gray-500">{fmtDate(f.enrolled_at)}</Td>
                    <Td><Badge status="ACTIVE" label="Enrolled" /></Td>
                    <Td>
                      <button
                        onClick={() => { if (window.confirm(`Remove face data for ${f.employee_name}?`)) remove.mutate(f.id) }}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Remove"
                      >
                        <Trash2 size={15} />
                      </button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
