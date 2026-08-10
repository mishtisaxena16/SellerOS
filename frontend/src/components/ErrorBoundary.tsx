import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

// Catches render/lifecycle errors anywhere below it in the tree so one broken
// page can't blank out the whole app. This does not change any business logic —
// it only decides what renders when a child component throws.
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('SellerOS UI crash:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-app text-app min-h-screen flex items-center justify-center p-6">
          <div className="card max-w-sm w-full p-6 text-center">
            <div className="w-10 h-10 rounded-lg bg-accent-red-soft text-accent-red flex items-center justify-center mx-auto mb-3">
              <AlertTriangle size={18} />
            </div>
            <div className="text-[14px] font-semibold text-app mb-1">Something went wrong</div>
            <div className="text-[12.5px] text-dim mb-4">
              This part of SellerOS hit an unexpected error. You can try again, or head back to the dashboard.
            </div>
            <div className="flex items-center justify-center gap-2">
              <button onClick={this.handleReset} className="btn-ghost-app text-[12.5px] px-3 py-1.5">
                Try again
              </button>
              <a href="/dashboard" className="btn-primary-app text-[12.5px] px-3 py-1.5">
                Go to dashboard
              </a>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
