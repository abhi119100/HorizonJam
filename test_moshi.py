# test_moshi.py
from moshika_core import tts_bytes


def main():
    with open("hello_moshi.wav", "wb") as f:
        f.write(tts_bytes("Hello! I am running locally on your machine."))
    print("Done -> hello_moshi.wav")


if __name__ == "__main__":
    main()
