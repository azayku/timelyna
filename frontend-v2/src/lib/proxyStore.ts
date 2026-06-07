import { create } from 'zustand'

interface ProxiedEmployee {
  id: number
  name: string
  email: string
}

interface ProxyState {
  isProxy: boolean
  proxiedEmployee: ProxiedEmployee | null
  proxyLogId: number | null
  proxyToken: string | null
  startProxy: (emp: ProxiedEmployee, logId: number, token: string) => void
  endProxy: () => void
}

export const useProxyStore = create<ProxyState>(set => ({
  isProxy: false,
  proxiedEmployee: null,
  proxyLogId: null,
  proxyToken: null,
  startProxy: (emp, logId, token) =>
    set({ isProxy: true, proxiedEmployee: emp, proxyLogId: logId, proxyToken: token }),
  endProxy: () =>
    set({ isProxy: false, proxiedEmployee: null, proxyLogId: null, proxyToken: null }),
}))
