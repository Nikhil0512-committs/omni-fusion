/* eslint-disable react-hooks/static-components */
"use client"

import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { useAuth } from "@/components/auth/AuthProvider"
import { RoleGuard } from "@/components/auth/RoleGuard"
import NotificationBell from "@/components/NotificationBell"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Activity, LayoutDashboard, Users, FileText, LogOut, FilePlus, Bell,
  Menu, X, ChevronDown, PanelLeftClose, PanelLeftOpen, HeartPulse, MessageSquare
} from "lucide-react"

const pageNames: Record<string, string> = {
  patient: "Health overview", doctor: "Clinical overview", reports: "Medical reports",
  analytics: "Practice analytics", patients: "Patient directory", assessment: "New assessment",
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { profile, signOut } = useAuth()
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const isPatient = profile?.role === "PATIENT"
  const patientLinks = [
    { name: "Dashboard", href: "/patient", icon: LayoutDashboard },
    { name: "New Assessment", href: "/patient/assessment/new", icon: FilePlus },
    { name: "Reports", href: "/patient/reports", icon: FileText },
    { name: "My Doctor", href: "/patient/doctor", icon: Users },
  ]
  const doctorLinks = [
    { name: "Overview", href: "/doctor", icon: LayoutDashboard },
    { name: "Patients", href: "/doctor/patients", icon: Users },
    { name: "Messages", href: "/doctor/messages", icon: MessageSquare },
    { name: "Analytics", href: "/doctor/analytics", icon: Activity },
  ]
  const links = isPatient ? patientLinks : doctorLinks
  const segments = pathname.split("/").filter(Boolean)
  const title = pageNames[segments.at(-1) || ""] || (segments.length > 2 ? "Patient profile" : "Dashboard")

  const Sidebar = ({ mobile = false }: { mobile?: boolean }) => (
    <motion.aside
      initial={mobile ? { x: -320 } : false}
      animate={{ x: 0, width: mobile ? 288 : collapsed ? 88 : 264 }}
      exit={mobile ? { x: -320 } : undefined}
      transition={{ type: "spring", stiffness: 330, damping: 34 }}
      className={`dashboard-sidebar ${mobile ? "mobile-sidebar" : "desktop-sidebar"}`}
    >
      <div className="brand-row flex items-center justify-between">
        <Link href="/" title="Return to Landing Page" className="flex items-center space-x-2.5 hover:opacity-90 transition-opacity cursor-pointer">
          <div className="brand-mark"><HeartPulse size={21} /></div>
          {(!collapsed || mobile) && <span className="brand-name">Omni<span>Fusion</span></span>}
        </Link>
        {mobile && <button className="icon-button ml-auto" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={19}/></button>}
      </div>
      <div className="sidebar-content">
        {(!collapsed || mobile) && <p className="eyebrow">{isPatient ? "Patient workspace" : "Clinical workspace"}</p>}
        <nav className="sidebar-nav" aria-label="Primary navigation">
          {links.map(link => {
            const isDashboard = link.href === "/patient" || link.href === "/doctor"
            const active = isDashboard ? pathname === link.href : (pathname === link.href || pathname.startsWith(link.href + "/"))
            const Icon = link.icon
            return <Link key={link.name} href={link.href} title={collapsed && !mobile ? link.name : undefined}
              onClick={() => setMobileOpen(false)} className={active ? "nav-item active" : "nav-item"}>
              <Icon size={19}/>{(!collapsed || mobile) && <span>{link.name}</span>}
              {active && <motion.i layoutId={mobile ? "mobile-active" : "desktop-active"}/>}
            </Link>
          })}
        </nav>
        <div className="care-card">
          <span className="care-pulse"><Activity size={17}/></span>
          {(!collapsed || mobile) && <div><strong>AI monitoring</strong><small>All systems operational</small></div>}
        </div>
      </div>
      <div className="sidebar-footer">
        <button className="user-chip" onClick={() => setProfileOpen(!profileOpen)}>
          <span className="avatar">{profile?.full_name?.charAt(0) || "U"}</span>
          {(!collapsed || mobile) && <span className="user-copy"><strong>{profile?.full_name || "Your account"}</strong><small>{isPatient ? "Patient" : "Cardiologist"}</small></span>}
        </button>
        {!mobile && <button className="collapse-button" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">
          {collapsed ? <PanelLeftOpen size={18}/> : <PanelLeftClose size={18}/>} {(!collapsed) && <span>Collapse</span>}
        </button>}
      </div>
    </motion.aside>
  )

  return <RoleGuard allowedRoles={["PATIENT", "DOCTOR"]}>
    <div className="dashboard-shell">
      <Sidebar />
      <AnimatePresence>{mobileOpen && <><motion.button className="drawer-backdrop" aria-label="Close navigation" onClick={() => setMobileOpen(false)} initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}/><Sidebar mobile /></>}</AnimatePresence>
      <div className="dashboard-stage">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20}/></button>
          <div className="page-context"><span>{isPatient ? "My health" : "Workspace"} /</span><strong>{title}</strong></div>
          <div className="top-actions">
            <NotificationBell />
            <button className="top-profile" onClick={() => setProfileOpen(!profileOpen)}><span className="avatar">{profile?.full_name?.charAt(0) || "U"}</span><ChevronDown size={15}/></button>
          </div>
          <AnimatePresence>{profileOpen && <motion.div className="profile-menu" initial={{opacity:0,y:-8,scale:.97}} animate={{opacity:1,y:0,scale:1}} exit={{opacity:0,y:-8}}>
            <div><strong>{profile?.full_name || "Your account"}</strong><small>{isPatient ? "Patient account" : "Clinical account"}</small></div>
            <button onClick={signOut}><LogOut size={16}/> Sign out</button>
          </motion.div>}</AnimatePresence>
        </header>
        <motion.main key={pathname} className="dashboard-main" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:.42,ease:[.22,1,.36,1]}}>{children}</motion.main>
      </div>
    </div>
  </RoleGuard>
}
