import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input floorplan image")
    parser.add_argument("--output", required=True, help="Output scene GLB")
    args = parser.parse_args()
    print(f"Mock CLI reconstruction: {args.input} -> {args.output}")

if __name__ == "__main__":
    main()
