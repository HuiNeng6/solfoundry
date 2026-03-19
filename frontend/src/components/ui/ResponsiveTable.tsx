import { useState } from 'react';

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => React.ReactNode;
  mobileHidden?: boolean;
}

interface ResponsiveTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyField: keyof T;
  cardTitle?: (item: T) => React.ReactNode;
  cardDescription?: (item: T) => React.ReactNode;
}

export function ResponsiveTable<T extends Record<string, unknown>>({
  data,
  columns,
  keyField,
  cardTitle,
  cardDescription,
}: ResponsiveTableProps<T>) {
  return (
    <>
      {/* Desktop table view */}
      <div className="responsive-table overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {data.map((item) => (
              <tr key={String(item[keyField])} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                {columns.map((col) => (
                  <td
                    key={String(col.key)}
                    className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
                  >
                    {col.render
                      ? col.render(item)
                      : String(item[col.key as keyof T] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card view */}
      <div className="responsive-cards space-y-3">
        {data.map((item) => (
          <div
            key={String(item[keyField])}
            className="mobile-card"
          >
            {cardTitle && (
              <div className="font-medium text-gray-900 dark:text-white">
                {cardTitle(item)}
              </div>
            )}
            {cardDescription && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {cardDescription(item)}
              </p>
            )}
            <div className="grid grid-cols-2 gap-2 text-sm">
              {columns
                .filter((col) => !col.mobileHidden)
                .map((col) => (
                  <div key={String(col.key)}>
                    <dt className="text-gray-500 dark:text-gray-400 text-xs">
                      {col.header}
                    </dt>
                    <dd className="text-gray-900 dark:text-gray-100 font-medium">
                      {col.render
                        ? col.render(item)
                        : String(item[col.key as keyof T] ?? '')}
                    </dd>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

// Example usage component
interface Bounty {
  id: string;
  title: string;
  tier: number;
  reward: string;
  status: 'open' | 'in-progress' | 'completed';
  deadline: string;
}

export function BountyTableExample() {
  const bounties: Bounty[] = [
    { id: '1', title: 'Mobile Responsive Audit', tier: 1, reward: '200M $FNDRY', status: 'open', deadline: '2026-03-22' },
    { id: '2', title: 'API Documentation', tier: 2, reward: '500K $FNDRY', status: 'in-progress', deadline: '2026-03-25' },
    { id: '3', title: 'Smart Contract Audit', tier: 3, reward: '5M $FNDRY', status: 'open', deadline: '2026-04-01' },
  ];

  const columns: Column<Bounty>[] = [
    { key: 'title', header: 'Title' },
    { key: 'tier', header: 'Tier', render: (b) => <span className="px-2 py-1 rounded-full text-xs bg-brand-100 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300">T{b.tier}</span> },
    { key: 'reward', header: 'Reward' },
    { key: 'status', header: 'Status', render: (b) => (
      <span className={`px-2 py-1 rounded-full text-xs ${
        b.status === 'open' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
        b.status === 'in-progress' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' :
        'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
      }`}>
        {b.status}
      </span>
    )},
    { key: 'deadline', header: 'Deadline', mobileHidden: true },
  ];

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Active Bounties</h2>
      <ResponsiveTable
        data={bounties}
        columns={columns}
        keyField="id"
        cardTitle={(b) => b.title}
        cardDescription={(b) => `${b.reward} • Tier ${b.tier}`}
      />
    </div>
  );
}