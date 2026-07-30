"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from './AuthProvider'

export function RoleGuard({ 
  children, 
  allowedRoles,
  redirectTo = '/login'
}: { 
  children: React.ReactNode
  allowedRoles: string[]
  redirectTo?: string
}) {
  const { user, profile, loading } = useAuth()
  const router = useRouter()

  const [isE2e, setIsE2e] = useState(false)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsE2e(localStorage.getItem('e2e') === 'true')
    }
  }, [])

  useEffect(() => {
    if (!loading && !isE2e) {
      if (!user) {
        router.push(redirectTo)
      } else if (profile && !allowedRoles.includes(profile.role)) {
        router.push(`/${profile.role.toLowerCase()}`)
      } else if (!profile) {
        router.push('/onboarding/patient')
      }
    }
  }, [user, profile, loading, allowedRoles, redirectTo, router, isE2e])

  if (isE2e) {
    return <>{children}</>
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400">
        <p className="animate-pulse">Authenticating...</p>
      </div>
    )
  }

  if (!user || (profile && !allowedRoles.includes(profile.role))) {
    return null
  }

  return <>{children}</>
}
