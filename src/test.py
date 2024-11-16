from blinker import Signal

def test_signal_emission():
    print("Creating signal...")
    test_signal = Signal('test-signal')

    def test_handler(sender, **kwargs):
        print(f"Handler called with sender={sender}, kwargs={kwargs}")

    print("Connecting handler...")
    test_signal.connect(test_handler)

    print("Sending signal...")
    test_signal.send(None, state={"example_key": "example_value"})

test_signal_emission()
