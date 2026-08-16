"use client"

import React, { useState, useEffect, useRef } from 'react'
import { api } from '@/lib/api'
import { ChatMessage } from '@/lib/types'
import { Send, Loader2, MessageSquare } from 'lucide-react'
import { useAuth } from '@/components/auth/AuthProvider'

interface ChatBoxProps {
  otherUserId: string
  otherUserName: string
}

export function ChatBox({ otherUserId, otherUserName }: ChatBoxProps) {
  const { profile } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  const fetchMessages = async () => {
    try {
      const data = await api.getChatMessages(otherUserId)
      setMessages(data)
    } catch (err) {
      console.error("Failed to fetch messages:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMessages()
    const interval = setInterval(fetchMessages, 3000)
    return () => clearInterval(interval)
  }, [otherUserId])

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }, [messages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return

    const tempContent = input.trim()
    setInput('')
    setSending(true)

    // Optimistic UI update
    if (profile) {
      const tempMsg: ChatMessage = {
        id: `temp-${Date.now()}`,
        sender_id: profile.id,
        receiver_id: otherUserId,
        content: tempContent,
        read: false,
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, tempMsg])
    }

    try {
      await api.sendChatMessage(otherUserId, tempContent)
      // fetch immediately after send
      await fetchMessages()
    } catch (err) {
      console.error("Failed to send message:", err)
      // fetch to sync original state on failure
      await fetchMessages()
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden flex flex-col h-[500px]">
      <div className="bg-slate-950 p-4 border-b border-slate-800 flex items-center">
        <MessageSquare className="w-5 h-5 text-emerald-500 mr-2" />
        <h3 className="text-lg font-bold text-slate-100">Chat with {otherUserName}</h3>
      </div>
      
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading && messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-slate-500" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-slate-500">
            No messages yet. Say hello!
          </div>
        ) : (
          messages.map(msg => {
            const isMe = msg.sender_id === profile?.id
            return (
              <div key={msg.id} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}>
                <div 
                  className={`max-w-[80%] px-4 py-2 rounded-2xl ${
                    isMe 
                      ? 'bg-emerald-100 text-emerald-950 rounded-tr-sm' 
                      : 'bg-slate-800 text-slate-700 rounded-tl-sm'
                  }`}
                >
                  {msg.content}
                </div>
                <span className="text-[10px] text-slate-500 mt-1 px-1">
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            )
          })
        )}
      </div>

      <form onSubmit={handleSend} className="p-4 bg-slate-950 border-t border-slate-800 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-full px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
        />
        <button
          type="submit"
          disabled={!input.trim() || sending}
          className="p-3 bg-emerald-600 hover:bg-emerald-500 rounded-full text-white transition-colors disabled:opacity-50"
        >
          {sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
        </button>
      </form>
    </div>
  )
}
