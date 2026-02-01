import pyoccam

# Now you can use pyoccam functions
data = pyoccam.load_dementia()

print(pyoccam.__version__)

#print(data.keys())

# Or use the main classes
manager = pyoccam.OpagVBMManager()