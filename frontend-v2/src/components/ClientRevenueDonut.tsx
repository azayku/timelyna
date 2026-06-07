import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts'
import { useChartTheme } from '../lib/useChartTheme'

export interface ClientRevenueDataPoint {
  client_name: string
  revenue: number
}

interface ClientRevenueDonutProps {
  data: ClientRevenueDataPoint[]
}

const fmtEur = (v: number) =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(v)

export default function ClientRevenueDonut({ data }: ClientRevenueDonutProps) {
  const { colors, tooltipStyle, textColor } = useChartTheme()

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={data}
          dataKey="revenue"
          nameKey="client_name"
          cx="40%"
          cy="50%"
          innerRadius={52}
          outerRadius={84}
          paddingAngle={3}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={colors[i % colors.length]} />
          ))}
        </Pie>
        <Legend
          layout="vertical"
          align="right"
          verticalAlign="middle"
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11, lineHeight: '22px' }}
          formatter={(value: string) => (
            <span style={{ color: textColor }}>{value}</span>
          )}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value) => [fmtEur(value as number), '']}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
