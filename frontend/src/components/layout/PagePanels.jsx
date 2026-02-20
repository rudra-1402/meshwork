export function MultiPaneLayout({
  panes,
  children,
  height = '100vh',
  backgroundColor = 'var(--bg-primary)',
  style,
}) {
  return (
    <div
      style={{
        display: 'flex',
        height,
        overflow: 'hidden',
        backgroundColor,
        position: 'relative',
        ...style,
      }}
    >
      {children}
      {panes.map((pane) => (
        <div
          key={pane.key}
          aria-hidden={pane.ariaHidden ? 'true' : undefined}
          style={{
            flex: pane.flex || '1 1 0',
            minWidth: pane.minWidth,
            display: 'flex',
            padding: pane.padding,
            backgroundColor: pane.backgroundColor ?? backgroundColor,
          }}
        >
          {pane.content}
        </div>
      ))}
    </div>
  )
}

export function PaneSurface({
  children,
  maxWidth,
  padding = '32px',
  borderRadius = '28px',
  backgroundColor = 'var(--bg-surface)',
  border,
  alignItems = 'center',
  justifyContent = 'center',
  overflowY = 'auto',
  style,
}) {
  return (
    <div
      style={{
        flex: 1,
        minWidth: 0,
        maxWidth,
        margin: '0 auto',
        borderRadius,
        backgroundColor,
        border,
        display: 'flex',
        alignItems,
        justifyContent,
        padding,
        overflowY,
        ...style,
      }}
    >
      {children}
    </div>
  )
}
