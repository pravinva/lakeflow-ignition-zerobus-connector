import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { HierarchyAsset, AssetTemplate, AssetAttributeValue } from '../services/api';

interface AssetDetailPanelProps {
  asset: HierarchyAsset;
  templates: AssetTemplate[];
  onEdit: () => void;
  onAddChild: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}

export default function AssetDetailPanel({
  asset,
  templates,
  onEdit,
  onAddChild,
  onDelete,
  onRefresh,
}: AssetDetailPanelProps) {
  const [attributes, setAttributes] = useState<AssetAttributeValue[]>([]);
  const [editingAttrs, setEditingAttrs] = useState(false);
  const [attrValues, setAttrValues] = useState<Record<string, string>>({});
  const [applyingTemplate, setApplyingTemplate] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');

  useEffect(() => {
    loadAttributes();
  }, [asset.asset_id]);

  async function loadAttributes() {
    try {
      const res = await api.assetFramework.getAssetAttributes(asset.asset_id);
      setAttributes(res.data);
      const vals: Record<string, string> = {};
      for (const a of res.data) {
        vals[a.attribute_id] = a.value ?? '';
      }
      setAttrValues(vals);
    } catch {
      setAttributes([]);
    }
  }

  async function handleSaveAttributes() {
    const values = Object.entries(attrValues).map(([attribute_id, value]) => ({
      attribute_id,
      value: value || null,
    }));
    await api.assetFramework.updateAssetAttributes(asset.asset_id, values);
    setEditingAttrs(false);
    loadAttributes();
  }

  async function handleApplyTemplate() {
    if (!selectedTemplateId) return;
    await api.assetFramework.applyTemplate(asset.asset_id, selectedTemplateId);
    setApplyingTemplate(false);
    setSelectedTemplateId('');
    onRefresh();
    loadAttributes();
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold">{asset.asset_name}</h2>
          <p className="text-sm text-gray-400 mt-1">
            <span className="font-mono text-xs bg-gray-800 px-1.5 py-0.5 rounded">{asset.asset_id}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={onEdit} className="px-3 py-1.5 text-sm rounded bg-gray-800 text-gray-300 hover:bg-gray-700">
            Edit
          </button>
          <button onClick={onAddChild} className="px-3 py-1.5 text-sm rounded bg-gray-800 text-gray-300 hover:bg-gray-700">
            Add child
          </button>
          <button onClick={onDelete} className="px-3 py-1.5 text-sm rounded bg-red-900/50 text-red-400 hover:bg-red-900/80">
            Delete
          </button>
        </div>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <span className="text-xs text-gray-500">Type</span>
          <p className="text-sm">{asset.asset_type.replace(/_/g, ' ')}</p>
        </div>
        <div>
          <span className="text-xs text-gray-500">Site</span>
          <p className="text-sm">{asset.site_name ?? '-'}</p>
        </div>
        <div>
          <span className="text-xs text-gray-500">Template</span>
          <p className="text-sm">{asset.template_name ?? 'None'}</p>
        </div>
        <div>
          <span className="text-xs text-gray-500">Parent</span>
          <p className="text-sm font-mono text-xs">{asset.parent_asset_id ?? 'Root'}</p>
        </div>
      </div>

      {asset.description && (
        <div>
          <span className="text-xs text-gray-500">Description</span>
          <p className="text-sm text-gray-300">{asset.description}</p>
        </div>
      )}

      {/* Apply template */}
      {!applyingTemplate ? (
        <button
          onClick={() => setApplyingTemplate(true)}
          className="text-sm text-blue-400 hover:text-blue-300"
        >
          Apply template...
        </button>
      ) : (
        <div className="flex gap-2 items-center">
          <select
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
            className="flex-1 px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200"
          >
            <option value="">Select template</option>
            {templates.map((t) => (
              <option key={t.template_id} value={t.template_id}>
                {t.template_name}
              </option>
            ))}
          </select>
          <button
            onClick={handleApplyTemplate}
            disabled={!selectedTemplateId}
            className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50"
          >
            Apply
          </button>
          <button
            onClick={() => { setApplyingTemplate(false); setSelectedTemplateId(''); }}
            className="px-3 py-1.5 text-sm rounded bg-gray-800 text-gray-300 hover:bg-gray-700"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Attribute values */}
      {attributes.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-gray-300">Attributes</h3>
            {!editingAttrs ? (
              <button
                onClick={() => setEditingAttrs(true)}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                Edit values
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={handleSaveAttributes}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  Save
                </button>
                <button
                  onClick={() => { setEditingAttrs(false); loadAttributes(); }}
                  className="text-xs text-gray-400 hover:text-gray-300"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 border-b border-gray-800">
                <th className="text-left py-1 font-normal">Attribute</th>
                <th className="text-left py-1 font-normal">Value</th>
                <th className="text-left py-1 font-normal">Unit</th>
                <th className="text-left py-1 font-normal">Type</th>
              </tr>
            </thead>
            <tbody>
              {attributes.map((attr) => (
                <tr key={attr.attribute_id} className="border-b border-gray-800/50">
                  <td className="py-1.5 text-gray-300">
                    {attr.attribute_name}
                    {attr.is_required && <span className="text-red-400 ml-1">*</span>}
                  </td>
                  <td className="py-1.5">
                    {editingAttrs ? (
                      <input
                        type="text"
                        value={attrValues[attr.attribute_id] ?? ''}
                        onChange={(e) =>
                          setAttrValues((prev) => ({ ...prev, [attr.attribute_id]: e.target.value }))
                        }
                        className="w-full px-2 py-0.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200"
                      />
                    ) : (
                      <span className="font-mono text-xs">{attr.value ?? '-'}</span>
                    )}
                  </td>
                  <td className="py-1.5 text-gray-500 text-xs">{attr.unit ?? ''}</td>
                  <td className="py-1.5 text-gray-500 text-xs">{attr.data_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
