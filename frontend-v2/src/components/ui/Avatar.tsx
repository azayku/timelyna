// Avatar component — inspired by GXON avatar page
// Supports: initials, image, size variants, status indicator, group stacking

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
type AvatarStatus = 'online' | 'offline' | 'away' | 'busy' | null

const SIZES: Record<AvatarSize, string> = {
  xs: 'w-6 h-6 text-[10px]',
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
  xl: 'w-16 h-16 text-xl',
}

const STATUS_COLORS: Record<NonNullable<AvatarStatus>, string> = {
  online: 'bg-emerald-500',
  offline: 'bg-slate-400',
  away: 'bg-amber-500',
  busy: 'bg-red-500',
}

const STATUS_SIZES: Record<AvatarSize, string> = {
  xs: 'w-1.5 h-1.5',
  sm: 'w-2 h-2',
  md: 'w-2.5 h-2.5',
  lg: 'w-3 h-3',
  xl: 'w-4 h-4',
}

// Generate a consistent color from a name string
function nameToColor(name: string): string {
  const colors = [
    'bg-indigo-500', 'bg-emerald-500', 'bg-amber-500', 'bg-red-500',
    'bg-purple-500', 'bg-blue-500', 'bg-pink-500', 'bg-teal-500',
    'bg-orange-500', 'bg-cyan-500',
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

function getInitials(name: string): string {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

interface AvatarProps {
  name: string
  src?: string
  size?: AvatarSize
  status?: AvatarStatus
  className?: string
  /** Override the auto-derived initials (e.g. "AR" for Achille Romano). */
  initials?: string
}

export default function Avatar({ name, src, size = 'md', status = null, className = '', initials: customInitials }: AvatarProps) {
  const color = nameToColor(name)
  const initials = customInitials ?? getInitials(name)

  return (
    <div className={`relative inline-flex flex-shrink-0 ${className}`}>
      {src ? (
        <img
          src={src}
          alt={name}
          className={`${SIZES[size]} rounded-full object-cover ring-2 ring-white`}
        />
      ) : (
        <div
          className={`${SIZES[size]} ${color} rounded-full flex items-center justify-center text-white font-semibold ring-2 ring-white`}
          title={name}
        >
          {initials}
        </div>
      )}
      {status && (
        <span
          className={`absolute bottom-0 right-0 ${STATUS_SIZES[size]} ${STATUS_COLORS[status]} rounded-full ring-2 ring-white`}
        />
      )}
    </div>
  )
}

// AvatarGroup — stacked avatars with overflow count
interface AvatarGroupProps {
  names: string[]
  max?: number
  size?: AvatarSize
}

export function AvatarGroup({ names, max = 4, size = 'sm' }: AvatarGroupProps) {
  const visible = names.slice(0, max)
  const overflow = names.length - max

  return (
    <div className="flex items-center -space-x-2">
      {visible.map((name, i) => (
        <Avatar key={i} name={name} size={size} />
      ))}
      {overflow > 0 && (
        <div
          className={`${SIZES[size]} bg-slate-200 text-slate-600 rounded-full flex items-center justify-center text-[10px] font-bold ring-2 ring-white`}
        >
          +{overflow}
        </div>
      )}
    </div>
  )
}
