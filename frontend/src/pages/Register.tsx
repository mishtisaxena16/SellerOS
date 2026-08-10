import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'
import { Loader2 } from 'lucide-react'

export default function Register() {
  const { register, error, clearError } = useAuth()
  const navigate = useNavigate()
  const [businessName, setBusinessName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    clearError()
    setFormError(null)
    const trimmedBusinessName = businessName.trim()
    const trimmedEmail = email.trim()
    if (!trimmedBusinessName) {
      setFormError('Business name cannot be empty.')
      return
    }
    if (password.length < 8) {
      setFormError('Password must be at least 8 characters.')
      return
    }
    setSubmitting(true)
    try {
      await register(trimmedEmail, password, trimmedBusinessName)
      // Brand new sellers land on the dashboard, which shows a welcome
      // state with next steps — connecting a marketplace is one option
      // among several, not a forced gate before they can use anything.
      navigate('/dashboard', { replace: true })
    } catch {
      // error is surfaced via AuthContext.error
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Get started"
      footer={<>Already have an account? <Link to="/login" className="text-accent-blue">Log in</Link></>}
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div>
          <label htmlFor="register-business-name" className="block text-[13px] text-dim mb-1.5">Business name</label>
          <input
            id="register-business-name"
            type="text" required autoFocus value={businessName}
            onChange={e => setBusinessName(e.target.value)}
            placeholder="Your store or company name"
            autoComplete="organization"
            maxLength={100}
            disabled={submitting}
            className="input-app w-full px-3.5 py-2.5 text-[14px] disabled:opacity-60"
          />
        </div>
        <div>
          <label htmlFor="register-email" className="block text-[13px] text-dim mb-1.5">Email</label>
          <input
            id="register-email"
            type="email" required value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@business.com"
            autoComplete="email"
            disabled={submitting}
            className="input-app w-full px-3.5 py-2.5 text-[14px] disabled:opacity-60"
          />
        </div>
        <div>
          <label htmlFor="register-password" className="block text-[13px] text-dim mb-1.5">Password</label>
          <input
            id="register-password"
            type="password" required minLength={8} value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            disabled={submitting}
            className="input-app w-full px-3.5 py-2.5 text-[14px] disabled:opacity-60"
          />
        </div>
        {(formError || error) && <div role="alert" aria-live="assertive" className="text-[13px] text-accent-red">{formError || error}</div>}
        <button type="submit" disabled={submitting} className="btn-primary-app w-full py-2.5 text-[14px] mt-2 flex items-center justify-center gap-2">
          {submitting && <Loader2 size={15} className="animate-spin" />}
          {submitting ? 'Creating account…' : "Get started — it's free"}
        </button>
      </form>
    </AuthLayout>
  )
}
