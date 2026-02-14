import { useMemo, useState } from 'react';
import type { HierarchyAsset } from '../services/api';

const TYPE_ICONS: Record<string, string> = {
  enterprise: '\u{1F3E2}',  // office building
  site: '\u{1F4CD}',         // map pin
  battery_bess: '\u{1F50B}', // battery
  wind_turbine: '\u{1F32C}', // wind
  substation: '\u{26A1}',    // zap
  inverter: '\u{1F9AE}',     // circuit
};

function getIcon(type: string) {
  return TYPE_ICONS[type] ?? '\u{1F4E6}'; // package fallback
}

interface TreeNode {
  asset: HierarchyAsset;
  children: TreeNode[];
}

function buildTree(assets: HierarchyAsset[]): TreeNode[] {
  const map = new Map<string, TreeNode>();
  const roots: TreeNode[] = [];

  for (const asset of assets) {
    map.set(asset.asset_id, { asset, children: [] });
  }

  for (const asset of assets) {
    const node = map.get(asset.asset_id)!;
    if (asset.parent_asset_id && map.has(asset.parent_asset_id)) {
      map.get(asset.parent_asset_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots;
}

function matchesSearch(node: TreeNode, term: string): boolean {
  const lower = term.toLowerCase();
  if (
    node.asset.asset_name.toLowerCase().includes(lower) ||
    node.asset.asset_id.toLowerCase().includes(lower) ||
    node.asset.asset_type.toLowerCase().includes(lower)
  ) {
    return true;
  }
  return node.children.some((child) => matchesSearch(child, term));
}

interface TreeNodeRowProps {
  node: TreeNode;
  depth: number;
  expandedIds: Set<string>;
  selectedId: string | null;
  searchTerm: string;
  onToggle: (id: string) => void;
  onSelect: (id: string) => void;
}

function TreeNodeRow({
  node,
  depth,
  expandedIds,
  selectedId,
  searchTerm,
  onToggle,
  onSelect,
}: TreeNodeRowProps) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expandedIds.has(node.asset.asset_id);
  const isSelected = selectedId === node.asset.asset_id;

  if (searchTerm && !matchesSearch(node, searchTerm)) {
    return null;
  }

  return (
    <>
      <div
        className={`flex items-center gap-2 px-2 py-1.5 cursor-pointer text-sm rounded ${
          isSelected
            ? 'bg-gray-800 border-l-2 border-blue-500 text-white'
            : 'text-gray-300 hover:bg-gray-800/50 border-l-2 border-transparent'
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => onSelect(node.asset.asset_id)}
      >
        <span
          className={`w-4 text-center text-xs text-gray-500 ${hasChildren ? 'cursor-pointer' : ''}`}
          onClick={(e) => {
            if (hasChildren) {
              e.stopPropagation();
              onToggle(node.asset.asset_id);
            }
          }}
        >
          {hasChildren ? (isExpanded ? '\u25BE' : '\u25B8') : ''}
        </span>
        <span className="text-base leading-none">{getIcon(node.asset.asset_type)}</span>
        <span className="truncate">{node.asset.asset_name}</span>
        {node.asset.child_count > 0 && (
          <span className="text-xs text-gray-500 ml-auto">{node.asset.child_count}</span>
        )}
      </div>
      {isExpanded &&
        node.children.map((child) => (
          <TreeNodeRow
            key={child.asset.asset_id}
            node={child}
            depth={depth + 1}
            expandedIds={expandedIds}
            selectedId={selectedId}
            searchTerm={searchTerm}
            onToggle={onToggle}
            onSelect={onSelect}
          />
        ))}
    </>
  );
}

interface TreeViewProps {
  assets: HierarchyAsset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function TreeView({ assets, selectedId, onSelect }: TreeViewProps) {
  const tree = useMemo(() => buildTree(assets), [assets]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => {
    // Start with root nodes expanded
    const roots = new Set<string>();
    for (const a of assets) {
      if (!a.parent_asset_id) roots.add(a.asset_id);
    }
    return roots;
  });
  const [search, setSearch] = useState('');

  const onToggle = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-2">
        <input
          type="text"
          placeholder="Search assets..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
      </div>
      <div className="flex-1 overflow-y-auto px-1">
        {tree.map((node) => (
          <TreeNodeRow
            key={node.asset.asset_id}
            node={node}
            depth={0}
            expandedIds={expandedIds}
            selectedId={selectedId}
            searchTerm={search}
            onToggle={onToggle}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
