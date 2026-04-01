import { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import {
  TrendingUp, DollarSign, ShoppingCart,
  RefreshCw, Loader2, AlertCircle, Database
} from 'lucide-react';
import {
  api, RevenueResponse, TopProductsResponse, CategoryPerformanceResponse,
} from '../api';

const COLORS = [
  '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
  '#f43f5e', '#f97316', '#eab308', '#22c55e', '#14b8a6',
];

export default function AnalyticsPage() {
  const [revenue, setRevenue] = useState<RevenueResponse | null>(null);
  const [topProducts, setTopProducts] = useState<TopProductsResponse | null>(null);
  const [categories, setCategories] = useState<CategoryPerformanceResponse | null>(null);
  const [period, setPeriod] = useState('daily');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (p: string) => {
    setLoading(true);
    setError(null);
    try {
      const [rev, top, cat] = await Promise.all([
        api.getRevenue(p),
        api.getTopProducts(10),
        api.getCategoryPerformance(),
      ]);
      setRevenue(rev);
      setTopProducts(top);
      setCategories(cat);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load analytics';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(period);
  }, [period]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.syncToSnowflake();
      await loadData(period);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Sync failed';
      setError(message);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
          <AlertCircle className="w-10 h-10 text-amber-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-amber-800 mb-2">Analytics Unavailable</h3>
          <p className="text-amber-700 text-sm mb-4">{error}</p>
          <div className="space-y-2">
            <p className="text-amber-600 text-xs">
              Make sure Snowflake credentials are configured in your .env file and data has been synced.
            </p>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="inline-flex items-center gap-2 bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-700 disabled:opacity-50"
            >
              {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
              Sync Data to Snowflake
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sales Analytics</h1>
          <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
            <Database className="w-3.5 h-3.5" />
            Powered by Snowflake Data Warehouse
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Sync to Snowflake
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {revenue && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <KPICard
            title="Total Revenue"
            value={`$${revenue.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
            icon={DollarSign}
            color="text-emerald-600"
            bg="bg-emerald-50"
          />
          <KPICard
            title="Total Orders"
            value={revenue.total_orders.toLocaleString()}
            icon={ShoppingCart}
            color="text-blue-600"
            bg="bg-blue-50"
          />
          <KPICard
            title="Avg Order Value"
            value={`$${revenue.total_orders > 0 ? (revenue.total_revenue / revenue.total_orders).toFixed(2) : '0.00'}`}
            icon={TrendingUp}
            color="text-purple-600"
            bg="bg-purple-50"
          />
        </div>
      )}

      {/* Revenue Chart */}
      {revenue && revenue.data.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Revenue Over Time ({period})
          </h2>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={revenue.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="period"
                tick={{ fontSize: 12 }}
                tickFormatter={(v: string) => {
                  const d = new Date(v);
                  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }}
              />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `$${v}`} />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Revenue']}
                labelFormatter={(label: string) => new Date(label).toLocaleDateString()}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#6366f1"
                strokeWidth={2.5}
                dot={{ r: 4, fill: '#6366f1' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        {topProducts && topProducts.products.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Products by Revenue</h2>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={topProducts.products.slice(0, 8)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v: number) => `$${v}`} />
                <YAxis
                  type="category"
                  dataKey="product_name"
                  tick={{ fontSize: 11 }}
                  width={140}
                />
                <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`, 'Revenue']} />
                <Bar dataKey="total_revenue" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Category Performance */}
        {categories && categories.categories.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Category</h2>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={categories.categories}
                  dataKey="total_revenue"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  label={({ category, percent }: { category: string; percent: number }) =>
                    `${category} (${(percent * 100).toFixed(0)}%)`
                  }
                  labelLine={true}
                >
                  {categories.categories.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Category Table */}
      {categories && categories.categories.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mt-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Category</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Revenue</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Units Sold</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Avg Order Value</th>
                </tr>
              </thead>
              <tbody>
                {categories.categories.map((cat, i) => (
                  <tr key={cat.category} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 px-4 flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COLORS[i % COLORS.length] }}
                      />
                      {cat.category}
                    </td>
                    <td className="text-right py-3 px-4 font-medium">
                      ${cat.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="text-right py-3 px-4">{cat.total_sold.toLocaleString()}</td>
                    <td className="text-right py-3 px-4">${cat.avg_order_value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function KPICard({
  title, value, icon: Icon, color, bg,
}: {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-lg ${bg}`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
