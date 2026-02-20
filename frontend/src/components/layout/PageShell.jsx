import { useState } from 'react'
import { Menu } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'
import { MobileDrawer } from './MobileDrawer'
import { IconButton } from '../ui/IconButton'

export function PageShell({ children, navItems = [], topItems = [], brand = 'MeshWork', brandTo = '/home' }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <Navbar
        brand={brand}
        brandTo={brandTo}
        navItems={topItems}
        rightSlot={(
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="md:hidden">
              <IconButton icon={Menu} ariaLabel="Open navigation" onClick={() => setMobileOpen(true)} />
            </div>
          </div>
        )}
      />

      <div style={{ display: 'flex', minHeight: 'calc(100vh - 68px)', alignItems: 'flex-start', paddingTop: '6px' }}>
        <div style={{ display: 'block' }} className="hidden md:block">
          <Sidebar
            items={navItems}
            brand={brand}
            brandTo={brandTo}
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed((prev) => !prev)}
          />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <main style={{ padding: '14px 24px 20px 24px' }}>
            {children}
          </main>
        </div>
      </div>

      <MobileDrawer open={mobileOpen} onClose={() => setMobileOpen(false)} items={navItems} />
    </div>
  )
}
