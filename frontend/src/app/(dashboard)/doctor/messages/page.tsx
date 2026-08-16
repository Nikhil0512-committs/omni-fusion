"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/components/auth/AuthProvider"
import { api } from "@/lib/api"
import { ChatBox } from "@/components/ChatBox"
import { Loader2, MessageSquare, User } from "lucide-react"

export default function GlobalInboxPage() {
  const { profile } = useAuth()
  const [patients, setPatients] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPatient, setSelectedPatient] = useState<any | null>(null)

  useEffect(() => {
    async function loadPatients() {
      try {
        const links = await api.getPatients()
        const accepted = links.filter(l => l.status === 'accepted' && l.profiles?.role === 'PATIENT')
        setPatients(accepted.map(l => l.profiles))
      } catch (err) {
        console.error("Failed to load patients", err)
      } finally {
        setLoading(false)
      }
    }
    loadPatients()
  }, [])

  if (loading) {
    return <div className="flex h-[calc(100vh-100px)] items-center justify-center"><Loader2 className="w-8 h-8 text-indigo-500 animate-spin" /></div>
  }

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-100px)] flex flex-col">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Global Inbox</h1>
        <p className="text-slate-500">Manage direct messages with all your connected patients.</p>
      </div>

      <div className="flex-1 bg-white border border-slate-200 rounded-2xl overflow-hidden flex flex-col md:flex-row shadow-xl">
        
        {/* Sidebar: Patient List */}
        <div className="w-full md:w-80 bg-slate-50 border-b md:border-b-0 md:border-r border-slate-200 flex flex-col">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider flex items-center">
              <MessageSquare className="w-4 h-4 mr-2" />
              Connected Patients
            </h2>
          </div>
          
          <div className="overflow-y-auto flex-1 p-2 space-y-1">
            {patients.length === 0 ? (
              <div className="p-4 text-center text-slate-500 text-sm">No connected patients.</div>
            ) : (
              patients.map(p => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPatient(p)}
                  className={`w-full text-left p-3 rounded-lg flex items-center transition-colors ${selectedPatient?.id === p.id ? 'bg-emerald-100 text-emerald-900' : 'hover:bg-slate-200 text-slate-700'}`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 shrink-0 ${selectedPatient?.id === p.id ? 'bg-emerald-200 text-emerald-700' : 'bg-slate-200 text-slate-500'}`}>
                    <User className="w-5 h-5" />
                  </div>
                  <div className="truncate">
                    <p className="font-medium truncate">{p.fullName || 'Unknown Patient'}</p>
                    <p className={`text-xs truncate ${selectedPatient?.id === p.id ? 'text-emerald-700' : 'text-slate-500'}`}>{p.email || 'No email'}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Main Content: Chat Box */}
        <div className="flex-1 flex flex-col bg-white overflow-hidden relative">
          {selectedPatient ? (
            <div className="flex-1 overflow-hidden h-full">
              <ChatBox otherUserId={selectedPatient.id} otherUserName={selectedPatient.fullName || 'Patient'} />
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">Select a Conversation</h3>
              <p className="text-slate-500 max-w-sm">Choose a patient from the list on the left to start viewing or sending messages securely.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
