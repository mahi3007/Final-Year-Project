import datacollective

try:
    print("MDC version:", datacollective.__version__)
except Exception as e:
    print("Version check:", e)

try:
    details = datacollective.get_dataset_details("cmu5jplf300nwmh07iqvk9leo")
    print("Details type:", type(details))
    print("Details:", details)
except Exception as e:
    print("Error getting details:", e)
