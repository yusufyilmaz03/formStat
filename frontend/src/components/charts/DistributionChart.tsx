import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { colorAt } from "../../lib/colors";

interface DistItem {
  label: string;
  count: number;
  percent?: number;
}

export function CategoryBar({ data }: { data: DistItem[] }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(160, data.length * 34)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="label" width={130} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: any, _n, p: any) => [`${v} (${p.payload.percent ?? ""}%)`, "Sayı"]} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={colorAt(i)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CategoryPie({ data }: { data: DistItem[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="label" cx="50%" cy="50%" outerRadius={80} label={(e: any) => e.label}>
          {data.map((_, i) => (
            <Cell key={i} fill={colorAt(i)} />
          ))}
        </Pie>
        <Tooltip formatter={(v: any, _n, p: any) => [`${v} (${p.payload.percent ?? ""}%)`, p.payload.label]} />
      </PieChart>
    </ResponsiveContainer>
  );
}

interface HistBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export function Histogram({ bins }: { bins: HistBin[] }) {
  const data = bins.map((b) => ({
    label: `${Math.round(b.bin_start * 100) / 100}–${Math.round(b.bin_end * 100) / 100}`,
    count: b.count,
  }));
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
        <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={50} />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" fill={colorAt(0)} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
