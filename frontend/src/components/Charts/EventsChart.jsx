import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

function EventsChart({ events }) {
  // Group events by time buckets (5-minute intervals)
  const groupedData = events.reduce((acc, event) => {
    const time = new Date(event.timestamp || Date.now());
    const bucket = new Date(Math.floor(time.getTime() / 300000) * 300000);
    const key = bucket.toISOString();

    if (!acc[key]) {
      acc[key] = { time: bucket, count: 0, critical: 0, high: 0 };
    }

    acc[key].count++;
    if (event.severity === 'critical') acc[key].critical++;
    if (event.severity === 'high') acc[key].high++;

    return acc;
  }, {});

  const chartData = Object.values(groupedData)
    .sort((a, b) => a.time - b.time)
    .slice(-12); // Last 12 buckets (1 hour)

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: '#1a1a1a',
          border: '1px solid #333',
          padding: '12px',
          borderRadius: '8px'
        }}>
          <p style={{ color: '#e0e0e0', marginBottom: '8px' }}>
            {format(payload[0].payload.time, 'HH:mm')}
          </p>
          <p style={{ color: '#4ade80', margin: 0 }}>
            Total: {payload[0].value}
          </p>
          <p style={{ color: '#ef4444', margin: 0 }}>
            Critical: {payload[0].payload.critical}
          </p>
          <p style={{ color: '#f59e0b', margin: 0 }}>
            High: {payload[0].payload.high}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
        <XAxis
          dataKey="time"
          tickFormatter={(time) => format(new Date(time), 'HH:mm')}
          stroke="#888"
        />
        <YAxis stroke="#888" />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#4ade80"
          strokeWidth={2}
          dot={{ fill: '#4ade80', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default EventsChart;
