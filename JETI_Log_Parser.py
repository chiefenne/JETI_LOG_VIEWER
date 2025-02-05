import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any

class JetiTelemetryParser:
    def __init__(self, log_data: str):
        self.raw_data = log_data
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.device_id_to_name: Dict[int, str] = {}

    def parse(self):
        """Main parsing method that coordinates the parsing process."""
        lines = self.raw_data.splitlines()
        self._parse_devices(lines)
        self._parse_entries(lines)

    def _parse_devices(self, lines: List[str]):
        """Parse device and channel definitions from header lines."""
        for line in lines:
            if line.startswith("#"):
                continue  # Skip comment lines

            parts = line.split(";")
            if len(parts) < 4 or parts[0] != "000000000":
                continue  # Skip lines that are not device metadata

            device_id = int(parts[1])
            channel_id = int(parts[2])
            channel_name = parts[3].strip()
            unit = parts[4].strip() if len(parts) > 4 else None

            if channel_id == 0:
                # This is a device name line
                device_name = channel_name
                self.device_id_to_name[device_id] = device_name
                if device_name not in self.devices:
                    self.devices[device_name] = {"channels": {}, "data": {}}
            else:
                # This is a channel for the current device
                device_name = self.device_id_to_name.get(device_id)
                if device_name:
                    self.devices[device_name]["channels"][channel_id] = {
                        "name": channel_name,
                        "unit": unit,
                    }
                    # Prepare a placeholder for the numpy array to store channel data
                    self.devices[device_name]["data"][channel_id] = []

    def _parse_entries(self, lines: List[str]):
        """Parse the telemetry data entries."""
        for line in lines:
            if line.startswith("#") or line.startswith("000000000"):
                continue  # Skip header and metadata lines

            parts = line.split(";")
            if len(parts) < 6:
                continue  # Skip lines that don’t have enough fields

            timestamp = int(parts[0])
            device_id = int(parts[1])
            channel_data = parts[2:]

            for i in range(0, len(channel_data), 4):
                channel_id = int(channel_data[i])
                # channel_data[i+1] is the Jeti data type (ignored here)
                decimal_places = int(channel_data[i+2])
                raw_value = int(channel_data[i+3])
                final_value = raw_value / (10 ** decimal_places)

                device_name = self.device_id_to_name.get(device_id)
                if device_name and channel_id in self.devices[device_name]["data"]:
                    # Add this data point to the list for this channel
                    self.devices[device_name]["data"][channel_id].append((timestamp, final_value))

        # Convert lists to numpy arrays
        for device_name in self.devices:
            for channel_id, data_points in self.devices[device_name]["data"].items():
                self.devices[device_name]["data"][channel_id] = np.array(data_points)

    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        """Return the organized device data structure."""
        return self.devices



# Example usage:
if __name__ == "__main__":

  # read the log data from a file
    filename = '/Users/andreas/Downloads/JETI_test.log'
    with open(filename, "r", encoding='utf-8', errors='replace') as file:
        telemetry_log_data = file.read()

    # Create a parser instance and parse the log data
    parser = JetiTelemetryParser(telemetry_log_data)
    parser.parse()

    devices = parser.get_devices()

    # print devices and channels
    for device_name, device_data in devices.items():
        print(f"Device: {device_name}")
        for channel_id, channel_data in device_data["channels"].items():
            print(f"  Channel {channel_id}: {channel_data['name']} ({channel_data['unit']})")

    # Specify the device and channel you want to plot
    target_device = "MHB"
    target_channel_id = 15

    # Retrieve the channel's data
    if target_device in devices and target_channel_id in devices[target_device]["data"]:
        data = devices[target_device]["data"][target_channel_id]

        # Ensure there is data to plot
        if data.size > 0:
            timestamps = data[:, 0]
            values = data[:, 1]

            # Plot the data
            plt.figure(figsize=(10, 6))
            plt.plot(timestamps, values, label=f"{devices[target_device]['channels'][target_channel_id]['name']} ({devices[target_device]['channels'][target_channel_id]['unit']})")
            plt.title(f"Time Series Data for {target_device}, Channel {target_channel_id}")
            plt.xlabel("Timestamp (ms)")
            plt.ylabel("Value")
            plt.legend()
            plt.grid()
            plt.show()
        else:
            print(f"No data found for device '{target_device}', channel {target_channel_id}.")
    else:
        print(f"Device '{target_device}' or channel {target_channel_id} not found.")
