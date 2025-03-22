import argparse

from puslib.streams.file import FileInput  # noqa: E402


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract telemetry packets from archive files.")
    parser.add_argument('input', metavar='path', help='Archive file')
    parser.add_argument('-o', '--offset', metavar='size', type=int, default=0, help="Offset from outer proprietary headers to CCSDS header.")
    parser.add_argument('-v', '--validate-pec', action="store_true", help="Validate packet error control.")
    args = parser.parse_args()

    file_input_stream = FileInput(args.input, args.offset, args.validate_pec)
    for _, packet in file_input_stream:
        print(packet)
