import inspect
import datacollective

print("load_dataset signature:", inspect.signature(datacollective.load_dataset))
print("\nSource code of load_dataset:")
try:
    print(inspect.getsource(datacollective.load_dataset))
except Exception as e:
    print("Error:", e)
