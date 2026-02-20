import sounddevice as sd

print("=== AUDIO DEVICES ===")
print("Default device (input, output):", sd.default.device)
print()

for i, device in enumerate(sd.query_devices()):
    in_ch = device.get("max_input_channels", 0)
    out_ch = device.get("max_output_channels", 0)
    marker = "<-- DEFAULT INPUT" if isinstance(sd.default.device, (list, tuple)) and len(sd.default.device) > 0 and sd.default.device[0] == i else ""
    print(f"{i}: in={in_ch} out={out_ch} | {device.get('name','')} {marker}")
