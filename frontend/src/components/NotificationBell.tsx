"use client"

import { useState, useEffect, useRef } from "react"
import { Bell, Check, BellRing } from "lucide-react"
import { useAuth } from "@/components/auth/AuthProvider"
import { api, Notification } from "@/lib/api"
import { createClient } from "@/lib/supabase/client"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"

export default function NotificationBell() {
  const { profile } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!profile?.id) return

    const loadNotifications = async () => {
      try {
        const data = await api.getNotifications()
        setNotifications(data.items)
        setUnreadCount(data.unreadCount)
      } catch (err) {
        console.error("Failed to load notifications:", err)
      }
    }

    loadNotifications()

    const supabase = createClient()
    const channel = supabase
      .channel('schema-db-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${profile.id}`,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            const newNotif = {
              id: payload.new.id,
              userId: payload.new.user_id,
              title: payload.new.title,
              message: payload.new.message,
              type: payload.new.type,
              read: payload.new.read,
              createdAt: payload.new.created_at,
            }
            setNotifications((prev) => [newNotif, ...prev].slice(0, 50))
            if (!payload.new.read) {
              setUnreadCount((prev) => prev + 1)
            }
          } else if (payload.eventType === 'UPDATE') {
            setNotifications((prev) =>
              prev.map((n) =>
                n.id === payload.new.id ? { ...n, read: payload.new.read } : n
              )
            )
            // Recompute unread count
            setUnreadCount((prev) => {
              if (payload.old.read === false && payload.new.read === true) return Math.max(0, prev - 1)
              if (payload.old.read === true && payload.new.read === false) return prev + 1
              return prev
            })
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [profile?.id])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleMarkRead = async (id: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await api.markNotificationRead(id)
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)))
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (err) {
      console.error("Failed to mark read:", err)
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      setUnreadCount(0)
    } catch (err) {
      console.error("Failed to mark all read:", err)
    }
  }

  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        className="icon-button notification"
        aria-label="Notifications"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell size={19} />
        {unreadCount > 0 && <i>{unreadCount > 9 ? '9+' : unreadCount}</i>}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 mt-2 w-80 sm:w-96 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col"
            style={{ maxHeight: '80vh' }}
          >
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 backdrop-blur">
              <h3 className="font-semibold text-slate-100 flex items-center space-x-2">
                <BellRing size={16} className="text-blue-400" />
                <span>Notifications</span>
              </h3>
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors flex items-center space-x-1"
                >
                  <Check size={14} />
                  <span>Mark all read</span>
                </button>
              )}
            </div>

            <div className="overflow-y-auto flex-1">
              {notifications.length === 0 ? (
                <div className="p-8 text-center flex flex-col items-center justify-center">
                  <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center mb-3">
                    <Bell className="text-slate-500" size={20} />
                  </div>
                  <p className="text-slate-400 text-sm">You have no notifications</p>
                </div>
              ) : (
                <div className="flex flex-col">
                  {notifications.map((notif) => (
                    <Link
                      key={notif.id}
                      href={notif.type === 'new_prediction' ? '/doctor/patients' : '#'}
                      onClick={() => !notif.read && api.markNotificationRead(notif.id)}
                      className={`p-4 border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors block ${
                        !notif.read ? 'bg-slate-800/20' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 pr-4">
                          <h4 className={`text-sm mb-1 ${!notif.read ? 'font-semibold text-slate-100' : 'font-medium text-slate-300'}`}>
                            {notif.title}
                          </h4>
                          <p className="text-xs text-slate-400 line-clamp-2">{notif.message}</p>
                          <span className="text-[10px] text-slate-500 mt-2 block">{formatTime(notif.createdAt)}</span>
                        </div>
                        {!notif.read && (
                          <button
                            onClick={(e) => handleMarkRead(notif.id, e)}
                            className="p-1.5 bg-slate-800 rounded-md hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors shrink-0"
                            title="Mark as read"
                          >
                            <Check size={14} />
                          </button>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
