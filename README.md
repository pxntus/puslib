# Puslib

**Puslib** is a Python library for working with the ECSS Packet Utilization Standard (PUS), a protocol widely used in the space industry.

PUS defines an application-level interface between ground and space, covering both segments. It specifies a binary packet format for telecommands and telemetry (based on CCSDS space packets) and a routing mechanism for those packets, as well as a software architecture built around application processes and a set of standard services.

Puslib covers two main use cases:

* **TM/TC packet parsing** — deserialize raw packet streams, inspect packet fields, and extract parameter data for post-processing or analysis.
* **PUS application stack** — implement a PUS-compliant backend that receives telecommands and emits telemetry, for use in EGSE equipment, simulators, or any system that communicates over TM/TC.

The PUS stack is designed from the perspective of the system being monitored and controlled. It receives telecommands and produces telemetry, making it better suited for simulators and EGSE than for mission control systems. It targets ground tooling and test equipment rather than flight software, but don't let the sky be the limit.

## Install

```shell
pip install puslib
```

Python 3.10 or later is required.

## Basic Example

```python
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
