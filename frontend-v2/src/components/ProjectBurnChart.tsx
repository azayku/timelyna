import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  ResponsiveContainer,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import { useChartTheme } from '../lib/useChartTheme'

export interface BurnRateDataPoint {
  project_name: string
  budget_hours: number
  billed_hours: number
}

interface ProjectBurnChartProps {
  data: BurnRateDataPoint[]
}

export default function ProjectBurnChart({ data }: ProjectBurnChartProps) {
  const { t } = useTranslation()
  const { textColor, gridColor, tooltipStyle, colors } = useChartTheme()

  // Truncate long project names for the axis
  const truncate = (s: string, max = 14) =>
    s.length > max ? s.slice(0, max) + '…' : s

  const chartData = data.map((d) => ({
    ...d,
    label: truncate(d.project_name),
    overBudget: d.billed_hours > d.budget_hours,
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart
        data={chartData}
        margin={{ top: 4, right: 8, left: -16, bottom: 0 }}
        barCategoryGap="30%"
        barGap={4}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 10, fill: textColor }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: textColor }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}h`}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value, name) => [`${value as number}h`, name as string]}
          labelFormatter={(label) => {
            const s = String(label)
            const item = data.find((d) => d.project_name.startsWith(s.replace('…', '')))
            return item?.project_name ?? s
          }}
        />
        <Legend
          iconType="square"
          iconSize={10}
          wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
        />
        <Bar dataKey="budget_hours" name="Budget (h)" fill="#c7d2fe" radius={[4, 4, 0, 0]} maxBarSize={32} />
        <Bar dataKey="billed_hours" name={t('finance.billedHours')} radius={[4, 4, 0, 0]} maxBarSize={32}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.overBudget ? colors[3] : colors[0]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
