"""Legacy launcher retained for compatibility; automation is disabled."""

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--application-id", type=int)
    parser.add_argument("--channel")
    parser.parse_args()
    print("Browser automation is disabled. Use Continue in Falcon for Assisted Apply.")


if __name__ == "__main__":
    main()
