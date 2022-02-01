# Puslib

**Puslib** is a Python implementation of the telemetry and telecommand packet utilization standard (PUS). It is a standard widely used in the space industry for the purposes of remote monitoring and control of spacecraft subsystems and payloads.

This package is mainly intended for ground segment tools, e.g.:

* data extraction and post-processing of telemetry.
* simulators.
* EGSE SW, and thus enabling the use of mission control systems for controling and monitoring of EGSE equipment.
* enable Python based commanding for mission control systems and other PUS based systems.
* mission-specific tools.
* student projects.

## Install

```Shell
pip install puslib
```

Python 3.7 or later is required.

## Basic Example

```Python
from datetime import datetime
from functools import partial

from puslib import packet
from puslib import time

MyTmPacket = partial(packet.PusTmPacket.deserialize,
                     has_type_counter_field=False,
                     has_destination_field=False)
MyCucTime = partial(time.CucTime, 4, 2, has_preamble=False)

with open('telemetry.dump', 'rb') as f:
    content = f.read()
    data = memoryview(content)

    offset = 0
    cuc_time = MyCucTime()
    while offset < len(data):
        packet_length, packet = MyTmPacket(data[offset:],
                                           cuc_time,
                                           validate_fields=False,
                                           validate_pec=False)
        offset += packet_length
        if packet.service == 3 and packet.subservice == 25:
            print(packet)
```

## Supported Features

* CCSDS packet handling (telecommands and telemetry packets)
* CCSDS Unsegmented Time Code (CUC) support
* Policy handling of mission specific or implementation specific configurations
* Simple abstraction of application processes
* Streams for telemetry and telecommand I/O access
* PUS Services:
  * PUS 1: Request Verification
  * PUS 3: Housekeeping (*partial support*)
  * PUS 5: Event Reporting
  * PUS 8: Function Management
  * PUS 17: Test (*partial support*)
  * PUS 20: On-board Parameter Management (*partial support*)

## Links

* [ECSS-E-ST-70-41C – Telemetry and telecommand packet utilization (15 April 2016)](https://ecss.nl/standard/ecss-e-st-70-41c-space-engineering-telemetry-and-telecommand-packet-utilization-15-april-2016/)
* [CCSDS 301.0-B-4 – Time Code Formats](https://public.ccsds.org/Pubs/301x0b4e1.pdf)
