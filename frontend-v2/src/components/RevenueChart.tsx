import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import { useChartTheme } from '../lib/useChartTheme'

export interface RevenueDataPoint {
  month: string
  revenue: number
  hours: number
}

interface RevenueChartProps {
  data: RevenueDataPoint[]
}

const fmtEur = (v: number) =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(v)

export default function RevenueChart({ data }: RevenueChartProps) {
  const { t } = useTranslation()
  const { textColor, gridColor, tooltipStyle, colors } = useChartTheme()

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: textColor }}
          axisLine={false}
          tickLine={false}
        />
        {/* Left axis — revenue */}
        <YAxis
          yAxisId="revenue"
          tick={{ fontSize: 11, fill: textColor }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
        />
        {/* Right axis — hours */}
        <YAxis
          yAxisId="hours"
          orientation="right"
          tick={{ fontSize: 11, fill: textColor }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}h`}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value, name) => {
            const v = value as number
            const n = name as string
            return n === t('finance.billedHours')
              ? [`${v}h`, n]
              : [fmtEur(v), n]
          }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
        />
        <Bar
          yAxisId="revenue"
          dataKey="revenue"
          fill={colors[0]}
          radius={[4, 4, 0, 0]}
          name={t('finance.revenueThisMonth')}
          maxBarSize={40}
        />
        <Line
          yAxisId="hours"
          type="monotone"
          dataKey="hours"
          stroke={colors[1]}
          strokeWidth={2}
          dot={{ r: 3, fill: colors[1] }}
          activeDot={{ r: 5 }}
          name={t('finance.billedHours')}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
