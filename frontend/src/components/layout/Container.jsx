export function Container({ children, maxWidth = '1200px', className = '', style }) {
  return (
    <div
      className={className}
      style={{
        width: '100%',
        maxWidth,
        marginInline: 'auto',
        paddingInline: '24px',
        ...style,
      }}
    >
      {children}
    </div>
  )
}
