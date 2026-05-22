'use client';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

interface Props {
  data: { week_start: string; message_count: number }[];
}

export function TrendChart({ data }: Props) {
  if (!data || data.length === 0) return null;

  const chartData = data.map((d) => ({
    week: d.week_start.slice(5),
    messages: d.message_count,
  }));

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-medium text-slate-400 mb-4">周互动趋势</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="week"
            stroke="#64748b"
            tick={{ fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Line
            type="monotone"
            dataKey="messages"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#8b5cf6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
