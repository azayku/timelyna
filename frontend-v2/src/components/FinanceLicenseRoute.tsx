import { useFinanceLicense } from '../features/finance/useFinanceLicense'
import FinanceLicenseGate from './FinanceLicenseGate'

interface FinanceLicenseRouteProps {
  children: React.ReactNode
}

export default function FinanceLicenseRoute({ children }: FinanceLicenseRouteProps) {
  const { isActive, isLoading, daysLeft } = useFinanceLicense()

  return (
    <>
      <FinanceLicenseGate isActive={isActive} isLoading={isLoading} daysLeft={daysLeft} />
      {isActive && !isLoading && <>{children}</>}
    </>
  )
}
