import { api } from '../services/api';

const SCENARIOS = [
  { id: 'wind', label: 'Wind Farm (Hexham)', description: '50 turbines' },
  { id: 'battery', label: 'Battery Site (Liddell)', description: '20 battery units' },
  { id: 'mixed', label: 'Mixed Fleet', description: '30 turbines + 15 batteries' },
] as const;

interface ScenarioSwitcherProps {
  activeScenario: string;
  onScenarioChange: (scenario: string) => void;
}

export default function ScenarioSwitcher({ activeScenario, onScenarioChange }: ScenarioSwitcherProps) {
  const handleClick = async (scenarioId: string) => {
    if (scenarioId === activeScenario) return;
    await api.setScenario(scenarioId);
    onScenarioChange(scenarioId);
  };

  return (
    <div className="flex gap-2">
      {SCENARIOS.map((s) => (
        <button
          key={s.id}
          data-active={s.id === activeScenario}
          onClick={() => handleClick(s.id)}
          className={`px-3 py-1.5 rounded text-sm transition-colors ${
            s.id === activeScenario
              ? 'bg-databricks-primary text-white'
              : 'bg-gray-800 text-gray-400 hover:text-gray-100 hover:bg-gray-700'
          }`}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
