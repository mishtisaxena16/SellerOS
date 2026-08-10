import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

export default function AuthLayout({
  title, subtitle, children, footer,
}: {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}) {
  return (
    <div className="bg-app text-app min-h-screen font-sans flex flex-col">
      <div className="px-6 md:px-10 h-[76px] flex items-center border-b border-app">
        <Link to="/" className="flex items-center gap-2.5 font-bold text-[17px] tracking-tight">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L21 7V17L12 22L3 17V7L12 2Z" stroke="#3b82f6" strokeWidth="1.6" />
          </svg>
          SellerOS
        </Link>
      </div>
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-[400px]">
          <div className="eyebrow-app mb-5">{subtitle}</div>
          <h1 className="text-[24px] sm:text-[28px] font-semibold tracking-[-0.02em] mb-6 sm:mb-8">{title}</h1>
          <div className="card p-5 sm:p-7">{children}</div>
          <div className="text-center mt-6 text-[14px] text-dim">{footer}</div>
        </div>
      </div>
    </div>
  )
}
