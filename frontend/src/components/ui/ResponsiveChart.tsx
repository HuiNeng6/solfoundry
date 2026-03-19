import { useState } from 'react';

interface ChartData {
  label: string;
  value: number;
  color?: string;
}

interface ResponsiveChartProps {
  data: ChartData[];
  title: string;
  type?: 'bar' | 'line';
}

export function ResponsiveChart({ data, title, type = 'bar' }: ResponsiveChartProps) {
  const maxValue = Math.max(...data.map((d) => d.value));
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
      
      {/* Desktop chart - full visualization */}
      <div className="responsive-table overflow-x-auto">
        <div className="flex items-end gap-2 h-48 min-w-[400px] p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          {data.map((item, index) => (
            <div
              key={item.label}
              className="flex-1 flex flex-col items-center gap-2"
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <div
                className={`w-full rounded-t transition-all duration-200 ${
                  item.color || 'bg-brand-500'
                } ${hoveredIndex === index ? 'opacity-100' : 'opacity-80'}`}
                style={{ height: `${(item.value / maxValue) * 100}%` }}
              />
              <span className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[60px]">
                {item.label}
              </span>
              {hoveredIndex === index && (
                <div className="absolute bottom-full mb-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 px-2 py-1 rounded text-xs">
                  {item.value.toLocaleString()}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Mobile chart - simplified scrollable view */}
      <div className="responsive-cards">
        <div className="overflow-x-auto -mx-4 px-4">
          <div className="flex items-end gap-3 h-32 min-w-[320px] py-2">
            {data.map((item) => (
              <div
                key={item.label}
                className="flex flex-col items-center gap-1 min-w-[48px]"
              >
                <div
                  className={`w-8 rounded-t ${item.color || 'bg-brand-500'}`}
                  style={{ height: `${(item.value / maxValue) * 80}px` }}
                />
                <span className="text-[10px] text-gray-500 dark:text-gray-400">
                  {item.label.slice(0, 3)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Mobile data list */}
        <div className="mt-4 space-y-2">
          {data.map((item) => (
            <div
              key={item.label}
              className="flex items-center justify-between text-sm"
            >
              <span className="text-gray-600 dark:text-gray-400">{item.label}</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {item.value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Simple stats grid that's mobile-friendly
interface StatCard {
  label: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
}

interface ResponsiveStatsGridProps {
  stats: StatCard[];
}

export function ResponsiveStatsGrid({ stats }: ResponsiveStatsGridProps) {
  return (
    <div className="grid gap-3 sm:gap-4 grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="mobile-card"
        >
          <div className="flex items-center gap-2">
            {stat.icon && (
              <div className="p-2 rounded-lg bg-brand-50 dark:bg-brand-900/20 text-brand-500">
                {stat.icon}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 truncate">
                {stat.label}
              </p>
              <p className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white truncate">
                {stat.value}
              </p>
              {stat.change && (
                <p
                  className={`text-xs font-medium ${
                    stat.changeType === 'positive'
                      ? 'text-green-600 dark:text-green-400'
                      : stat.changeType === 'negative'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {stat.change}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}