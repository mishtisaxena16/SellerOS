import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'
import { Loader2 } from 'lucide-react'

export default function Login() {
  const { login, error, clearError } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const from = (location.state as { from?: string })?.from || '/dashboard'

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    clearError()
    const trimmedEmail = email.trim()
    if (!trimmedEmail || !password) return
    setSubmitting(true)
    try {
      await login(trimmedEmail, password)
      navigate(from, { replace: true })
    } catch {
      // error is surfaced via AuthContext.error
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Login"
      footer={<>New to SellerOS? <Link to="/register" className="text-accent-blue">Create an account</Link></>}
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div>
          <label htmlFor="login-email" className="block text-[13px] text-dim mb-1.5">Email</label>
          <input
            id="login-email"
            type="email" required autoFocus value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@business.com"
            autoComplete="email"
            disabled={submitting}
            className="input-app w-full px-3.5 py-2.5 text-[14px] disabled:opacity-60"
          />
        </div>
        <div>
          <label htmlFor="login-password" className="block text-[13px] text-dim mb-1.5">Password</label>
          <input
            id="login-password"
            type="password" required value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            disabled={submitting}
            className="input-app w-full px-3.5 py-2.5 text-[14px] disabled:opacity-60"
          />
        </div>
        {error && <div role="alert" aria-live="assertive" className="text-[13px] text-accent-red">{error}</div>}
        <button type="submit" disabled={submitting} className="btn-primary-app w-full py-2.5 text-[14px] mt-2 flex items-center justify-center gap-2">
          {submitting && <Loader2 size={15} className="animate-spin" />}
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>
    </AuthLayout>
  )
}
