import { StrictMode, Component, ReactNode, ErrorInfo } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Application runtime error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#FFFFFF] flex items-center justify-center p-6 text-[#191919] font-sans">
          <div className="max-w-md w-full p-8 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] space-y-4">
            <h1 className="font-serif text-2xl text-[#191919]">Application notice</h1>
            <p className="text-xs text-[#191919]/70 leading-relaxed">
              {this.state.error?.message || 'An unexpected error occurred during rendering.'}
            </p>
            <div className="pt-2 flex gap-3">
              <button
                onClick={() => {
                  try {
                    localStorage.removeItem('creditpilot_user');
                    localStorage.removeItem('loansense_user');
                  } catch {}
                  window.location.reload();
                }}
                className="px-4 py-2 rounded bg-[#191919] text-white text-xs font-medium hover:bg-[#333333] transition-colors"
              >
                Reset session & reload
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 rounded bg-white border border-[#E5E5E5] text-[#191919] text-xs font-medium hover:bg-[#EAEAEA] transition-colors"
              >
                Reload page
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
