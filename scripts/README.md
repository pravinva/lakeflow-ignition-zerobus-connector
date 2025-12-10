# Automation Scripts

Generic tools for creating and deploying Event Streams without manual configuration.

## Quick Start: Create Any Event Stream

### Method 1: From Command Line

```bash
./create_eventstream.py \
  --name "zerobus_gateway" \
  --tags "[Sample_Tags]Ramp/Ramp0" "[Sample_Tags]Ramp/Ramp1" "[Sample_Tags]Ramp/Ramp2" \
  --gateway-url "http://localhost:8088" \
  --output "../configs/zerobus_gateway.json" \
  --script-output "../configs/zerobus_gateway_handler.py"
```

### Method 2: From Tag File

```bash
# 1. Create tag file
cat > tags.txt <<EOF
[Sample_Tags]Ramp/Ramp0
[Sample_Tags]Ramp/Ramp1
[Sample_Tags]Ramp/Ramp2
[Sample_Tags]Ramp/Ramp3
EOF

# 2. Generate configuration
./create_eventstream.py \
  --name "zerobus_gateway" \
  --tag-file tags.txt \
  --script-output handler.py
```

### Method 3: Interactive

```bash
./create_eventstream.py --name my_stream --tags # (then add tags interactively)
```

## Usage Examples

### Create Event Stream for Production Tags

```bash
./create_eventstream.py \
  --name "production_tags" \
  --tags \
    "[default]Equipment/Pump01/Temperature" \
    "[default]Equipment/Pump01/Pressure" \
    "[default]Equipment/Pump02/Temperature" \
  --debounce 50 \
  --max-wait 500 \
  --max-queue-size 50000
```

### Create Event Stream with Wildcard Pattern

```bash
# Create tags file with pattern
cat > production_tags.txt <<EOF
[default]Equipment/Pump01/Temperature
[default]Equipment/Pump01/Pressure
[default]Equipment/Pump02/Temperature
[default]Equipment/Pump02/Pressure
[default]Equipment/Tank*/Level
EOF

./create_eventstream.py \
  --name "production_monitoring" \
  --tag-file production_tags.txt
```

### Create Multiple Event Streams

```bash
# Stream 1: High-frequency tags (fast-changing values)
./create_eventstream.py \
  --name "fast_tags" \
  --tag-file configs/fast_tags.txt \
  --debounce 50 \
  --max-wait 500

# Stream 2: Low-frequency tags (slow-changing values)
./create_eventstream.py \
  --name "slow_tags" \
  --tag-file configs/slow_tags.txt \
  --debounce 500 \
  --max-wait 5000

# Stream 3: Critical alarms
./create_eventstream.py \
  --name "alarms" \
  --tag-file configs/alarm_tags.txt \
  --debounce 10 \
  --max-wait 100
```

## Command Reference

### Required Arguments

- `--name` - Event Stream name (alphanumeric, underscores, hyphens)
- `--tags` OR `--tag-file` - Tag paths to monitor

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--gateway-url` | `http://localhost:8088` | Gateway URL for handler |
| `--debounce` | `100` | Buffer debounce (ms) |
| `--max-wait` | `1000` | Buffer max wait (ms) |
| `--max-queue-size` | `10000` | Buffer max queue size |
| `--batch-size` | `50` | Batch size hint |
| `--output` | `configs/<name>.json` | Output file path |
| `--script-output` | (none) | Separate script file |

## Installation in Designer

After generating configuration:

1. **Open Designer**
2. **Go to:** Project Browser → Event Streams
3. **Create new:** Right-click → New Event Stream
4. **Name:** Use the `--name` you specified
5. **Configure Source:**
   - Type: Tag Event
   - Tag Paths: Copy from generated config or tags file
6. **Configure Encoder:**
   - Type: String
   - Encoding: UTF-8
7. **Configure Buffer:**
   - Copy values from generated config
8. **Add Handler → Script:**
   - Paste from: `<name>_handler.py` (or from config JSON)
9. **Save and Enable**

## Generated Files

The tool creates:

1. **`<name>.json`** - Complete Event Stream configuration
2. **`<name>_handler.py`** - Handler script (if `--script-output` specified)

### Configuration File Structure

```json
{
  "name": "stream_name",
  "source": {
    "type": "Tag Event",
    "tagPaths": ["[Provider]Folder/Tag", ...]
  },
  "encoder": { "type": "String" },
  "buffer": { "debounceMs": 100, ... },
  "handler": {
    "type": "Script",
    "script": "def onEventsReceived(events, state): ..."
  }
}
```

## Advanced Usage

### Custom Buffer for High-Frequency Tags

```bash
./create_eventstream.py \
  --name "high_frequency" \
  --tag-file fast_tags.txt \
  --debounce 10 \
  --max-wait 100 \
  --max-queue-size 100000
```

### Custom Buffer for Low-Frequency Tags

```bash
./create_eventstream.py \
  --name "low_frequency" \
  --tag-file slow_tags.txt \
  --debounce 1000 \
  --max-wait 10000 \
  --max-queue-size 1000
```

### Multi-Environment Deployment

```bash
# Development
./create_eventstream.py \
  --name "dev_stream" \
  --tag-file tags.txt \
  --gateway-url "http://dev-gateway:8088" \
  --output configs/dev_stream.json

# Production
./create_eventstream.py \
  --name "prod_stream" \
  --tag-file tags.txt \
  --gateway-url "http://prod-gateway:8088" \
  --output configs/prod_stream.json
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Generate Event Stream Config
  run: |
    ./scripts/create_eventstream.py \
      --name "production" \
      --tag-file configs/production_tags.txt \
      --gateway-url "${{ secrets.GATEWAY_URL }}" \
      --output eventstream.json

- name: Upload Artifact
  uses: actions/upload-artifact@v3
  with:
    name: eventstream-config
    path: eventstream.json
```

## Troubleshooting

### Script Not Found

```bash
# Make sure you're in the scripts directory
cd /path/to/lakeflow-ignition-zerobus-connector/scripts
```

### Python Not Found

```bash
# Install Python 3
brew install python3  # macOS
sudo apt install python3  # Linux
```

### Invalid Tag Format

Tags must follow Ignition format:
```
Correct:   [Provider]Folder/TagName
Wrong:     Provider/Folder/TagName
Wrong:     [Provider]/Folder/TagName
Wrong:     Provider.Folder.TagName
```

## Files

- **`create_eventstream.py`** - Generic Event Stream generator
- **`gateway_tag_forwarder.py`** - Gateway script alternative
- **`install_gateway_script.sh`** - Gateway script installer
- **`deploy_eventstream.sh`** - Full deployment automation
- **`README.md`** - This file

## Next Steps

1. Generate your Event Stream configuration
2. Copy handler script from generated file
3. Configure in Designer (one time)
4. Version control the generated configs
5. Replicate to other environments

Or skip Event Streams entirely and use **Gateway Script** approach (see `gateway_tag_forwarder.py`).

