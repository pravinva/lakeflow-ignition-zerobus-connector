# AGL Energy Logo Kit

Logos for AGL Energy customer engagements.

## Included Logos

| File | Description | Use Case |
|------|-------------|----------|
| `AGL_Energy_logo.png` | AGL Energy logo (cyan/teal rays) | Customer branding |
| `kaluza_logo_black.png` | Kaluza logo (three black hexagons) | Kaluza platform |

## When to Use This Kit

Use this kit for:
- ✅ AGL Energy customer engagements
- ✅ Kaluza platform architectures
- ✅ Energy sector diagrams

## Logo Descriptions

When the AI generates diagrams, it uses these descriptions:

| Logo Name | Description in Prompt |
|-----------|----------------------|
| `agl_energy_logo` | "cyan/teal AGL Energy logo with rays" |
| `kaluza_logo_black` | "three black hexagons in triangular pattern" |

## Example Diagram Spec

```yaml
name: "agl-data-platform"
description: "AGL Energy data platform with Kaluza"

components:
  - id: "kaluza"
    label: "Kaluza Platform"
    logo_name: "kaluza_logo_black"

  - id: "databricks"
    label: "Databricks"
    logo_name: "databricks-full"

  - id: "agl"
    label: "AGL Energy Systems"
    logo_name: "agl_energy_logo"

connections:
  - from_id: "kaluza"
    to_id: "databricks"
    label: "Data Pipeline"
```

## Configuration

```yaml
# configs/agl.yaml
logo_kit:
  logo_dir: "./logos/agl"
```

## Usage

```bash
nano-banana generate \
    --config configs/agl.yaml \
    --diagram-spec prompts/diagram_specs/agl-architecture.yaml \
    --template baseline
```

## Notes

- Include core Databricks logos from `logos/default/` if needed
- Use AGL brand colors in diagram constraints
- Kaluza logo should be used for platform-specific components
