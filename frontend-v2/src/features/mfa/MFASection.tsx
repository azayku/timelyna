import { useState } from 'react'
import { Shield, ShieldCheck, ShieldOff } from 'lucide-react'
import { useMFAStatus, useSetupMFA, useEnableMFA, useDisableMFA } from './hooks'
import { swalDark } from '../../lib/swalConfig'
import Swal from 'sweetalert2'
import Card, { CardHeader } from '../../components/ui/Card'
import Button from '../../components/ui/Button'

export default function MFASection() {
  const { data: status } = useMFAStatus()
  const setupMutation = useSetupMFA()
  const enableMutation = useEnableMFA()
  const disableMutation = useDisableMFA()
  const [setupData, setSetupData] = useState<{ secret: string; qr_code_base64: string } | null>(null)
  const [code, setCode] = useState('')

  const handleSetup = async () => {
    try {
      const data = await setupMutation.mutateAsync()
      setSetupData(data)
    } catch {
      void swalDark({ icon: 'error', title: 'Erreur', text: 'Impossible de générer le QR code MFA.' })
    }
  }

  const handleEnable = async () => {
    try {
      await enableMutation.mutateAsync(code)
      setSetupData(null)
      setCode('')
      void swalDark({ icon: 'success', title: 'MFA activé', text: 'Votre compte est maintenant protégé par 2FA.' })
    } catch {
      void swalDark({ icon: 'error', title: 'Code invalide', text: 'Vérifiez votre application authenticator.' })
    }
  }

  const handleDisable = async () => {
    const result = await Swal.fire({
      title: 'Désactiver le MFA ?',
      html: '<p class="text-sm text-slate-600 dark:text-slate-400">Entrez votre code TOTP pour confirmer</p><input id="mfa-code" class="mt-2 w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-center text-lg tracking-widest bg-white dark:bg-slate-700 text-slate-800 dark:text-white" placeholder="000000" maxlength="6" />',
      showCancelButton: true,
      confirmButtonText: 'Désactiver',
      cancelButtonText: 'Annuler',
      confirmButtonColor: '#ef4444',
      background: document.documentElement.classList.contains('dark') ? '#1e293b' : '#ffffff',
      color: document.documentElement.classList.contains('dark') ? '#ffffff' : '#0f172a',
      preConfirm: () => {
        const input = document.getElementById('mfa-code') as HTMLInputElement
        return input?.value || ''
      },
    })
    if (result.isConfirmed && result.value) {
      try {
        await disableMutation.mutateAsync(result.value)
        void swalDark({ icon: 'success', title: 'MFA désactivé' })
      } catch {
        void swalDark({ icon: 'error', title: 'Code invalide' })
      }
    }
  }

  return (
    <Card>
      <CardHeader title="Authentification à deux facteurs (2FA)" />
      <div className="space-y-4">
        <div className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
          {status?.mfa_enabled ? (
            <ShieldCheck className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
          ) : (
            <Shield className="h-6 w-6 text-slate-400 flex-shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <h3 className="font-semibold text-slate-800 dark:text-white text-sm">
              {status?.mfa_enabled ? 'MFA activé' : 'MFA désactivé'}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {status?.mfa_enabled 
                ? 'Votre compte est protégé par une authentification à deux facteurs' 
                : 'Renforcez la sécurité de votre compte en activant le 2FA'}
            </p>
          </div>
        </div>

        {status?.mfa_enabled ? (
          <div className="flex justify-end pt-2">
            <Button
              onClick={handleDisable}
              variant="danger"
              icon={<ShieldOff size={16} />}
              loading={disableMutation.isPending}
            >
              Désactiver le MFA
            </Button>
          </div>
        ) : setupData ? (
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                📱 Scannez ce QR code avec <strong>Google Authenticator</strong> ou <strong>Authy</strong>
              </p>
            </div>

            <div className="flex justify-center">
              <img
                src={`data:image/png;base64,${setupData.qr_code_base64}`}
                alt="QR Code MFA"
                className="w-48 h-48 rounded-lg border-2 border-slate-200 dark:border-slate-600"
              />
            </div>

            <div className="bg-slate-100 dark:bg-slate-700 rounded-lg p-4 text-center">
              <p className="text-xs text-slate-600 dark:text-slate-400 mb-1 font-medium">
                Code manuel (si vous ne pouvez pas scanner) :
              </p>
              <p className="font-mono text-base font-bold text-slate-800 dark:text-white tracking-widest select-all">
                {setupData.secret}
              </p>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                Entrez le code à 6 chiffres pour confirmer
              </label>
              <input
                type="text"
                inputMode="numeric"
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength={6}
                className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-4 py-3 text-center text-2xl tracking-widest font-mono bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                autoComplete="off"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => {
                  setSetupData(null)
                  setCode('')
                }}
                className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Annuler
              </button>
              <Button
                onClick={handleEnable}
                disabled={code.length !== 6}
                loading={enableMutation.isPending}
                className="flex-1"
              >
                Activer le MFA
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex justify-end pt-2">
            <Button
              onClick={handleSetup}
              icon={<Shield size={16} />}
              loading={setupMutation.isPending}
            >
              Configurer le MFA
            </Button>
          </div>
        )}
      </div>
    </Card>
  )
}
