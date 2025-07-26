# JunctionRelay Home Assistant Integration

This is the HACS-compatible custom integration for JunctionRelay.

## Installation

1. Copy the `custom_components/junctionrelay` folder to your Home Assistant config directory.
2. Add to your `configuration.yaml`:

```yaml
junctionrelay:
  host: "http://localhost:7180"
```

3. Restart Home Assistant.

## HACS Setup

To add this integration to HACS:
1. Go to HACS > Integrations > Custom Repositories
2. Paste the GitHub URL: `https://github.com/catapultcase/JunctionRelay_HomeAssistant`
3. Choose "Integration" as the category.
4. Click Install.
