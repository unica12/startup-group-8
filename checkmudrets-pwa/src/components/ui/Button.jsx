const VARIANTS = {
  primary: 'bg-brand text-white hover:bg-brand-hover',
  secondary: 'bg-white text-text border border-line-strong hover:border-brand',
  ghost: 'bg-pill text-text hover:bg-line',
  danger: 'bg-danger text-white hover:bg-danger/90',
};

const SIZES = {
  md: 'min-h-[52px] px-[22px] py-[15px] text-sm',
  sm: 'min-h-[40px] px-4 py-2 text-[13px]',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  full = false,
  className = '',
  children,
  type = 'button',
  ...props
}) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-btn font-extrabold leading-tight
        cursor-pointer transition-[transform,box-shadow,background-color,border-color] duration-200
        hover:-translate-y-0.5 hover:shadow-hover active:translate-y-0
        disabled:opacity-50 disabled:pointer-events-none
        ${VARIANTS[variant]} ${SIZES[size]} ${full ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
