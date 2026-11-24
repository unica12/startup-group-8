export default function Card({ as: Tag = 'div', className = '', padding = 'p-5', children, ...props }) {
  return (
    <Tag
      className={`bg-surface border border-line rounded-card shadow-card ${padding} ${className}`}
      {...props}
    >
      {children}
    </Tag>
  );
}
