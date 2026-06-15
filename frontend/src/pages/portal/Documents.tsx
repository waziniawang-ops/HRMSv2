import { useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { FileText, Upload, Trash2, Download } from 'lucide-react'
import { PortalLayout } from './PortalLayout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import portalApi from '@/lib/portalApi'
import { fmt } from '@/lib/utils'

interface Doc {
  id: string
  doc_type: string
  name: string
  file: string
  file_url: string
  uploaded_at: string
}

const DOC_TYPES = [
  { value: 'RESUME', label: 'Resume / CV' },
  { value: 'COVER_LETTER', label: 'Cover Letter' },
  { value: 'ACADEMIC_CERT', label: 'Academic Certificate' },
  { value: 'IDENTITY', label: 'Identity Document' },
  { value: 'PORTFOLIO', label: 'Portfolio' },
  { value: 'OTHER', label: 'Other' },
]

const DOC_COLORS: Record<string, string> = {
  RESUME: 'bg-blue-50 text-blue-700',
  COVER_LETTER: 'bg-purple-50 text-purple-700',
  ACADEMIC_CERT: 'bg-green-50 text-green-700',
  IDENTITY: 'bg-orange-50 text-orange-700',
  PORTFOLIO: 'bg-pink-50 text-pink-700',
  OTHER: 'bg-gray-50 text-gray-700',
}

export default function PortalDocuments() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const docTypeRef = useRef<HTMLSelectElement>(null)
  const nameRef = useRef<HTMLInputElement>(null)

  const { data, isLoading } = useQuery<{ count: number; results: Doc[] }>({
    queryKey: ['portal-docs'],
    queryFn: () => portalApi.get('/recruitment/my-documents/').then(r => r.data),
  })

  const upload = useMutation({
    mutationFn: (fd: FormData) => portalApi.post('/recruitment/my-documents/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
    onSuccess: () => {
      toast.success('Document uploaded')
      qc.invalidateQueries({ queryKey: ['portal-docs'] })
      if (fileRef.current) fileRef.current.value = ''
      if (nameRef.current) nameRef.current.value = ''
    },
    onError: () => toast.error('Upload failed'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => portalApi.delete(`/recruitment/my-documents/${id}/`),
    onSuccess: () => { toast.success('Document removed'); qc.invalidateQueries({ queryKey: ['portal-docs'] }) },
    onError: () => toast.error('Delete failed'),
  })

  function handleUpload() {
    const file = fileRef.current?.files?.[0]
    const docType = docTypeRef.current?.value || 'OTHER'
    const name = nameRef.current?.value?.trim() || file?.name || 'Document'
    if (!file) { toast.error('Please select a file'); return }
    const fd = new FormData()
    fd.append('file', file)
    fd.append('doc_type', docType)
    fd.append('name', name)
    upload.mutate(fd)
  }

  return (
    <PortalLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Documents</h1>
        <p className="text-sm text-gray-500 mt-1">Upload your CV, certificates, and other supporting documents</p>
      </div>

      {/* Upload card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Upload New Document</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Document Type</label>
            <select ref={docTypeRef} defaultValue="RESUME"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
              {DOC_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Document Name</label>
            <input ref={nameRef} placeholder="e.g. My Resume 2024"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">File</label>
            <input ref={fileRef} type="file" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 file:mr-3 file:text-xs file:font-medium file:border-0 file:bg-blue-50 file:text-blue-700 file:rounded file:px-2 file:py-1" />
          </div>
        </div>
        <Button onClick={handleUpload} loading={upload.isPending}>
          <Upload size={15} /> Upload Document
        </Button>
        <p className="text-xs text-gray-400 mt-2">Accepted: PDF, Word (.doc/.docx), JPG, PNG — Max 10 MB</p>
      </div>

      {/* Documents list */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Uploaded Documents</h2>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner className="h-6 w-6" /></div>
        ) : !data?.results?.length ? (
          <div className="text-center py-16 text-gray-400">
            <FileText size={36} className="mx-auto mb-2 opacity-30" />
            <p className="text-gray-600 font-medium">No documents uploaded yet</p>
            <p className="text-sm mt-1">Upload your CV to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {data.results.map((doc) => {
              const typeLabel = DOC_TYPES.find(t => t.value === doc.doc_type)?.label ?? doc.doc_type
              return (
                <div key={doc.id} className="px-5 py-4 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-gray-50 border border-gray-200 flex items-center justify-center shrink-0">
                    <FileText size={18} className="text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{doc.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${DOC_COLORS[doc.doc_type] ?? 'bg-gray-50 text-gray-600'}`}>
                        {typeLabel}
                      </span>
                      <span className="text-xs text-gray-400">Uploaded {fmt(doc.uploaded_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {doc.file_url && (
                      <a href={doc.file_url} target="_blank" rel="noopener noreferrer"
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Download">
                        <Download size={15} />
                      </a>
                    )}
                    <button
                      onClick={() => { if (window.confirm(`Delete "${doc.name}"?`)) remove.mutate(doc.id) }}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </PortalLayout>
  )
}
