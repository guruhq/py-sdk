import guru

g = guru.Guru()

# Get the framework that matches the name `Client Support`
framework = g.get_framework("Client Support", cache=True)

# Import the framework
new_imported_framework_collection = framework.import_framework()
print(new_imported_framework_collection.name)

